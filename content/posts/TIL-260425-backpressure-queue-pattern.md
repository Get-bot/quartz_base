---
title: "[TIL-260425] Backpressure 패턴 — Queue ≠ Rate Limiter"
date: 2026-04-25
tags: ["Redis", "Spring Boot", "Backpressure", "Sorted Set", "Lua", "Kafka", "Architecture Pattern"]
categories: ["TIL"]
description: "선착순 쿠폰 시스템에서 Sorted Set 대기열로 5만+ 동시 트래픽을 평탄화. Lua 원자성, ZPOPMIN 결과 키 패턴, SOLD_OUT short-circuit 구현"
---

## 잘한 점

### Sorted Set 대기열로 5만+ 동시 트래픽을 평탄화

**상황**
- 선착순 쿠폰 발급 시스템에서 redis-stock + kafka-consumer로 발급 자체는 안전하게 만들어둠
- 근데 이벤트 오픈 순간 5만 명이 동시에 `/issue`를 때리면 Tomcat 워커·Redis 핫키·DB 풀에 동시 압력이 걸리는 시나리오
- latency 무너지고 클라이언트는 무한 로딩에 빠짐
- Rate Limiter(429 거부)는 "공정"하지만 사용자 경험을 깨뜨림

**액션**
- `POST /enter`로 들어오는 즉시 Redis Sorted Set ZADD(score=arrivalMs)로 줄세움 → 즉시 200 + rank 응답
- `@Scheduled(fixedDelay=1s)` 워커가 ZPOPMIN으로 batch_size명씩 dequeue → 기존 `CouponIssueService.issue()` 호출
- 결과는 별도 `result:{eventId}:{userId}` 키에 TTL 1h로 기록 → 클라이언트 폴링으로 상태 전이 관찰
- 운영자는 `batch-size / poll-interval`로 admission rate를 자유롭게 제어

**칭찬**
- "거부 대신 지연"이라는 발상 전환을 코드로 옮겨낸 점
- 신규 코드는 enter/scheduler/result 3개로 응축 — 기존 redis-stock(Lua)과 kafka-consumer(Producer 보상) 경로를 그대로 재사용한 설계
- /issue 엔드포인트도 그대로 두고 비교 학습용으로 보존한 게 깔끔함
- 1-day PDCA cycle로 99% Match Rate 달성

---

## 개선점

### ZPOPMIN destructive 특성 — crash 시 데이터 손실 가능성

**문제**
- ZPOPMIN으로 dequeue된 직후 처리 중에 앱이 죽으면 popped 유저는 큐에서도 result 키에서도 사라짐
- "/enter로 ZADD까지 성공했는데 결과 키도 없는" 영구 미발급 상태가 발생 가능
- 학습 프로젝트 범위 밖이라 일단 OOS로 명시했지만 운영 환경이라면 큰 위험

**원인**
- ZPOPMIN은 본질적으로 atomic-but-destructive — 꺼내는 순간 큐에서 사라짐
- 처리 결과 기록(result 키 SET)은 그 다음 단계라 그 사이 시간 간격이 있음
- Spring graceful shutdown(`setWaitForTasksToCompleteOnShutdown=true`)이 일부 완화하지만 SIGKILL이나 OOM에는 무력

**액션플랜**
- 다음 학습 phase로 Redis Streams 마이그레이션이 자연스러운 다음 단계
- `XADD` + `XREADGROUP` + `XACK` 패턴 — Kafka Consumer Group처럼 PEL(Pending Entries List)이 자동 재배달
- 또는 Processing Set 패턴: ZPOPMIN 대신 ZRANGEBYSCORE → MULTI(ZREM + SADD `processing:`) → 처리 후 SREM. 부팅 시 잔여 유저 재처리

---

## 배운 점

### Queue ≠ Rate Limiter — Backpressure는 "지연 허용"

**배움**
- 큐는 rate limiter가 아니라 "시스템 처리 능력과 트래픽을 분리하는 버퍼"라는 걸 코드 짜면서 체감
- Rate Limiter는 거부(429)로 트래픽을 깎지만 Backpressure는 지연(200 + rank)으로 흡수함
- 입장률을 정적으로 정하는 게 아니라 `batch_size / poll-interval`로 시스템이 직접 정함 — 처리 능력 기준의 self-pacing

**의미**
- 다음에 트래픽 스파이크 문제를 만나면 "거부할까 지연할까"부터 먼저 결정하는 습관
- 단순 throttling은 사용자 경험을 깨뜨리지만 큐는 "현재 N번째 대기 중"으로 진행 상황 가시화 가능
- "처리 능력 ≥ 입장 속도"가 시스템 설계의 핵심 부등식 — 이것만 지키면 latency가 폭발할 일이 없음

### 결과 키 패턴은 ZPOPMIN destructive의 보완

**배움**
- Plan에는 "ZPOPMIN으로 꺼내서 발급 처리"까지만 있었는데, 실제 짜면서 "클라이언트가 결과를 어떻게 알지?"를 마주침
- ZPOPMIN destructive라 큐에서 사라진 후엔 ZRANK로 조회 불가능 → 별도 결과 키 도입
- 페이로드 형식 `ISSUED:<uuid>` / `SOLD_OUT` / `ALREADY_ISSUED` / `FAILED:<errorCode>`로 단순 String 사용 (redis-cli GET 시 사람-친화)

**의미**
- 설계 단계에서 "비동기 결과 통지 채널"을 명시적으로 두는 게 중요
- destructive 자료구조를 쓸 땐 "꺼낸 후의 정보를 어디에 보존할 것인가"를 같이 설계

---

## 핵심 내용

### 키워드
- `Backpressure`, `Redis Sorted Set`, `ZADD/ZPOPMIN/ZRANK`, `@Scheduled(fixedDelay)`, `Lua atomicity`, `result key pattern`, `SOLD_OUT short-circuit`, `Hash tag {eventId}`

### 요약
- **Backpressure**: 거부(429)가 아니라 지연(200 + rank). 큐는 rate limiter가 아니라 시스템 처리 능력과 트래픽 스파이크를 분리하는 버퍼.
- **enter 원자성**: SISMEMBER → ZSCORE → ZADD → EXPIRE를 단일 Lua EVAL로 묶음. 가장 빈번한 거부 케이스(이미 발급)를 가장 먼저 검사.
- **결과 통지**: ZPOPMIN은 destructive하므로 처리 결과를 별도 `result:{eventId}:{userId}` 키에 TTL 1h로 기록 → 폴링으로 `WAITING → ISSUED/SOLD_OUT/ALREADY_ISSUED/FAILED` 전이 관찰.
- **SOLD_OUT short-circuit**: 첫 매진 후 batch 잔여 유저는 어차피 같은 결과 → Lua 호출 없이 SET만으로 일괄 통보 (N-1 EVAL 절약).
- **fixedDelay vs fixedRate**: fixedDelay는 처리 시간이 길어지면 자동 back-pressure. fixedRate는 호출 누적으로 overload 가속.
- **Hash tag `{eventId}`**: waiting/result/issued 키 모두 같은 슬롯 → Redis Cluster 호환.

### 코드/명령어

```lua
-- enter_queue.lua — 1 RTT EVAL로 race-free enter
-- KEYS[1]=waiting:{eventId}, KEYS[2]=coupon:issued:{eventId}
-- ARGV[1]=userId, ARGV[2]=score(arrivalMs), ARGV[3]=ttlSeconds

if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then
    return -1   -- 이미 발급 (재진입 차단)
end
if redis.call('ZSCORE', KEYS[1], ARGV[1]) ~= false then
    return 0    -- 이미 큐 (중복 enter 차단)
end
redis.call('ZADD', KEYS[1], ARGV[2], ARGV[1])
if redis.call('TTL', KEYS[1]) < 0 then
    redis.call('EXPIRE', KEYS[1], ARGV[3])
end
return 1        -- 신규 enqueue 성공
```

```kotlin
// CouponIssueScheduler — drain + SOLD_OUT short-circuit
@Scheduled(fixedDelayString = "\${waiting-queue.poll-interval-ms:1000}")
fun drainQueues() {
    val openEvents = eventRepository.findAllOpenAt(Instant.now())
    for (event in openEvents) drainOneEvent(event.id)
}

private fun drainOneEvent(eventId: UUID) {
    val popped = waitingQueueRepository.popMin(eventId, batchSize)
    for (userId in popped) {
        try {
            val response = couponIssueService.issue(eventId, userId)
            recordResult(eventId, userId, "ISSUED:${response.id}", ttl)
        } catch (e: BusinessException) {
            recordResult(eventId, userId, mapPayload(e.errorCode), ttl)
            if (e.errorCode == ErrorCode.EVENT_SOLD_OUT) {
                drainRemainingAsSoldOut(eventId, popped, userId, ttl)
                return  // batch 잔여 일괄 통보 후 종료
            }
        }
    }
}
```

### 참고 자료
- Redis Sorted Set 스펙: https://redis.io/docs/latest/develop/data-types/sorted-sets/
- Redis Streams (다음 학습 phase): https://redis.io/docs/latest/develop/data-types/streams/
- Spring `@Scheduled` fixedDelay vs fixedRate: https://docs.spring.io/spring-framework/reference/integration/scheduling.html
- 본 PR: https://github.com/Get-bot/spring-event-lab/pull/7
