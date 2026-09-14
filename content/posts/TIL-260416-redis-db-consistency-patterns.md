---
title: "[TIL-260416] PR 리뷰로 배운 Redis-DB 정합성 패턴 5가지"
date: 2026-04-16
tags: ["Redis", "JPA", "Spring Boot", "Kotlin", "Lua", "트랜잭션", "보상 패턴"]
categories: ["TIL"]
description: "JPA deferred flush, @Transactional readOnly 전파 함정, UK-aware 보상 분기 등 PR 리뷰에서 배운 Redis-DB 정합성 핵심 패턴 정리"
---

## 잘한 점

### PR 리뷰 코멘트 8건 전수 분석 + 코드 수정까지 완주

**상황**
- PR #4 (Redis Lua 기반 선착순 쿠폰 발급)에 Copilot이 리뷰 코멘트 8건을 달았다
- 코멘트가 타당한지부터 판단해야 했고, 수정이 필요하면 왜 그렇게 고쳐야 하는지 원인까지 파악해야 했다

**액션**
- 3개 리뷰 에이전트(Reuse/Quality/Efficiency)를 병렬로 돌려서 Copilot 리뷰 + 자체 분석을 크로스체크
- 8건 모두 타당함을 확인하고, HIGH 3건(Lua TTL, 트랜잭션 범위, UK-aware 보상)을 우선 수정
- 수정 후 코드를 직접 리뷰하면서 추가 버그 2건을 더 잡았다 (`@Transactional(readOnly=true)` 전파 문제, `Duration.toString()` 직렬화 문제)

**칭찬**
- "리뷰가 맞는지" 비판적으로 검증한 뒤 수용한 게 좋았다. 무조건 수용하거나 무조건 무시하지 않았다
- 수정하면서 원래 리뷰에서 못 잡은 버그 2건까지 추가로 발견한 건 꽤 뿌듯

---

### 커밋 1개를 3개로 분리한 판단

**상황**
- 코드 변경 + PDCA 문서 갱신 + CLAUDE.md 업데이트를 한 커밋에 다 넣어버렸다 (17파일)
- 직접 "너무 한번에 커밋한 거 아냐?"라고 셀프 피드백

**액션**
- `git reset --soft HEAD~1`로 풀고 3개로 분리:
  - 코드 변경 (5파일)
  - PDCA 문서 (10파일)
  - CLAUDE.md + Knowledge Base (2파일)

**칭찬**
- 커밋 크기에 대한 감각이 생기고 있다. "일단 커밋하고 넘어가자"가 아니라 리뷰어 관점에서 생각한 것

---

## 개선점

### CouponIssueTxService 네이밍과 클래스 분리 판단

**문제**
- FIX-6(트랜잭션 범위 축소) 해결을 위해 `CouponIssueTxService`라는 별도 클래스를 만들었다
- 메서드 1개짜리 클래스, 이름에 `Tx`(Transaction)라는 인프라 관심사가 노출
- Plan 문서에서는 `TransactionTemplate`을 쓰기로 했는데, 구현 시 다른 선택을 함

**원인**
- `@Transactional` self-invocation 문제를 해결하려다 보니 "별도 클래스가 가장 확실하다"고 판단
- TransactionTemplate 방식도 있었지만 익숙한 쪽을 선택

**액션플랜**
- 다음에 같은 패턴이 나오면 TransactionTemplate을 한번 써보자 — 클래스 증식 없이 같은 효과
- 네이밍은 `CouponIssueWriter`(파일명)와 `CouponIssueTxService`(클래스명)가 불일치하는 것도 정리 필요

---

## 배운 점

### JPA deferred flush — save()는 즉시 INSERT가 아니다

**배움**
- `repository.save(entity)`는 Hibernate 1차 캐시에 등록만 하고, 실제 INSERT SQL은 flush 시점(보통 트랜잭션 커밋 직전)에 실행된다
- 그래서 catch 블록에서 `DataIntegrityViolationException`을 잡으려면 `saveAndFlush()`를 써야 한다
- 이걸 모르면 UK 위반이 커밋 시점에 터져서 catch를 완전히 우회한다

**의미**
- JPA 사용할 때 "save = INSERT"라는 멘탈 모델이 위험하다는 걸 확실히 깨달았다
- 보상 로직이 있는 코드에서는 반드시 `saveAndFlush` 사용

---

### @Transactional(readOnly=true)의 REQUIRED 전파 함정

**배움**
- 클래스 레벨에 `@Transactional(readOnly = true)`를 걸면, 그 안에서 호출하는 다른 Bean의 `@Transactional` 메서드가 REQUIRED 전파로 **기존 read-only 트랜잭션에 참여**한다
- 내부 메서드의 `readOnly=false` 설정은 무시됨 → PostgreSQL이 `SET TRANSACTION READ ONLY` 상태에서 INSERT를 거부
- FIX-6의 목적(Redis 호출 중 DB 커넥션 미점유)도 무효화

**의미**
- `@Transactional`을 클래스 레벨에 거는 건 편하지만, 트랜잭션 경계를 의식적으로 관리해야 할 때는 오히려 독이 된다
- 특히 외부 I/O(Redis, HTTP)가 섞인 메서드에서는 트랜잭션을 안 거는 게 맞다

---

### UK 위반과 일반 DB 오류는 보상 전략이 달라야 한다

**배움**
- Redis Lua 성공 → DB INSERT 실패 시 무조건 `SREM + INCR`(완전 롤백)하면 위험하다
- UK 위반이면 Redis issued Set이 정확한 상태 → SREM하면 다음 요청이 또 통과해서 무한 루프
- UK 위반: `restoreStock(INCR만)` / 기타 오류: `compensate(SREM + INCR)`로 분기

**의미**
- "보상 = 전부 되돌리기"가 아니라 "실패 원인에 따라 적절한 되돌리기"라는 관점이 중요하다
- 분산 시스템에서 보상 트랜잭션을 설계할 때 이 사고방식이 기본이 될 듯

---

## 핵심 내용

### 키워드
- `JPA Deferred Flush`, `saveAndFlush`, `@Transactional readOnly 전파`, `REQUIRED Propagation`, `Redis EXPIRE 비존재 키`, `TransactionTemplate`, `UK-aware 보상`, `Duration.toString() ISO 8601`

### 요약
- JPA `save()`는 INSERT를 지연한다. 예외를 catch하려면 `saveAndFlush()` 필수.
- `@Transactional(readOnly=true)` 클래스 레벨 + 내부 `@Transactional` 호출 → REQUIRED 전파로 read-only 참여 → INSERT 실패.
- Redis `EXPIRE`는 키 미존재 시 무효(no-op). Lua 스크립트 내에서 SADD 직후 TTL을 설정해야 안전.
- UK 위반 보상(INCR만)과 일반 DB 오류 보상(SREM+INCR)은 반드시 분기해야 한다.
- `Duration.ofSeconds(3600).toString()` → `"PT1H"` (ISO 8601). Redis ARGV에는 `ttlSeconds.toString()` → `"3600"` 사용.

### 코드/명령어

```kotlin
// UK-aware 보상 분기 패턴
try {
    couponIssueRepository.saveAndFlush(entity)
} catch (e: DataIntegrityViolationException) {
    // UK 위반: issued Set 유지, stock만 복원
    redisStockRepository.restoreStock(eventId)
    throw BusinessException(ErrorCode.COUPON_ALREADY_ISSUED)
} catch (e: DataAccessException) {
    // 기타 DB 오류: 완전 롤백
    redisStockRepository.compensate(eventId, userId)
    throw e
}
```

```lua
-- Lua에서 issued Set TTL 보장 (ARGV[2] = ttlSeconds)
redis.call('SADD', KEYS[2], ARGV[1])
if redis.call('TTL', KEYS[2]) == -1 then
    redis.call('EXPIRE', KEYS[2], ARGV[2])
end
```
