---
title: "[TIL-260429] DDD Rich Domain — Aggregate 분리, 금융 VO, 도메인 enum 도입"
date: 2026-04-29
tags: ["DDD", "Aggregate", "Kotlin", "Spring Boot", "JPA", "Value Object"]
categories: ["TIL"]
description: "SubAccount Entity v1.3 in-place 재작성으로 Aggregate 독립, @Embeddable 금융 VO 표준 패턴 정착, RegisteredAppType enum 도입"
---

## 잘한 점

### SubAccount Entity v1.2 → v1.3 in-place 재작성 (Aggregate 독립)

**상황**
- 출금 도메인 Aggregate 경계를 다시 그리는 중이었음
- v1.2는 SubAccount가 `masterAccountId`를 들고 있고 잔액도 `allocatedBalance / usedBalance`로 모델링되어 있었는데, 실제 비즈니스 규칙은 "일일 한도 + 일일 사용량"이었음
- 다행히 v1.2 마이그레이션이 아직 prod 미배포 상태라 in-place 재작성이 가능했음

**액션**
- `masterAccountId` 필드 제거 → SubAccount Aggregate를 진짜 독립적으로 만듦
- `allocatedBalance/usedBalance` → `dailyLimit/usedToday`로 도메인 언어 통일
- Rich Domain 메서드 4종을 Entity 안에 박음: `tryUse / unuse / changeDailyLimit / resetDailyUsage`
- ErrorCode도 같이 정렬: `ALLOCATION_BELOW_USED` → `LIMIT_BELOW_USED`, `INSUFFICIENT_BALANCE` → `INSUFFICIENT_DAILY_BALANCE`
- v1.3 Migration도 in-place로 재작성 (V20260427100400)

**칭찬**
- 도메인 언어 잘못 잡힌 걸 미배포 시점에 알아채고 정면으로 다시 짠 결정 — 배포 후였으면 backfill 마이그레이션 + 코드 호환 레이어로 며칠 갔을 일
- Rich Domain Model 원칙 지키느라 Service에 로직 안 쌓이고 Entity 안에 들어간 것

---

### 금융 VO 표준 패턴 정착 (`Money`, `BankAccount` @Embeddable)

**상황**
- MasterAccount + BankPgConfig 도메인 들어가면서 금액·계좌번호·PG 코드가 곳곳에서 String/Long으로 떠다니고 있었음
- 곧 출금 핵심(Withdrawal-Core)에서 Money 연산이 본격적으로 시작될 예정

**액션**
- `global/common/finance/` 패키지 신설 → `Money`, `BankAccount`, `PgCode` 표준 VO 추출
- JPA_WRITE_GUIDE §3.3에 @Embeddable VO 표준 패턴 명시 (생성자 검증, equals 자동, 컬럼 매핑)
- BankPgCredentials는 평문이 절대 새면 안 되니까 PiiMask로 toString/Logger 마스킹 처리

**칭찬**
- 처음부터 "있을 법한 미래"용 VO를 만들지 않고, **이미 두 군데 이상에서 쓰이고 있는 것**만 추출 — 추상화 욕심 안 부린 것

---

### RegisteredAppType enum 도입 + 출금 노티 도메인 골격

**상황**
- WithdrawalRecord에 "어디서 들어온 출금인지" 추적 필드가 필요했음 (APP / WEB)
- Plain String으로 두면 오타·비교 실수 무한히 생길 자리

**액션**
- `RegisteredAppType` enum 추가 (`APP / WEB`)
- RegisteredApp 생성 시 필수 + **불변** 으로 선언 (생성 후 변경 불가)
- findAll에 type 필터 추가 → status AND type 복합 필터 지원
- WithdrawalRecord에 `appType` 필드 추가 + 인덱스 보강
- `WithdrawalStatus` enum 추가, `withdrawal/notification` 패키지 골격까지 잡음

---

## 개선점

### v1.2 → v1.3 in-place가 가능했던 건 운이 좋았던 것

**문제**
- 이번엔 prod 미배포라 in-place로 갈아엎을 수 있었지만, 한 번이라도 배포된 뒤에 같은 결정을 내렸으면 backfill·호환 레이어·롤백 플랜까지 다 짜야 했을 것

**원인**
- v1.2 설계 단계에서 도메인 언어를 충분히 검증 안 한 채 Entity 형태부터 박았음
- `allocatedBalance/usedBalance`가 사실은 "잔액"이 아니라 "일일 한도/사용량"이라는 걸 구현 중반에 깨달음

**액션플랜**
- Entity 박기 전에 Plan/Design 문서에서 **도메인 용어 사전**을 먼저 확정하고 PR 리뷰
- 도메인 용어가 흔들릴 것 같으면 마이그레이션 합치지 말고 PR 단위로 끊어서 빠르게 retracement 가능하게

---

## 배운 점

### Aggregate 독립의 의미

**배움**
- SubAccount에서 `masterAccountId`를 빼니까 SubAccount만 단독으로 테스트·생성·삭제 가능해짐
- "ID 참조 vs `@ManyToOne`" 차이가 진짜 체감되는 순간 — 같은 트랜잭션·같은 영속성 컨텍스트로 묶이지 않는 것이 핵심
- Aggregate가 진짜 독립적이면 Service 테스트에서 Mock 대상이 명확해짐

**의미**
- 다음에 새 Entity 만들 때 "이게 누구의 Aggregate인가?" 먼저 묻고 시작
- ID 참조가 기본, `@ManyToOne`은 같은 Aggregate일 때만

---

### Rich Domain Model이 무엇을 막아주는가

**배움**
- `tryUse(amount)` 한 메서드 안에서 "한도 검증 + 사용량 증가 + 불변식 유지"가 한 단위로 이뤄짐
- 이걸 Service에서 풀면 누군가 한도 검증 빼먹고 사용량만 증가시키는 코드를 쉽게 짠다
- Entity는 "잘못된 상태가 되는 걸 거부"하는 게 본업

**의미**
- 비즈니스 규칙은 항상 Entity 안에서 한 메서드로 끝나게 — Service는 오케스트레이션만

---

## 핵심 내용

### 키워드
- `Aggregate 독립`, `ID 참조`, `Rich Domain Model`, `@Embeddable VO`, `JPA_WRITE_GUIDE §3.3`, `RegisteredAppType`, `WithdrawalStatus`

### 요약
- **Aggregate 독립**: 다른 Aggregate는 ID 참조만. `@ManyToOne` 금지. 같은 트랜잭션 보장이 필요한 단위만 한 Aggregate.
- **Rich Domain Model**: 비즈니스 규칙 = Entity 메서드. Service는 검증·할당된 메서드 호출 + 트랜잭션 경계만.
- **금융 VO 패턴**: `Money` / `BankAccount` / `PgCode` `@Embeddable`, 생성자에서 검증, PII는 toString 마스킹.
- **enum 불변 필드**: 생성 시 필수 + setter 없음. 비즈니스적으로 "바뀌면 안 되는 것"은 코드로 강제.

### 코드/명령어
```kotlin
// SubAccount v1.3 — Rich Domain 메서드
fun tryUse(amount: Money) {
    require(amount.isPositive()) { "amount must be positive" }
    val next = usedToday + amount
    if (next > dailyLimit) {
        throw BusinessException(WITHDRAWAL_INSUFFICIENT_DAILY_BALANCE)
    }
    usedToday = next
}

fun changeDailyLimit(newLimit: Money) {
    if (newLimit < usedToday) {
        throw BusinessException(WITHDRAWAL_LIMIT_BELOW_USED)
    }
    dailyLimit = newLimit
}
```

### 참고 자료
- `docs/engine/JPA_WRITE_GUIDE.md` §3.3 (@Embeddable VO 표준 패턴)
- `docs/02-design/features/sub-account-crud.design.md`
- 커밋: `3a73543` (SubAccount v1.3), `a630f7b` (금융 VO), `cedce39` (RegisteredAppType)
