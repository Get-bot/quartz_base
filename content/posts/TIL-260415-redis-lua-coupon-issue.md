---
title: "[TIL-260415] Redis Lua 선착순 쿠폰 발급 — WRONGTYPE 버그와 PDCA 검증"
date: 2026-04-15
tags: ["Redis", "Lua Script", "Spring Boot", "Kotlin", "PDCA", "HTTP Status Code"]
categories: ["TIL"]
description: "Redis Lua 스크립트로 선착순 쿠폰 발급을 구현하면서 WRONGTYPE 버그를 Design 기반 Gap Analysis로 발견하고, HTTP 410 Gone의 의미적 구분을 학습한 기록"
---

## 잘한 점

### Redis Lua 스크립트 기반 선착순 발급 전체 구현

**상황**
- redis-stock feature: Redis Lua로 SISMEMBER+GET/DECR+SADD를 원자적 블록으로 묶어 초과/중복 발급을 방지하는 선착순 쿠폰 API를 만들어야 했다
- DB 행 락 방식은 데드락·커넥션 풀 고갈 위험이 있어서 Redis로 재고 게이트키퍼를 옮기는 구조
- Design 문서를 먼저 작성하고 그대로 구현하는 PDCA 사이클로 진행

**액션**
- Lua 스크립트(`issue_coupon.lua`)에 Check-then-Act 패턴 적용 — 매진 경로(99%+ 트래픽)에서 읽기 1회, 쓰기 0회로 처리
- `RedisStockRepository`에 Lazy Init(SET NX EX) + `tryIssueCoupon`(Lua 실행) + `compensate`(SREM+INCR 보상) 3개 메서드 구현
- `IssueResult` enum으로 Lua 반환 코드(-1/0/1)를 타입 안전하게 래핑 — Design에는 없던 Enhancement인데 `when` exhaustive check가 가능해져서 더 안전
- `CouponIssueService.issue()`에서 Event 시간검증 → Redis Init → Lua → DB 저장 + 보상 플로우를 한 메서드에 orchestration
- ErrorCode 3종 추가: `COUPON_ALREADY_ISSUED`(CI409-1), `EVENT_SOLD_OUT`(E410/410 Gone), `REDIS_UNAVAILABLE`(R503)
- 총 8개 파일 생성, 2개 수정, ~237줄

**칭찬**
- Design 문서대로 구현하고 Gap Analysis까지 돌려서 수치로 검증한 게 좋았다
- `IssueResult` enum 추가 같은 Design 외 개선을 자연스럽게 넣은 판단
- Plan → Design → Do → Check → Act → Report → Archive까지 PDCA 풀사이클을 하루에 완주한 것

---

## 개선점

### WRONGTYPE 버그 — Redis 자료구조 타입 충돌

**문제**
- Gap Analysis에서 Match Rate 78%가 나왔다. 원인 중 가장 크리티컬한 건 `initStockIfAbsent()`의 issued 키 초기화 방식
- Design은 `redisTemplate.expire(issuedKey, Duration)`으로 명시했는데, 구현에서 `opsForValue().set(issuedKey, "0", Duration)`으로 작성
- 이러면 issued 키가 **String 타입**으로 생성되는데, Lua 스크립트의 `SISMEMBER`와 `SADD`는 **Set 타입**을 기대한다
- Redis는 키별로 단일 타입만 허용하므로 `WRONGTYPE Operation against a key holding the wrong kind of value` 에러가 터진다
- 이벤트에 대한 첫 번째 발급 요청부터 전부 500 에러

**원인**
- Design 문서의 `expire()` 호출 의도를 제대로 이해 못 하고, "issued 키도 초기화해야 하니까 set으로 값을 넣자"는 판단을 함
- 빈 키에 `EXPIRE`를 호출하면 no-op인 게 어색해서 뭔가 값을 넣으려 한 것
- 근데 그게 Lua의 Set 연산과 충돌한다는 걸 놓침

**액션플랜**
- Redis 키를 초기화할 때 "이 키를 나중에 어떤 자료구조로 쓰는지"를 항상 먼저 확인하자
- Design 문서에 Redis Key Design 섹션이 있으면 Type 컬럼을 추가해서 String/Set/Hash를 명시하자
- 구현할 때 초기화 코드의 Redis 명령어가 해당 타입과 맞는지 체크리스트로 검증

---

## 배운 점

### Design 문서 기반 Gap Analysis의 위력

**배움**
- WRONGTYPE 버그는 코드만 읽어서는 찾기 어렵다. `set()`이 문법적으로 틀린 건 아니니까
- 근데 Design 문서의 `expire()` 명세와 비교하니까 바로 보였다. "왜 다르지?" → "아 타입이 달라지네" → Critical 버그 발견
- Gap Analysis의 Match Rate가 78%에서 시작해서 5건 수정 후 97%까지 올라가는 과정이 객관적이어서 좋았다

**의미**
- 동시성 버그는 테스트로만 잡을 수 있지만, 타입 불일치 같은 설계 오류는 Design 문서와의 비교로 잡을 수 있다
- PDCA의 Check 단계가 단순한 형식이 아니라 실제로 크리티컬 버그를 잡아주는 걸 직접 체감
- 앞으로 Redis 관련 코드를 짤 때 "이 키의 자료구조 타입은 뭐지?"를 먼저 확인하는 습관이 생겼다

### HTTP 410 Gone의 의미적 구분

**배움**
- `EVENT_SOLD_OUT`을 처음에 409 Conflict로 매핑했는데, Design은 410 Gone을 지정했다
- 410 Gone = "리소스가 영구적으로 사라짐, 재시도 무의미" → 클라이언트가 재시도를 중단하도록 유도
- 409 Conflict = "현재 상태와 충돌, 재시도 가능성 있음"
- 같은 "재고 부족"이라도 DB 레벨(409)과 Redis 완전 매진(410)을 구분하면 클라이언트 로직이 더 효율적

**의미**
- HTTP 상태코드를 숫자로만 외우지 말고 의미(semantics)를 이해해야 적절한 코드를 선택할 수 있다
- 410은 처음 써봤는데, 매진 시나리오에 딱 맞는 코드였다

---

## 핵심 내용

### 키워드
- `Redis Lua Script`, `WRONGTYPE`, `Check-then-Act`, `SISMEMBER`, `DECR`, `SADD`, `SET NX EX`, `SREM`, `INCR`, `HTTP 410 Gone`, `PDCA Gap Analysis`, `IssueResult enum`

### 요약
- **Redis Lua 원자성**: 개별 Redis 명령은 원자적이지만 조합은 아니다. Lua 스크립트로 여러 명령을 묶으면 실행 중 다른 요청이 끼어들 수 없다.
- **Check-then-Act 패턴**: Flash sale에서 매진 후 요청이 99%+이므로, GET으로 먼저 재고를 확인하여 매진 경로를 읽기 1회·쓰기 0회로 처리한다. DECR-first보다 쓰기 비용(AOF, 레플리카 전파)을 대폭 줄인다.
- **WRONGTYPE 방지**: Redis 키는 생성 시점의 자료구조 타입이 고정된다. String(`SET`)으로 만든 키에 Set 명령(`SISMEMBER`, `SADD`)을 실행하면 WRONGTYPE 에러.
- **Lazy Init**: 이벤트 생성 시가 아니라 첫 발급 요청 시 `SET key value NX EX ttl`로 Redis에 재고를 초기화한다. 별도 스케줄러 불필요.
- **DB 보상 전략**: Lua 성공 → DB INSERT 실패 시 `SREM`(발급 기록 제거) + `INCR`(재고 복원)으로 정합성을 복구한다.

### 코드/명령어

```lua
-- issue_coupon.lua — Check-then-Act 패턴
local stock = tonumber(redis.call('GET', KEYS[1]))
if stock == nil or stock <= 0 then
    return 0   -- 매진: 읽기 1회, 쓰기 0회
end
if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then
    return -1  -- 중복: 읽기 2회, 쓰기 0회
end
redis.call('DECR', KEYS[1])
redis.call('SADD', KEYS[2], ARGV[1])
return 1       -- 성공: 읽기 2회, 쓰기 2회
```

```kotlin
// WRONGTYPE 버그 수정 — issued 키는 Set 타입이므로 expire()만 호출
if (wasSet == true) {
    redisTemplate.expire(issuedKey, Duration.ofSeconds(ttlSeconds))
    // ❌ redisTemplate.opsForValue().set(issuedKey, "0", Duration) → WRONGTYPE!
}
```

```kotlin
// IssueResult enum — Lua 반환 코드 타입 안전 래핑
enum class IssueResult(val code: Long) {
    ALREADY_ISSUED(-1), SOLD_OUT(0), SUCCESS(1);
    companion object {
        private val CODE_MAP = entries.associateBy { it.code }
        fun fromCode(code: Long): IssueResult =
            CODE_MAP[code] ?: throw IllegalStateException("Unknown code: $code")
    }
}
```
