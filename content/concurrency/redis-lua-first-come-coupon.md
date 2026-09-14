---
title: "Redis Lua로 선착순 쿠폰 발급 만들기"
date: 2026-04-16
tags: ["redis", "lua", "concurrency", "spring-boot", "kotlin", "transaction", "testing"]
description: "DB row lock이 왜 무너지는지에서 시작해 Lua 원자 블록, @Transactional 범위 분리, 실패 유형별 보상 전략, 이중 래치 동시성 테스트까지 선착순 발급의 전체 그림."
source: https://velog.io/@co-vol/Redis-Lua%EB%A1%9C-%EC%84%A0%EC%B0%A9%EC%88%9C-%EC%BF%A0%ED%8F%B0-%EB%B0%9C%EA%B8%89-%EB%A7%8C%EB%93%A4%EA%B8%B0
---

## 왜 DB 락이 안 되는가

가장 직관적인 구현은 이렇다:

```sql
SELECT remaining FROM event WHERE id = ? FOR UPDATE;
-- remaining > 0이면 발급
UPDATE event SET remaining = remaining - 1 WHERE id = ?;
INSERT INTO coupon_issue (event_id, user_id) VALUES (?, ?);
```

문제는 `FOR UPDATE`가 행 단위 락을 건다는 것. 1,000명이 동시에 쿠폰을 요청하면 999명이 한 줄로 대기한다. HikariCP 기본 풀이 10개니까, 10번째 요청부터는 커넥션 대기 큐에 쌓인다. 요청이 많아지면 타임아웃, 데드락, 커넥션 풀 고갈이 순서대로 찾아온다.

p99 응답시간이 500ms를 넘기기 시작하면 사실상 서비스 장애다.

## Redis 명령 하나하나는 원자적이다. 그런데 조합은 아니다

"그러면 Redis DECR로 재고 차감하면 되지 않나?" 맞다, 절반만.

Redis의 개별 명령(GET, DECR, SADD)은 싱글 스레드라서 각각은 원자적이다. 하지만 이걸 순차적으로 호출하면:

```
Thread A: GET stock → 1 (재고 있음)
Thread B: GET stock → 1 (재고 있음)
Thread A: DECR stock → 0
Thread B: DECR stock → -1  ← 초과 발급
```

GET과 DECR 사이에 다른 스레드가 끼어들 수 있다. 이게 "개별 명령은 원자적이지만 조합은 아니다"의 핵심이다.

## Lua 스크립트: 3개 명령을 1개 원자 블록으로

Redis는 Lua 스크립트를 실행할 때 다른 명령을 끼워넣지 않는다. 서버 사이드에서 단일 블록으로 실행된다. 이걸 이용하면 GET + DECR + SADD를 하나의 원자적 연산으로 묶을 수 있다.

```lua
-- issue_coupon.lua
-- KEYS[1] = coupon:stock:{eventId}
-- KEYS[2] = coupon:issued:{eventId}
-- ARGV[1] = userId
-- ARGV[2] = ttlSeconds

-- 1) 재고 확인 — 매진이 전체 트래픽의 99%+ → 읽기 1회로 즉시 탈출
local stock = tonumber(redis.call('GET', KEYS[1]))
if stock == nil or stock <= 0 then
    return 0   -- 매진
end

-- 2) 중복 확인 — 읽기 1회 추가
if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then
    return -1  -- 이미 발급됨
end

-- 3) 성공 경로에서만 쓰기 발생
redis.call('DECR', KEYS[1])
redis.call('SADD', KEYS[2], ARGV[1])

-- 4) issued Set에 TTL 없으면 설정(최초 발급 시점 기준)
if redis.call('TTL', KEYS[2]) == -1 then
    redis.call('EXPIRE', KEYS[2], ARGV[2])
end

return 1       -- 발급 성공
```

27줄. 이 안에 선착순 발급의 핵심 로직이 다 들어있다.

### Check-then-Act: 매진 경로를 먼저 최적화하는 이유

선착순 이벤트의 트래픽 분포를 생각해보자. 쿠폰 1,000개에 요청 10,000건이면, 성공하는 건 1,000건(10%)이고 매진으로 튕기는 건 9,000건(90%)이다. 실제 운영에서는 이 비율이 99% 이상이다.

그래서 Lua 스크립트의 첫 번째 동작이 `GET stock`이다. 매진이면 읽기 1회로 바로 리턴하고, DECR이나 SADD 같은 쓰기 연산을 아예 안 한다. 90%+ 트래픽이 읽기 한 번만 하고 빠지는 구조다.

## 서비스 레이어: @Transactional을 어디에 걸 것인가

Lua 스크립트가 성공하면 DB에 발급 이력을 저장해야 한다. 여기서 `@Transactional` 배치가 중요하다.

처음에는 CouponIssueService 전체에 `@Transactional`을 걸었다. 코드 리뷰에서 이 문제가 잡혔다:

```
CouponIssueService.issue() {
    @Transactional  ← DB 커넥션 획득
    eventRepository.findById()        // DB 읽기
    redisStockRepository.initStock()  // ← Redis 호출인데 DB 커넥션 점유 중
    redisStockRepository.tryIssue()   // ← Redis 호출인데 DB 커넥션 점유 중
    couponIssueRepository.save()      // DB 쓰기
}                                     // ← 여기서 커넥션 반환
```

Redis 호출하는 동안에도 DB 커넥션을 붙잡고 있다. HikariCP 기본 풀이 10개인데, 200개 스레드가 동시에 들어오면 190개가 커넥션 대기에 걸린다. DB 락을 피하려고 Redis를 도입했는데 결국 커넥션 풀에서 병목이 생기는 거다.

해결책은 트랜잭션 범위를 쪼개는 것이다:

```kotlin
// CouponIssueService — @Transactional 없음
@Service
class CouponIssueService(
    private val eventRepository: EventRepository,
    private val redisStockRepository: RedisStockRepository,
    private val couponIssueTxService: CouponIssueTxService,
) {
    fun issue(eventId: UUID, userId: UUID): CouponIssueResponse {
        val event = eventRepository.findByIdOrNull(eventId)
            ?: throw BusinessException(ErrorCode.EVENT_NOT_FOUND)

        // 기간 검증
        if (!event.period.contains(Instant.now())) {
            throw BusinessException(ErrorCode.EVENT_NOT_OPEN)
        }

        // Redis 호출 — DB 커넥션 미점유
        val ttlSeconds = Duration.between(Instant.now(), event.period.endedAt)
            .plusHours(1).toSeconds()
        redisStockRepository.initStockIfAbsent(eventId, event.totalQuantity, ttlSeconds)

        val result = redisStockRepository.tryIssueCoupon(eventId, userId, ttlSeconds)
        when (result) {
            IssueResult.ALREADY_ISSUED -> throw BusinessException(ErrorCode.COUPON_ALREADY_ISSUED)
            IssueResult.SOLD_OUT -> throw BusinessException(ErrorCode.EVENT_SOLD_OUT)
            IssueResult.SUCCESS -> Unit
        }

        // DB 저장만 트랜잭션 — 커넥션 점유 최소화
        val couponIssue = couponIssueTxService.saveOrCompensate(eventId, userId)
        return CouponIssueResponse.from(couponIssue)
    }
}
```

```kotlin
// CouponIssueTxService — DB 저장 구간만 @Transactional
@Service
class CouponIssueTxService(
    private val couponIssueRepository: CouponIssueRepository,
    private val redisStockRepository: RedisStockRepository,
) {
    @Transactional
    fun saveOrCompensate(eventId: UUID, userId: UUID): CouponIssue {
        try {
            return couponIssueRepository.saveAndFlush(
                CouponIssue(eventId = eventId, userId = userId),
            )
        } catch (e: DataIntegrityViolationException) {
            // UK 위반: Redis는 정확, DB에 이미 존재 → stock만 복원
            redisStockRepository.restoreStock(eventId)
            throw BusinessException(ErrorCode.COUPON_ALREADY_ISSUED)
        } catch (e: DataAccessException) {
            // 기타 DB 오류: Redis 상태를 완전 롤백
            redisStockRepository.compensate(eventId, userId)
            throw e
        }
    }
}
```

Redis 호출 구간에서는 DB 커넥션을 잡지 않고, `saveOrCompensate` 안에서만 짧게 잡았다가 놓는다.

## 보상 처리: Redis는 성공했는데 DB가 실패하면?

Lua 스크립트가 성공(DECR + SADD)한 뒤 DB INSERT가 실패하는 경우가 있다. 이때 Redis 상태를 되돌려야 정합성이 유지된다.

여기서 중요한 건 **실패 유형에 따라 보상 전략이 다르다**는 점이다:

**UK 위반 (DataIntegrityViolationException)**:
Lua의 SISMEMBER를 통과했지만 극히 드문 타이밍에 DB에 먼저 기록된 경우. 이때 issued Set에는 userId가 이미 들어가 있으니 그건 그대로 두고, stock만 `INCR`로 복원한다. SREM까지 하면 같은 유저가 다시 발급받을 수 있다.

**기타 DB 오류 (DataAccessException)**:
네트워크 장애, 타임아웃 등. 이 경우는 발급 자체가 없었던 걸로 만들어야 하니까 `SREM`(issued Set에서 제거) + `INCR`(stock 복원)을 둘 다 한다.

```
UK 위반  → restoreStock(INCR만)   — "발급은 됐으니 기록은 유지, 재고만 복원"
기타 오류 → compensate(SREM+INCR) — "아예 없었던 일로"
```

이 구분을 안 하면 동일 유저가 재발급받거나, 재고가 맞지 않는 상황이 생긴다.

## 코드 리뷰에서 잡힌 버그들

초기 구현 후 PR 리뷰에서 꽤 미묘한 버그들이 나왔다:

**WRONGTYPE 버그**: Redis에서 `coupon:issued:{eventId}` 키를 String으로 초기화했는데 Lua 스크립트에서는 Set 연산(SISMEMBER, SADD)을 했다. Redis는 키의 타입이 생성 시점에 고정되기 때문에 WRONGTYPE 에러가 발생했다. 초기화 코드에서 해당 키를 SET 명령 대신 EXPIRE만 거는 것으로 수정했다.

**HTTP 상태코드 혼동**: 매진을 처음에 409 Conflict로 리턴했다. 409는 "재시도하면 될 수 있음"이고, 410 Gone은 "리소스가 소진됨, 재시도 의미 없음"이다. 선착순 매진은 410이 맞다. 클라이언트가 불필요한 재시도를 하지 않도록 의미를 정확히 전달해야 한다.

**Lua ARGV 타입**: `Duration.ofSeconds(3600)`을 그대로 넘기면 Lua에 `"PT3600S"`라는 문자열이 도착한다. `ttlSeconds.toString()`으로 `"3600"`을 넘겨야 한다.

이런 건 테스트가 아니라 코드 리뷰에서만 잡히는 종류의 버그다.

## 동시성 테스트: "정말로 안전한가?"를 증명하기

코드 리뷰를 통과했으니 이제 실제로 동시에 수천 건을 쏴서 검증해야 한다. Kotest + Testcontainers로 4종의 테스트를 작성했다.

핵심은 **이중 래치(Double Latch) 패턴**이다:

```kotlin
fun concurrentExecute(
    taskCount: Int,
    poolSize: Int = minOf(taskCount, 200),
    action: (index: Int) -> Unit,
) {
    val executor = Executors.newFixedThreadPool(poolSize)
    val startLatch = CountDownLatch(1)    // 동시 출발 신호
    val doneLatch = CountDownLatch(taskCount)  // 전체 완료 대기

    repeat(taskCount) { i ->
        executor.submit {
            startLatch.await()  // 모든 스레드가 여기서 대기
            try {
                action(i)
            } finally {
                doneLatch.countDown()
            }
        }
    }

    startLatch.countDown()  // 한 번에 출발
    try {
        val completed = doneLatch.await(120, TimeUnit.SECONDS)
        check(completed) { "timed out" }
    } finally {
        executor.shutdownNow()  // 실패해도 스레드 정리 보장
        executor.awaitTermination(10, TimeUnit.SECONDS)
    }
}
```

이 패턴이 없으면 먼저 생성된 스레드부터 실행해서 "순차 요청"에 가까워진다. `startLatch`로 200개 스레드를 대기시킨 뒤 `countDown()` 한 번으로 동시에 출발시킨다.

### TC-01: 초과 발급 검증

```kotlin
test("1,000개 쿠폰에 3,000건 동시 요청 시 정확히 1,000건만 발급된다") {
    val totalQuantity = 1_000
    val taskCount = 3_000
    val event = createOpenEvent(totalQuantity)
    val successCount = AtomicInteger(0)
    val soldOutCount = AtomicInteger(0)

    concurrentExecute(taskCount) { _ ->
        try {
            couponIssueService.issue(event.id, UUID.randomUUID())
            successCount.incrementAndGet()
        } catch (e: BusinessException) {
            when (e.errorCode) {
                ErrorCode.EVENT_SOLD_OUT -> soldOutCount.incrementAndGet()
                else -> throw e
            }
        }
    }

    // 3중 검증
    successCount.get() shouldBe totalQuantity        // 성공 1,000건
    soldOutCount.get() shouldBe (taskCount - totalQuantity)  // 매진 2,000건
    couponIssueRepository.count() shouldBe totalQuantity.toLong()  // DB도 1,000건
}
```

3,000건 요청에 정확히 1,000건만 발급. 1,001건도 아니고 999건도 아니다.

### TC-02: 중복 발급 검증

동일한 userId로 100건을 동시에 쏜다. Lua의 SISMEMBER와 DB의 Unique Key가 이중으로 방어하므로 딱 1건만 발급된다.

### TC-03: 매진 후 무결성

5개 쿠폰을 순차 발급으로 매진시킨 뒤 1,000건을 동시에 쏜다. 추가 발급 0건.

### TC-04: Redis-DB 정합성

Redis의 `coupon:issued:{eventId}` Set 크기와 DB의 `coupon_issue` 테이블 row count가 일치하는지 검증.

4개 테스트 전부 통과. Lua 스크립트의 원자성이 실제 동시 환경에서 검증됐다.

### 테스트하면서 겪은 삽질

처음에 TC-01의 `taskCount`를 10,000으로 잡았다. 그런데 WSL2 + Testcontainers + HikariCP(기본 10개) 조합에서 120초 안에 안 끝났다. 200개 스레드가 10개 커넥션을 놓고 경쟁하니 커넥션 대기 시간이 누적되는 거다.

3,000건(재고의 3배)으로 줄였다. 동시성 안전성 증명에는 3배 과부하면 충분하고, CI 환경에서도 안정적으로 통과한다.

더 큰 문제도 있었다. TC-01이 타임아웃으로 실패한 뒤 TC-02에서 `couponIssueRepository.count()`가 224를 반환했다. TC-02는 동일 userId 100건이니 최대 1건이어야 하는데.

원인은 **TC-01에서 executor.shutdown()에 도달하지 못한 것**이다. `check(completed)`가 예외를 던지면서 200개 스레드가 정리되지 않고 백그라운드에서 계속 DB에 쓰고 있었다. `beforeTest`에서 `deleteAllInBatch()`를 해도 그 뒤에 잔여 스레드가 쓰니까 오염되는 거다.

`try-finally`로 `executor.shutdownNow()`를 감싸서 해결했다. 테스트가 실패해도 스레드 풀이 확실히 정리된다.

## 전체 아키텍처 흐름

```
Client → POST /api/v1/events/{eventId}/issue

CouponIssueService.issue(eventId, userId)
  ├── 1. eventRepository.findById()          ← DB Read (커넥션 잠깐 잡고 놓음)
  ├── 2. event.period.contains(now)          ← 기간 검증
  ├── 3. initStockIfAbsent(SET NX EX)       ← Redis (DB 커넥션 미점유)
  ├── 4. tryIssueCoupon(Lua 스크립트)         ← Redis (DB 커넥션 미점유)
  │     ├── SOLD_OUT(0)  → 410 Gone
  │     ├── ALREADY(-1)  → 409 Conflict
  │     └── SUCCESS(1)   → continue
  └── 5. CouponIssueTxService.saveOrCompensate()  ← @Transactional (여기만)
        ├── DB INSERT 성공 → 201 Created
        ├── UK 위반 → restoreStock(INCR) + 409
        └── DB 오류 → compensate(SREM+INCR) + re-throw
```

Redis 호출 구간(3~4)에서 DB 커넥션을 안 잡는다. DB 쓰기(5)에서만 짧게 잡았다가 놓는다.

## 배운 것들

**"개별 명령은 원자적이지만 조합은 아니다."** Redis를 쓰면서 가장 먼저 부딪히는 함정. Lua 스크립트가 이 문제의 정석적인 해법이다.

**트랜잭션 범위는 최소화해야 한다.** 특히 Redis 같은 외부 I/O를 포함하는 메서드에 `@Transactional`을 걸면 DB 커넥션이 Redis 응답을 기다리는 동안 낭비된다. 고동시성에서는 이게 전체 시스템을 죽인다.

**보상 전략은 실패 유형별로 달라야 한다.** UK 위반과 네트워크 오류를 같은 방식으로 롤백하면 데이터 불일치가 생긴다. 예외 타입을 구분해서 처리해야 한다.

**테스트에서 스레드 풀은 반드시 정리해야 한다.** `executor.shutdown()`이 실행 보장 안 되면 다음 테스트를 오염시킨다. 이건 코드 리뷰에서도 잡기 어렵고, 실제로 터져봐야 안다.

**동시성 테스트에는 이중 래치가 필수다.** 스레드를 만드는 것과 동시에 실행하는 것은 다르다. `startLatch`로 대기시킨 뒤 한 번에 출발시켜야 "진짜" 동시 요청이다.

---

*이 프로젝트의 전체 코드는 [spring-event-lab](https://github.com/Get-bot/spring-event-lab)에서 볼 수 있다.*

---

원문: [velog · 2026-04-16](https://velog.io/@co-vol/Redis-Lua%EB%A1%9C-%EC%84%A0%EC%B0%A9%EC%88%9C-%EC%BF%A0%ED%8F%B0-%EB%B0%9C%EA%B8%89-%EB%A7%8C%EB%93%A4%EA%B8%B0)
