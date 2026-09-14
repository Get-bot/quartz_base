---
title: "[TIL-260410] DDD 도메인 설계 3원칙 — Rich Domain Model / Value Object / Aggregate 경계"
date: 2026-04-10
tags: ["DDD", "Kotlin", "Spring Boot", "JPA", "도메인설계", "Aggregate", "Value Object"]
categories: ["TIL"]
description: "Event 엔티티를 Rich Domain Model로 리팩토링하면서 DateRange VO 추출, Event↔CouponIssue Aggregate 경계 분리까지 DDD 3가지 tactic을 한 흐름으로 적용"
---

## 잘한 점

### Event 엔티티를 Rich Domain Model로 리팩토링

**상황**
- Event 엔티티가 getter/setter 덩어리였고, 상태 전이 규칙(`READY → OPEN → CLOSED`)이랑 재고 차감 로직이 전부 `EventService`에 쌓여 있었음
- 전형적인 Anemic Domain Model — Entity는 빈 껍데기, Service는 비대
- 선착순 쿠폰 발급이라는 도메인 특성상 "어떤 상태에서 어떤 행동이 가능한가"가 핵심인데, 그 규칙이 흩어져 있으니 테스트·재사용이 힘들었음

**액션**
- 한 세션에 DDD 3가지 tactic을 연결해서 적용
- **Rich Domain Model**: `Event`에 `issue()`, `open()`, `close()`, `isIssuable()` 메서드 이동. `EventStatus` enum에도 `isIssuable` 프로퍼티 + `transitionTo()` 내장. Service는 유스케이스 orchestration만.
- **Value Object 추출**: `startedAt`/`endedAt`을 `@Embeddable DateRange`로 뽑아서 `startedAt < endedAt` 불변식을 VO `init` 블록 한 곳에 고정
- **Aggregate 경계**: `Event ↔ CouponIssue`를 `@ManyToOne` 대신 `eventId: UUID`로만 참조. 트랜잭션 경계 분리 + N+1 방지

**칭찬**
- 처음엔 3개 다 따로 다른 이슈로 올라왔는데 결국 "Event 리팩토링"이라는 하나의 스토리로 엮어낸 것
- 교과서에서만 보던 DDD tactic을 실제 코드에서 한 번에 연결해서 써본 게 좀 뿌듯
- "지금 꼭 VO 추출해야 하나?" 같은 YAGNI 질문을 스스로 던지고 근거 있게 결정한 판단 과정

---

## 개선점

### Value Object 추출 판단을 번복

**문제**
- `DateRange` Value Object를 처음엔 "오버스펙"이라고 보류했다가, "두 번째 기간 개념(Coupon 유효기간) 생길 조짐"이 보이자 바로 번복
- Plan 문서를 수정하는 동안 결정이 왔다갔다 한 느낌
- 추출 후엔 `EventResponse.from()`, `EventQuery.periodMatches` 등 연쇄적으로 수정해야 했음

**원인**
- "YAGNI vs 확장성" 타이밍 판단이 애매했음
- Martin Fowler의 "Refactor to Discovery"(같은 패턴이 3번 나타나기 전엔 추상화하지 마라)를 너무 교조적으로 적용하려 함
- 근데 "불변식이 독립적으로 중요한 경우"까지 지나치게 보수적으로 봤음

**액션플랜**
- 다음엔 "지금 당장 2개 이상 쓰는가 + 불변식이 있는가" 두 조건이면 VO 추출을 바로 결정하자
- 불변식은 독립적으로 중요한 설계 요소 — "미래에 쓸지 모를 추상화"가 아니라 "지금 도메인 규칙을 지키는 수단"으로 보면 추출 판단이 쉬워짐

### Event.issue() 예외를 처음엔 하나로 퉁침

**문제**
- 처음엔 `EVENT_NOT_ISSUABLE` 하나로 퉁쳤다가 나중에 `EVENT_NOT_OPEN` + `EVENT_OUT_OF_STOCK`으로 세분화
- 원인별 분리를 처음부터 못 함 → 클라이언트 UX 분기 불가

**원인**
- "발급 불가능"이라는 한 문장으로 묶어서 표현하는 게 자연스러워 보였음
- 근데 클라이언트 UX 관점에선 "재고 소진"과 "아직 미오픈"은 완전히 다른 메시지가 필요하다는 걸 늦게 깨달음

**액션플랜**
- 도메인 예외 설계할 때 "클라이언트가 이 에러 받고 어떤 UX 보여줄까?"를 먼저 생각하자
- 같은 UX면 하나, 다른 UX면 분리. 이 한 가지 질문만 던져도 됨

---

## 배운 점

### Aggregate 경계는 DDD 원칙이면서 동시에 성능 최적화

**배움**
- Aggregate 경계를 ID 참조로 두는 게 이론 + 성능 둘 다 맞음
- 선착순 쿠폰 발급은 TPS 1000을 노리는데, `@ManyToOne`으로 묶으면 발급 1건당 `SELECT FROM event`가 따라붙는다 → JPA가 스스로 N+1을 만드는 꼴
- 특히 Kafka consumer에서 CouponIssue를 생성할 때 Event 엔티티가 세션에 없어도 된다는 점이 결정적 — eventId UUID만 있으면 됨

**의미**
- "이론적으로 옳은 것"이 "성능상 옳은 것"과 겹칠 때가 있다
- DDD는 관념이 아니라 **트레이드오프가 검증된 실용 원칙**이라는 걸 코드로 확인함
- Vaughn Vernon이 "Reference other aggregates by identity only"를 왜 그렇게 강조하는지 몸으로 이해됨
- 앞으로 새 엔티티 만들 때 먼저 던질 질문: "이 도메인의 불변식은 뭔가? Entity가 스스로 지킬 수 있나?"

### Rich Domain Model을 만들면 Service가 진짜로 얇아진다

**배움**
- `validateDateRange()` 같은 Service 메서드가 통째로 사라지고 DateRange VO가 그 책임을 가져감
- Service는 repository 호출 + 응답 변환만 남음 — 5~10줄짜리 메서드로 줄어듦
- "Service 최소화, 도메인 최대화"가 말로만이 아니라 실제로 일어나는 현상

**의미**
- Entity/VO에 책임을 제대로 옮기면 Service 테스트가 훨씬 단순해짐
- 앞으로 Service가 50줄 넘어가면 "이 로직 중 Entity로 옮길 수 있는 건 없나?"를 먼저 고민하자

---

## 핵심 내용

### 키워드
- `Rich Domain Model`, `Anemic Domain Model`, `Value Object`, `@Embeddable`, `Aggregate Boundary`, `ID Reference`, `@ManyToOne 지양`, `Vaughn Vernon IDDD`

### 요약
- **Rich Domain Model**: 도메인 로직(상태 전이, 불변식 검증, 재고 차감)을 Entity/Enum 내부에 둔다. Service는 repository 호출 + 유스케이스 orchestration만.
- **Value Object**: 쌍으로 다니는 필드(`startedAt`/`endedAt`)는 `@Embeddable`로 추출. 불변식을 VO `init`에 고정.
- **Aggregate 경계**: 다른 Aggregate Root는 ID(UUID)로만 참조. `@ManyToOne` 지양. 트랜잭션 경계 분리 + N+1 방지 + 분리 가능성 확보.

### 코드/명령어
```kotlin
// 1) Rich Domain Model
class Event(...) : BaseTimeEntity() {
    fun issue() {
        if (!eventStatus.isIssuable)
            throw BusinessException(ErrorCode.EVENT_NOT_OPEN, "status=$eventStatus")
        if (remainingQuantity <= 0)
            throw BusinessException(ErrorCode.EVENT_OUT_OF_STOCK, ...)
        issuedQuantity++
    }
    fun open() { eventStatus = eventStatus.transitionTo(EventStatus.OPEN) }
}

// 2) Value Object
@Embeddable
class DateRange(startedAt: Instant, endedAt: Instant) {
    @Column(name = "started_at") var startedAt: Instant = startedAt
        protected set
    @Column(name = "ended_at") var endedAt: Instant = endedAt
        protected set
    init {
        if (!startedAt.isBefore(endedAt))
            throw BusinessException(ErrorCode.INVALID_DATE_RANGE, ...)
    }
}

@Entity
class Event(..., period: DateRange) : BaseTimeEntity() {
    @Embedded
    var period: DateRange = period
        protected set
}

// 3) Aggregate 경계 (ID 참조)
@Entity
class CouponIssue(
    eventId: UUID,   // ← @ManyToOne Event 아님!
    userId: UUID,
) : BaseCreatedTimeEntity() { ... }
```

### 참고 자료
- Vaughn Vernon, *Implementing Domain-Driven Design* (Red Book)
- Martin Fowler, "Anemic Domain Model": https://martinfowler.com/bliki/AnemicDomainModel.html
