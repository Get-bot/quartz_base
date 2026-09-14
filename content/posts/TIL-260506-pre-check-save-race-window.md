---
title: "[TIL-260506] 사전 체크-save 사이 race window 방어 패턴"
date: 2026-05-06
tags: ["Spring", "JPA", "PostgreSQL", "동시성", "Kotlin", "Race Condition"]
categories: ["TIL"]
description: "사전 체크 후 save 사이의 race window를 DataIntegrityViolationException 변환으로 방어하는 패턴과 UNIQUE 선언 컨벤션 통일"
---

## 잘한 점

### Copilot PR 리뷰 후속, 동시성 갭 빠르게 메움

**상황**
- BUWS-39 PR에 Copilot이 "사전 체크와 save 사이 race window가 있다"고 지적
- `SubAccountService.create()`가 `pocketCode` UNIQUE를 사전 조회로 확인한 뒤 `save()` 하는 구조였는데, 두 콜이 거의 동시에 동일 코드를 선점할 수 있음

**액션**
- `save()`를 `try`로 감싸고 `DataIntegrityViolationException` 을 `BusinessException(WITHDRAWAL_POCKET_CODE_GENERATION_FAILED)` 로 변환
- 사전 체크는 그대로 둠 (정상 케이스 빠른 실패용), DB UNIQUE 제약이 race window의 최후 보루 역할
- `RegisteredAppService` / `MasterAccountService` 의 기존 패턴과 정렬 — 새 패턴이 아니라 기존 컨벤션 따라잡은 것

**칭찬**
- 같은 PR에서 UNIQUE 선언 컨벤션 통일까지 묶어 처리한 것
  - `CREATE UNIQUE INDEX` → `ALTER TABLE ADD CONSTRAINT UNIQUE` 로 다른 테이블과 일관
  - 엔티티의 `@Table(indexes=Index(unique=true))` 와 `@Column(unique=true)` 중복 제거 → 단일 진실 원천
- 회귀 방지로 race window 시나리오 테스트도 1건 추가

---

## 개선점

### "사전 체크 = 충분"이라는 무의식적 가정

**문제**
- 처음 구현할 때 사전 조회로 unique 검증해놓고 race window를 의식조차 못 했음
- Copilot이 짚어주기 전까진 안전하다고 생각함

**원인**
- `validate → save` 순서가 머릿속에서 "원자적"으로 보임. 실제로는 두 SQL이 별개 시점에 발생하는데
- 다른 도메인(`RegisteredApp` / `MasterAccount`)에 이미 같은 패턴이 있는데 거기서 학습이 옮겨오지 않음 — 도메인별로 따로 짜는 습관

**액션플랜**
- "사전 체크가 있는 UNIQUE 자원 생성" 코드를 짤 때 DB 제약 위반 fallback 분기를 항상 짝으로 둘 것 — 셀프 체크리스트화
- PR 셀프 리뷰 단계에 "race window 점검" 항목 추가
- 다음 슬라이스(`withdrawal-safety-cron`)에서도 cron 동시 실행 방어(Redisson `tryLock(0)`) 짤 때 같은 사고 패턴 재사용

---

## 핵심 내용

### 키워드
- `DataIntegrityViolationException`, `race window`, `UNIQUE constraint`, `BusinessException cause chaining`, `Spring DAO Exception Translation`

### 요약
- **사전 체크-save race window**: 두 트랜잭션이 거의 동시에 (a) UNIQUE 자원 부재 확인 → (b) save 호출 시 양쪽 다 사전 체크는 통과, save에서 한쪽이 DB UNIQUE 제약 위반.
- **방어 패턴**: 사전 체크는 빠른 실패용으로 유지 + save를 `try-catch DataIntegrityViolationException` 으로 감싸 도메인 예외로 변환. `cause` 체이닝으로 원본 예외 보존.
- **UNIQUE 선언 컨벤션 (Postgres + JPA)**: `ALTER TABLE ADD CONSTRAINT ... UNIQUE` 를 단일 진실 원천으로. JPA 엔티티는 `@Column(unique=true)` 만, `@Table(indexes=...)` 로 중복 선언 금지.
- Spring이 JDBC `SQLException` → `DataIntegrityViolationException` 으로 자동 변환해줌 (Exception Translation). catch 타입은 JPA/Hibernate 의존이 아니라 Spring DAO 추상.

### 코드/명령어

```kotlin
// SubAccountService.create — race window 방어
val pocketCode = generateUniquePocketCode()  // 사전 체크 포함 (정상 케이스 빠른 실패)
val saved = try {
    subAccountRepository.save(req.toEntity(pocketCode))
} catch (e: DataIntegrityViolationException) {
    // race window: 사전 체크 통과 후 다른 tx가 동일 code 선점
    throw BusinessException(ErrorCode.WITHDRAWAL_POCKET_CODE_GENERATION_FAILED, cause = e)
}
```

```sql
-- 마이그레이션 컨벤션 통일
-- ❌ CREATE UNIQUE INDEX uk_sub_pocket_code ON sub_account (pocket_code);
-- ✅
ALTER TABLE sub_account
    ADD CONSTRAINT uk_sub_pocket_code UNIQUE (pocket_code);
```

```kotlin
// JPA 엔티티 — UNIQUE는 @Column 한 곳에만
@Entity
@Table(name = "sub_account")  // indexes=Index(unique=true) 중복 선언 금지
class SubAccount(
    @Column(name = "pocket_code", nullable = false, unique = true, length = 6)
    val pocketCode: String,
)
```
