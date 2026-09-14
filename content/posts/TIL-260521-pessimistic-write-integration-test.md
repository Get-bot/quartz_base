---
title: "[TIL-260521] PESSIMISTIC_WRITE 실효성을 진짜로 검증하는 통합 테스트"
date: 2026-05-21
tags: ["Spring Boot", "Kotlin", "JPA", "Hibernate", "PostgreSQL", "Testcontainers", "Kotest", "Integration Test"]
categories: ["TIL"]
description: "PESSIMISTIC_WRITE 가 실제로 잡히는지 검증하는 L4 통합 테스트 패턴 + 클래스 @Transactional 이 만들던 가짜 그린 + mutation testing 사고방식."
---

## 잘한 점

### 락 + 가시성 두 축을 동시에 검증하는 L4 spec

**상황**
- `WithdrawalPgNotificationService` 의 FAILED 분기에서 `SubAccount.usedToday` 환원을 `PESSIMISTIC_WRITE` 로 보호하도록 변경.
- prod 의 `@Lock(PESSIMISTIC_WRITE)` 가 IDE 리팩토링·alias 교체로 silent 하게 떨어져 나갈 위험이 있었음.
- 단위 테스트로는 락이 실제로 잡히는지 검증이 불가능.

**액션**
- L4 `@SpringBootTest` + `ExecutorService(2)` + `acquiredLatch` / `releaseLatch` 로 두 스레드 race 시나리오 구성.
- thread A: tx 안에서 `findByIdForUpdate` 로 락 잡고 `unuse` → 600ms hold → commit.
- thread B: A 의 `acquiredLatch` 후 같은 row 에 `findByIdForUpdate` → A commit 까지 대기.
- 두 축 검증: (1) B 의 wait 시간 ≥ holdMs (락이 실제로 잡혔다는 증거) (2) B 가 본 `usedToday` = A 의 `unuse` 결과 (commit 가시성).

**칭찬**
- 그냥 "락 함수 부르고 결과 나옴" 으로 끝낼 수도 있었는데 wait 시간 측정까지 넣어서 mutation safety 확보.
- prod 의 `@Lock` 떼면 spec 이 즉시 fail 한다는 걸 실제로 코드에서 확인까지 함.
- "이 테스트가 미래의 silent regression 을 잡아준다" 라는 명확한 의도로 짠 것.

### Integration spec 의 클래스 레벨 `@Transactional` 제거

**상황**
- `WithdrawalPgNotificationServiceIntegrationSpec` 에 클래스 레벨 `@Transactional` 이 박혀 있었음.
- `sut.apply` 가 `@Transactional(MANDATORY)` 라 호출자 tx 가 살아 있어야 동작.
- 결과적으로 spec 전체가 한 tx 안에서 돌아서 `PESSIMISTIC_WRITE` 검증이 무력화되고 commit 가시성도 못 봄.
- 게다가 `AlreadyNotified` dedup 재진입 테스트는 setup 에서 도메인 메서드로 흉내내고 `sut.apply` 를 1회만 호출 — 진짜 race 가 아님.

**액션**
- 클래스 `@Transactional` 제거 + `TransactionTemplate` 으로 seed / sut.apply / reload / cleanup 각각 별도 tx.
- `AlreadyNotified` 테스트를 `sut.apply` 두 번 호출 (1차 commit → 2차 진입) 로 재작성 — 진짜 dedup race.
- `afterTest` 에 명시 cleanup 추가 (롤백 의존 제거) → 다른 spec 과 격리.
- `WithdrawalFixture.withdrawalRecord` 에 `outerRefId` 파라미터 추가 — row 격리.

**칭찬**
- "테스트 그린이니 됐겠지" 안 하고 spec 이 진짜로 뭘 검증하는지 되짚어본 것.
- 무력화된 검증을 다시 살리는 데 그치지 않고 dedup 가짜 race 까지 같이 잡아낸 것.

---

## 개선점

### 클래스 `@Transactional` 이 만들던 가짜 그린

**문제**
- spec 클래스 위에 `@Transactional` 한 줄로 "롤백 편의" 를 챙긴 게 락·가시성 검증을 통째로 무력화.
- `PESSIMISTIC_WRITE` 가 실제로 동작하는지 알 수 없는 상태로 그린이 떴음.
- dedup race 테스트가 가짜였던 것도 마찬가지 — `sut.apply` 1회로는 1차/2차 진입 흐름이 안 만들어짐.

**원인**
- "통합 테스트도 단위 테스트처럼 빨리 + 격리되게" 욕심으로 클래스 `@Transactional` 을 기본값처럼 박음.
- self-tx 안에서 같은 row 에 lock 거는 건 self-lock 이라 즉시 통과 → 락이 빠져 있어도 동일하게 그린.
- commit boundary 가 없으니 "다른 tx 가 본 값" 이 정의되지 않음 — 가시성 검증 불가.

**액션플랜**
- 락·트랜잭션 경계·dedup 같은 검증이 핵심인 spec 에는 클래스 `@Transactional` 금지를 룰화.
- `TransactionTemplate` 으로 각 단계 별도 tx 만들고 `afterTest` 에서 명시 cleanup.
- 회고: 통합 테스트 전반에 같은 패턴이 박혀 있을 가능성 — 한번 ripgrep 으로 전수조사 해봐야 함.

---

## 배운 점

### Mutation test 사고방식 — "prod 한 줄 떼도 spec 이 잡아주나?"

**배움**
- 통합 테스트가 "동작 확인" 에서 멈추면 silent regression 막기 어려움.
- prod 의 `@Lock(PESSIMISTIC_WRITE)` 를 떼는 mutation 을 미리 가정하고, 그게 떨어지면 spec 이 fail 하도록 설계.
- wait 시간 측정처럼 "락이 잡혔다는 증거" 를 명시적으로 검증해야 mutation 에 강함.

**의미**
- 락·timeout·동시성 코드는 mutation 안전망이 특히 중요 — 어노테이션 한 줄 빠져도 정적 검사로 안 잡힘.
- 통합 테스트 짤 때 "이 prod 라인을 떼면 이 spec 이 어떻게 fail 하지?" 를 머릿속에서 한번 돌려보자.
- 도구 (Pitest 등) 없어도 사고방식만 가지고 가도 효과 큼.

### Integration test 의 commit boundary 가 검증의 단위

**배움**
- `PESSIMISTIC_WRITE` / 가시성 / dedup race 처럼 commit boundary 가 본질인 검증은 multi-tx 가 필수.
- 클래스 `@Transactional` 은 편의는 주지만 commit boundary 를 없애버려서 검증을 무력화.
- `TransactionTemplate` 으로 seed / sut / reload 를 분리하면 락도 가시성도 dedup race 도 진짜로 검증 가능.

**의미**
- "통합 테스트 = `@SpringBootTest` + `@Transactional`" 자동 반사 그만.
- spec 이 검증하는 게 commit 이후 동작인지 먼저 묻자 — 맞으면 클래스 `@Transactional` 빼고 `TransactionTemplate` 으로 분리.
- 단위 테스트의 "롤백 격리" 편의를 통합 테스트에 그대로 가져오면 가짜 그린이 나옴.

---

## 핵심 내용

### 키워드
- `PESSIMISTIC_WRITE`, `@Lock`, `findByIdForUpdate`, `TransactionTemplate`, `CountDownLatch`, `mutation testing`, `multi-tx`, `commit boundary`

### 요약
- L4 통합 테스트에서 `PESSIMISTIC_WRITE` 실효성 검증은 두 thread + `acquiredLatch` / `releaseLatch` + `holdMs` 패턴이 정석. (1) wait 시간 ≥ `holdMs` (락 잡힘 증거) (2) thread B 가 본 값 = thread A commit 결과 (가시성).
- 클래스 레벨 `@Transactional` 은 self-tx 안에서 self-lock 이라 락 검증을 무력화. `PESSIMISTIC_WRITE` / 가시성 / dedup race spec 은 클래스 `@Transactional` 제거 후 `TransactionTemplate` 으로 seed / sut / reload / cleanup 각각 별도 tx.
- prod 의 `@Lock` 어노테이션을 떼는 mutation 을 가정하고 spec 이 fail 하는지 확인하는 사고방식 (mutation testing) 이 silent regression 안전망.

### 코드/명령어

L4 락 검증 패턴:
```kotlin
val acquiredLatch = CountDownLatch(1)
val releaseLatch = CountDownLatch(1)
val holdMs = 600L
val pool = Executors.newFixedThreadPool(2)

val threadA = pool.submit {
    transactionTemplate.executeWithoutResult {
        val sub = subAccountRepository.findByIdForUpdate(subId)!!
        sub.unuse(rollbackAmount)
        acquiredLatch.countDown()
        releaseLatch.await(5, TimeUnit.SECONDS)  // commit 직전까지 hold
    }
}
val threadB = pool.submit {
    acquiredLatch.await(5, TimeUnit.SECONDS)
    val startNs = System.nanoTime()
    transactionTemplate.executeWithoutResult {
        val sub = subAccountRepository.findByIdForUpdate(subId)!!  // wait
        threadBSeenUsedToday.set(sub.usedToday)
    }
    threadBWaitMs.set((System.nanoTime() - startNs) / 1_000_000)
}

acquiredLatch.await(5, TimeUnit.SECONDS)
Thread.sleep(holdMs)
releaseLatch.countDown()

threadBWaitMs.get() shouldBeGreaterThanOrEqual (holdMs - 100)
threadBSeenUsedToday.get() shouldBe (initialUsed - rollbackAmount)
```

Multi-tx 분리 (클래스 `@Transactional` 제거):
```kotlin
// NG — 클래스 레벨 @Transactional. self-tx 라 PESSIMISTIC_WRITE 무력화
@Transactional
class WithdrawalPgNotificationServiceIntegrationSpec(...)

// OK — TransactionTemplate 으로 각 단계 분리
class WithdrawalPgNotificationServiceIntegrationSpec(
    private val transactionTemplate: TransactionTemplate,
) : FunSpec({
    test("FAILED 노티 시 usedToday 환원") {
        val recordId = transactionTemplate.execute { /* seed */ }!!
        transactionTemplate.executeWithoutResult { sut.apply(payload) }
        val reloaded = transactionTemplate.execute { /* reload */ }!!
        // assertions
    }
    afterTest { /* cleanup */ }
})
```

### 참고 자료
- Hibernate User Guide — Pessimistic locking: https://docs.jboss.org/hibernate/orm/current/userguide/html_single/Hibernate_User_Guide.html#locking-pessimistic
- Mutation testing (Pitest): https://pitest.org/
