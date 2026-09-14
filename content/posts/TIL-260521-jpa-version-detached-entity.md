---
title: "[TIL-260521] JPA @Version 어노테이션 함정 + detached entity 회귀 차단"
date: 2026-05-21
tags: ["Spring Boot", "Kotlin", "JPA", "Hibernate", "Optimistic Lock"]
categories: ["TIL"]
description: "JPA optimistic lock 은 jakarta.persistence.Version 만 동작. Spring Data 의 같은 이름 어노테이션은 REST 용이라 silent bug. detached entity 가 dirty checking 에서 누락되는 회귀도 같이 차단."
---

## 잘한 점

### Detached entity 시그니처 차단으로 dirty checking 복구

**상황**
- `WithdrawalSyncTxRunner.run` 의 시그니처가 `subAccount: SubAccount` 였음.
- `WithdrawalService` 가 outer 에서 lookup 한 entity 를 그대로 tx 로 넘기는 구조였음.
- 결과적으로 `tryUse` 가 `usedToday` 를 변경해도 DB 에 반영이 안 되고 있었음.

**액션**
- 시그니처를 `subAccountId: UUID` 로 변경하고 tx 안에서 `findByIdOrNull` 재조회로 바꿈.
- 이러면 entity 가 영속 컨텍스트에 등록되니까 dirty checking 으로 자연스럽게 commit.
- `WithdrawalSyncTxRunnerSpec` 에 `usedToday` 영구화 검증 + `SUB_ACCOUNT_NOT_FOUND` 시나리오 추가해서 회귀 차단.

**칭찬**
- "한도가 왜 안 쌓이지?" 같은 증상 보고서가 들어오기 전에 코드 리뷰 단계에서 잡은 게 좋음.
- 그냥 고치고 끝내지 않고 영구화 검증 spec 까지 짜서 silent regression 안전망까지 친 것.

---

## 개선점

### `org.springframework.data.annotation.Version` 으로 박혀 있던 silent bug

**문제**
- `SubAccount.@Version` 이 `org.springframework.data.annotation.Version` 으로 박혀 있었음.
- JPA 가 이 어노테이션을 인식 못해서 optimistic lock 이 사실상 무용지물.
- `version` 컬럼은 있지만 증가가 안 되니까 동시성 충돌 감지가 통째로 비어 있던 셈.

**원인**
- 이름이 똑같은 어노테이션이 두 패키지에 존재 (`org.springframework.data.annotation.Version` vs `jakarta.persistence.Version`).
- IDE 자동 import 가 첫 번째 후보를 잡아주면 그대로 통과.
- 컴파일도 되고 컬럼 매핑도 되니까 정적 검사로는 안 잡힘 — 런타임에도 조용함.

**액션플랜**
- `jakarta.persistence.Version` 으로 교체 (이번 PR 에서 처리).
- 어노테이션 import 할 때 패키지 한번 더 확인하는 습관.
- 기존 코드에 `org.springframework.data.annotation` 으로 박힌 게 또 있을 가능성 — ripgrep 으로 한번 훑어볼 가치 있음.

---

## 배운 점

### 같은 이름 어노테이션이 두 개 있을 때의 silent bug

**배움**
- JPA optimistic lock 은 `jakarta.persistence.Version` 만 동작한다.
- Spring Data 가 같은 이름의 어노테이션을 따로 제공하는데, 이건 Spring Data REST 의 ETag / HTTP cache 용.
- 같은 이름이라 IDE 자동 import 가 잘못된 후보를 잡아도 컴파일·런타임 모두 조용히 통과.

**의미**
- "이름이 똑같으니 둘 다 비슷한 거겠지" 추측이 silent bug 의 표준 코스.
- 동시성·트랜잭션·락 관련 어노테이션은 import 출처를 한번 더 확인하자.
- 코드 리뷰에서 import 라인 보는 습관도 같이 들이자.

### Detached entity 와 dirty checking 의 전제

**배움**
- Service 외부에서 lookup 한 entity 를 tx 안으로 넘기면 detached 상태.
- detached 면 dirty checking 대상이 아니라서 setter 호출이 DB 에 반영 안 됨.
- `@Version` 증가도 detached 에서는 안 일어남 — optimistic lock 의 핵심 조건이 빠지는 셈.

**의미**
- "`@Transactional` 안에서 호출하면 다 되는 줄 알았다" 는 흔한 오해.
- tx 안에서 다시 조회하는 게 안전 — 외부에서 받은 entity 는 인자로 받지 말고 ID 만 받는 시그니처를 우선 고려.

---

## 핵심 내용

### 키워드
- `jakarta.persistence.Version`, `org.springframework.data.annotation.Version`, `detached entity`, `dirty checking`, `optimistic lock`

### 요약
- JPA optimistic lock 은 `jakarta.persistence.Version` 으로만 동작한다. Spring Data 의 `@Version` 은 REST / HTTP cache 용이라 JPA 는 인식 안 함.
- Service 외부에서 lookup 한 entity 를 tx 로 넘기면 detached → `tryUse` 같은 도메인 메서드가 호출돼도 DB 에 반영 안 됨. tx 안에서 `findByIdOrNull` 로 재조회해야 managed 상태가 되어 dirty checking + `@Version` 증가가 동작.

### 코드/명령어

올바른 `@Version`:
```kotlin
import jakarta.persistence.Version  // OK — JPA optimistic lock
// import org.springframework.data.annotation.Version  // NG — Spring Data REST 용

@Version
@Column(name = "version", nullable = false)
var version: Long = 0
    protected set
```

Detached 회피 — tx 안 재조회:
```kotlin
// NG — outer 에서 lookup 한 entity 를 그대로 받음 → detached
@Transactional
fun run(subAccount: SubAccount, ...) {
    subAccount.tryUse(amount)  // dirty checking 안 됨
}

// OK — ID 로 받고 tx 안에서 재조회 → managed
@Transactional
fun run(subAccountId: UUID, ...) {
    val sub = subAccountRepository.findByIdOrNull(subAccountId)
        ?: throw BusinessException(SUB_ACCOUNT_NOT_FOUND)
    sub.tryUse(amount)  // managed → dirty checking + @Version 증가
}
```

### 참고 자료
- jakarta.persistence.Version — https://jakarta.ee/specifications/persistence/3.1/apidocs/jakarta.persistence/jakarta/persistence/version
- Spring Data Version (REST) — https://docs.spring.io/spring-data/commons/reference/auditing.html
