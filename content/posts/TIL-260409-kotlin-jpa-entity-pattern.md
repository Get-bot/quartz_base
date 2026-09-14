---
title: "[TIL-260409] Kotlin JPA Entity 패턴 — 선착순 이벤트 도메인 설계"
date: 2026-04-09
tags: ["Kotlin", "JPA", "Spring Boot", "QueryDSL", "KSP", "Entity"]
categories: ["TIL"]
description: "Kotlin JPA Entity에서 주 생성자 + protected set 패턴, plugin.jpa/allOpen 역할, kotlin.time vs java.time 호환성 이슈"
---

## 잘한 점

### 상황 1
- 선착순 쿠폰 이벤트 시스템의 핵심 도메인인 Event, CouponIssue 엔티티를 설계해야 했다. Kotlin + JPA 조합에서 엔티티를 어떻게 구성할지 패턴을 잡아야 하는 단계.

### 액션 1
- Kotlin의 주 생성자를 활용한 엔티티 패턴을 적용했다. 생성자 파라미터로 필수값을 받고, 프로퍼티에 `protected set`을 걸어서 외부 변경을 차단하는 구조로 잡았다. 도메인 로직(`issue()`, `open()`, `close()`)도 엔티티 안에 넣어서 Rich Domain Model로 설계.

### 칭찬 1
- 첫 엔티티 설계부터 `protected set`, 도메인 로직 캡슐화, 상태 검증(`check()`)까지 챙긴 게 좋았다. 처음부터 패턴을 제대로 잡아놓으면 이후 엔티티들도 이 기준을 따르면 되니까.

---

## 개선점

### 문제 1
- `kotlin.time.Instant`를 사용했는데 QueryDSL KSP codegen에서 `Comparable<Instant>` 타입 변환 에러가 터졌다. 빌드가 안 됨.

### 원인 1
- `kotlin.time.Instant`는 비교적 새로운 Kotlin stdlib 타입이라 QueryDSL KSP가 아직 지원을 안 한다. `KSType has type arguments, which are not supported for ClassName conversion` 에러.

### 액션플랜 1
- JPA 엔티티 시간 타입은 `java.time.Instant`를 쓰자. Kotlin stdlib 시간 API는 JPA/Hibernate/QueryDSL 생태계와 아직 호환이 안 된다.

### 문제 2
- IntelliJ에서 "Class 'Event'에는 [public, protected] no-arg 생성자가 포함되어야 합니다" 경고가 뜨는데, `plugin.jpa`가 적용되어 있어서 실제로는 문제없음.

### 원인 2
- WSL 환경에서 IntelliJ의 noArg 플러그인 인식이 안 되는 알려진 버그 (KTIJ-21314). IDE 정적 분석의 false positive.

### 액션플랜 2
- 무시해도 됨. IntelliJ 2026.1에서 개선 예정. 빌드/런타임에는 문제없으니 경고에 휘둘리지 말자.

---

## 배운 점

### 배움 1
- Kotlin JPA 엔티티에서 `plugin.jpa`(no-arg)와 `allOpen`이 하는 역할을 제대로 이해하게 됐다. JPA는 프록시를 만들기 위해 엔티티가 `open`이어야 하고, 리플렉션으로 인스턴스를 만들기 위해 no-arg 생성자가 필요하다. Kotlin은 기본이 `final`이고 no-arg 생성자가 없으니까, 이 두 플러그인이 컴파일 타임에 바이트코드를 조작해서 해결해준다.

### 의미 1
- "플러그인 넣으면 된다"가 아니라 **왜** 필요한지를 알게 됐다. 나중에 프록시 관련 이슈가 터져도 원인을 빠르게 잡을 수 있을 것 같다.

### 배움 2
- `kotlin.time` vs `java.time` — Kotlin에 자체 시간 API가 생겼지만, JPA/Hibernate/QueryDSL 같은 Java 생태계 라이브러리와는 아직 호환이 안 된다. 엔티티 레이어에서는 `java.time`을 써야 한다.

### 의미 2
- 새 API가 나왔다고 바로 쓰면 안 된다. 생태계 호환성부터 확인하자. 특히 코드 생성기(KSP) 쪽은 더 느리게 따라오는 경향이 있다.

---

## 핵심 내용

### 키워드
- `Kotlin JPA Entity`, `protected set`, `plugin.jpa`, `allOpen`, `Rich Domain Model`, `java.time.Instant`, `QueryDSL KSP`, `@JdbcTypeCode`

### 요약
- Kotlin JPA 엔티티는 주 생성자로 필수값을 받고, `protected set`으로 캡슐화한다. `plugin.jpa`가 no-arg 생성자를, `allOpen`이 open 클래스를 컴파일 타임에 자동 생성한다.
- 엔티티 시간 타입은 `java.time.Instant`를 사용한다. `kotlin.time.Instant`는 QueryDSL KSP 등에서 아직 미지원.
- 도메인 로직은 엔티티 안에 넣되, `check()`로 상태 전이 규칙을 강제한다.

### 코드/명령어

```kotlin
// Kotlin JPA Entity 패턴 — 주 생성자 + protected set
@Entity
@Table(name = "events")
class Event(
    title: String,
    totalQuantity: Int,
    eventStatus: EventStatus,
    startedAt: Instant,   // java.time.Instant
    endedAt: Instant,
) : BaseTimeEntity() {
    @Id
    @JdbcTypeCode(SqlTypes.UUID)
    var id: UUID = UUID.randomUUID()
        protected set

    var title: String = title
        protected set

    // 도메인 로직 — 상태 검증 포함
    fun issue() {
        check(isIssuable()) { "발급 불가" }
        issuedQuantity++
    }
}
```

```kotlin
// build.gradle.kts — 필수 플러그인
kotlin("plugin.jpa") version "2.3.20"  // no-arg 생성자 자동 생성
kotlin("plugin.spring") version "2.3.20"  // allOpen 포함

// allOpen 대상 명시
allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}
```

### 참고 자료
- [KTIJ-21314: noArg plugin not recognised on WSL](https://youtrack.jetbrains.com/issue/KTIJ-21314)
- [KT-36964: JPA Plugin false positive](https://youtrack.jetbrains.com/issue/KT-36964)
- [Kotlin No-arg plugin 공식 문서](https://kotlinlang.org/docs/no-arg-plugin.html)
