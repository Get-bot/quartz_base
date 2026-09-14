---
title: "[TIL-260412] PR 리뷰로 정리한 Kotlin/Spring Boot 코드 품질 패턴"
date: 2026-04-12
tags: ["Kotlin", "Spring Boot", "enum lazy", "Bean Validation", "코드 리뷰"]
categories: ["TIL"]
description: "Kotlin enum 전방 참조 + by lazy 캐싱, kotlin-stdlib 자동 추가, Bean Validation nullable 패턴"
---

## 잘한 점

### 3-에이전트 병렬 코드 리뷰로 PR 전 점검

**상황**
- event-crud API 구현 끝나고 PR 올리기 전 단계
- 동작은 하는데, 품질 면에서 놓친 게 없는지 한번 훑어보고 싶었음
- `/simplify`로 재사용/품질/효율성 3개 관점의 리뷰 에이전트를 동시에 돌림

**액션**
- 3개 에이전트가 각자 다른 관점으로 리뷰 → 이슈 6개 찾아냄
- 하나씩 "이거 진짜 문제야?" 따져보고 직접 수정
- 에이전트 제안 그대로 안 따르고, EventStatus는 `when` + `by lazy`로 더 깔끔하게 바꿨고, 쓰이지 않는 `isIssuable()` 메서드도 같이 정리함

**칭찬**
- 리뷰 결과 맹신 안 하고 하나씩 판단한 것. 실제로 EventCreateRequest nullable 건은 의도된 설계라서 걸러냈다 — 이거 그냥 적용했으면 validation 에러 메시지 다 깨졌을 듯
- 제안된 것 외에 Kotest 6.1.0 / MockK 1.14.9 업그레이드 + 버전 변수 추출까지 추가로 챙긴 건 좀 잘한 듯

---

## 개선점

오늘은 특별히 없음

---

## 배운 점

### Kotlin enum 전방 참조와 lazy 초기화

**배움**
- `EventStatus`에서 `READY`가 `setOf(OPEN)`을 참조하는데, enum은 선언 순서대로 초기화되니까 `READY` 시점에 `OPEN`이 아직 없음
- 그래서 람다 `() -> Set<EventStatus>`로 지연 평가하고 있었는데, 이러면 `canTransitionTo()` 호출마다 새 Set이 힙에 생김
- `by lazy`로 감싸면 첫 호출 때 한 번만 만들고 이후 캐싱. 고빈도 호출에서 GC 압력이 줄어든다

**의미**
- enum에서 다른 enum 값 참조할 때 전방 참조 제약을 항상 의식해야 한다. 이걸 진작 알았으면 처음부터 lazy로 짰을 텐데
- `by lazy`가 단순 "지연 로딩"만이 아니라 "초기화 순서 우회 + 캐싱"으로도 쓸 수 있다는 걸 체감함

---

## 핵심 내용

### 키워드
- `Kotlin enum lazy`, `by lazy`, `kotlin-stdlib 자동 추가`, `Bean Validation @field:NotNull vs non-null 타입`

### 요약
- Kotlin Gradle 플러그인은 `kotlin-stdlib`를 자동 추가한다. 명시적 `implementation(kotlin("stdlib"))`는 중복이므로 제거.
- Kotlin enum에서 다른 enum 값을 참조할 때 전방 참조 제약이 있다. 람다로 지연 평가하되 `by lazy`로 캐싱하면 매 호출 객체 생성을 방지할 수 있다.
- DTO에서 `Int?` + `@field:NotNull` + `!!` 패턴은 의도적이다. non-null 타입으로 선언하면 JSON null 시 Jackson 역직렬화에서 먼저 터져서 Bean Validation의 사용자 친화적 에러 메시지가 나오지 않는다. `@field:NotBlank`는 null 체크를 포함하므로 `String`(non-null) 사용 가능.
- 같은 패키지 내 클래스는 import 없이 참조 가능. IDE 자동 import가 불필요한 import를 추가하는 경우가 있다.

### 코드/명령어

```kotlin
// Before: 매 호출마다 새 Set 생성
enum class EventStatus(
    private val allowedTransitions: () -> Set<EventStatus>,
) {
    READY({ setOf(OPEN) }),  // 호출할 때마다 setOf() 실행
}

// After: lazy로 1회만 생성, 이후 캐싱
enum class EventStatus {
    READY;
    val allowedTransitions: Set<EventStatus> by lazy {
        when (this) {
            READY -> setOf(OPEN)
            OPEN -> setOf(CLOSED)
            CLOSED -> emptySet()
        }
    }
}
```
