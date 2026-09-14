---
title: "[TIL-260411] PR 리뷰로 정리한 Spring Boot + Kotlin 관용 패턴"
date: 2026-04-11
tags: ["Spring Boot", "Kotlin", "Bean Validation", "Spring Data", "Testcontainers", "PR Review"]
categories: ["TIL"]
description: "PR #1 리뷰 반영 과정에서 배운 3가지 — Bean Validation @NotBlank null 처리, Spring Data one-indexed-parameters 비대칭성, Testcontainers @Container + @JvmField 수명관리"
---

## 잘한 점

### AI가 내놓은 잘못된 기술 주장을 스펙 기반으로 잡아낸 것

**상황**
- copilot 리뷰어가 `EventCreateRequest.title`의 nullable + `@NotBlank` 조합을 "NPE 위험"이라고 지적
- Claude한테 PR 리뷰 타당성 검증을 요청했는데, Claude가 초기 답변에서 리뷰어 주장을 그대로 믿고 "실제 버그"라고 단정적으로 답함
- 심지어 "반영해야 할 실제 이슈"에 올려놓기까지 했음

**액션**
- Claude의 단정적 답변을 수용하지 않고 "근데 blank가 null empty 다 막는 거 아냐?"라고 짧게 반박
- Jakarta Bean Validation 스펙에서 `@NotBlank`가 실제로 null을 거부한다는 사실을 Claude가 재확인하도록 유도
- 결과적으로 "실제 버그"로 단정됐던 지적이 "스타일 개선 제안"으로 재평가됨

**칭찬**
- AI가 단정적인 어조로 말할 때도 맹신하지 않고 자기 감각을 먼저 의심해본 것
- "근데"로 시작하는 짧은 한마디가 오답이 PR 회신에 그대로 들어가는 걸 막았다는 점
- 평소 자주 쓰는 어노테이션의 실제 동작에 대해 외부 권위(리뷰어, AI)보다 자기 기억을 먼저 검증 기준으로 삼은 판단

### PR #1 리뷰 3건을 단계별 커밋으로 반영

**상황**
- copilot 리뷰어와 Claude의 리뷰 피드백 중 3건을 수용 결정
- (1) `EventQuery` 레이어 역전 (repository가 service를 import) (2) `EventCreateRequest.title` nullable 정리 (3) `IntegrationTestBase` 수명관리 자동화
- 각 항목 성격이 달라서 한 커밋에 몰아넣을 수 없었음

**액션**
- 3개 커밋으로 의미 단위 분리:
  - `fca5ba5` — `EventQuery`를 `service` → `repository` 패키지로 이동
  - `41b5ab6` — `title: String?` → `String`, `toEntity()`의 `title!!` 제거
  - `8378aac` — `IntegrationTestBase`를 `@Container` + `@JvmField`로 전환
- 각 커밋 후 `./gradlew compileKotlin` / `compileTestKotlin`로 회귀 확인을 요구

**칭찬**
- "한 번에 싹" 몰아서 커밋하지 않고 의미 단위로 쪼갠 판단 — PR 리뷰 스레드와 1:1 매핑
- `refactor:` / `test:` 타입 prefix로 커밋 성격을 명확히 한 점
- Claude가 실행하는 동안 IDE 자동 import가 `SseEmitter.event`를 잘못 붙인 것까지 중간에 체크한 점

### Spring + Kotlin DTO 관용 패턴 유지 결정

**상황**
- Claude가 `EventCreateRequest`의 4개 필드를 **전부 non-null**로 싹 바꾸려고 시도함
- 그 방향이 Spring + Kotlin 실무에서 쓰던 관용 패턴과 어긋난다고 느낌

**액션**
- "타이틀 notblank 제외하고는 nullable 해주고 to entity에서 !! 해주는게 코틀린에 맞지 않아?"라고 직접 방향 제시
- Claude의 과한 리팩터링을 중단시키고 `title` 하나만 non-null로 정리, 나머지는 기존 nullable + `@NotNull` + `!!` in `toEntity()` 유지

**칭찬**
- AI가 제안한 방향을 그대로 따르지 않고 "내가 쓰던 패턴이 왜 더 나은지"를 직접 설명한 것
- 결과적으로 Jackson 에러 vs Bean Validation 에러 응답 일관성이라는 더 깊은 논의까지 이끌어낸 판단

---

## 개선점

### AI 답변의 단정적 어조에 휘말릴 뻔한 순간

**문제**
- Claude가 첫 답변에서 `@NotBlank` NPE 주장을 그대로 믿고 "실제 버그"로 단정적으로 정리함
- 단정적 어조 + 표 형식 + "실제 버그로 남아있는 2건" 같은 구조화된 답변에 잠시 설득될 뻔함
- 내가 "근데"로 반박하지 않았으면 오답이 PR 회신에 그대로 들어갔을 것

**원인**
- AI가 "단정적 어조 + 출처 있어 보이는 설명" 조합으로 답할 때 그대로 믿게 되는 심리
- 평소 Bean Validation을 자주 쓰면서도 annotation별 null 처리 semantics를 명시적으로 정리해둔 적은 없음 → 처음엔 "내가 맞나?" 하고 반박 한 템포 늦어짐

**액션플랜**
- AI 답변 중 "X는 Y 때문에 Z가 된다" 같은 인과 주장은 공식 스펙 링크로 1회 확인하는 습관
- 자주 쓰는 기술의 semantic을 한 줄 메모로라도 정리해두기 — Bean Validation annotation별 null 처리 표 같은 것
- AI에게 기술 판단을 시킬 때 "이게 맞는지 스펙 확인해줘"를 루틴으로 덧붙이기

---

## 배운 점

### Spring Data `one-indexed-parameters`는 요청에만 적용된다

**배움**
- `spring.data.web.pageable.one-indexed-parameters=true`는 **request parsing에만** 적용 (입력 `page=1` → 내부 `pageNumber=0`)
- `Page.getNumber()`는 설정과 무관하게 **항상 0-based** 반환
- 응답 페이지 번호를 1-based로 맞추려면 DTO 매핑 단계에서 `page.number + 1` 보정을 직접 해야 함
- 비대칭은 Spring Data의 의도 — 내부 도메인 모델(`Pageable`/`Page`)을 항상 0-based로 유지해 JPA/QueryDSL 하위 레이어와 일관성 확보, 1-based는 HTTP 경계 편의 변환으로만 취급
- `PagedResourcesAssembler`(HATEOAS 경로)는 자동 보정하지만, 순수 `Page` JSON 직렬화에는 보정 로직이 없음

**의미**
- `PageResponse.from()`에서 `page.number + 1`이 설정과 충돌하는 게 아니라 **설정의 비대칭성을 완성**해주는 코드라는 걸 처음 알게 됨
- 설정을 켤 때는 "입력 / 내부 / 출력" 3개 지점에서 각각 어떻게 바뀌는지 명시적으로 확인하자
- "이름만 보면 전체가 1-based가 될 것 같다"는 인상과 실제 동작 범위(request parsing만) 사이의 gap을 의식

### Kotlin DTO null 처리 — 두 패턴의 트레이드오프

**배움**
- **전부 non-null 패턴**: `!!`가 없어 깔끔해 보이지만 null JSON 요청이 Jackson의 `MissingKotlinParameterException` → `HttpMessageNotReadableException`으로 빠짐. 이는 Bean Validation의 `MethodArgumentNotValidException`과 **에러 응답 포맷이 다름**
- **nullable + `@NotNull` 패턴**: 모든 null 체크가 BV로 수렴 → 필드별 커스텀 메시지와 일관된 400 응답 구조
- `@NotBlank`는 null 거부까지 포함하므로, String 필드는 non-null로 두고 `@NotBlank`와 짝짓는 게 자연스러움 — String만 예외적으로 non-null이 맞는 이유

**의미**
- DTO는 "검증 전 raw input 모양"을 표현하는 레이어라는 관점에서 nullable + `!!` in `toEntity()`는 실제로 의미 있는 관용 패턴
- `!!`는 런타임 위험이 아니라 "Validation 통과 후에만 도달함"을 코드로 문서화하는 효과
- DTO 필드 타입 선택 기준: **"null 요청이 어느 Exception으로 떨어지는가"**

### Kotlin companion object의 static 노출 3가지

**배움**
- `@JvmStatic fun/val` → **getter/메서드**를 outer class static으로 노출. 필드 자체는 여전히 Companion 내부에 있음
- `@JvmField val` → **필드 자체**를 outer class의 진짜 static field로 노출. getter/setter 없음 (그래서 `val`에만)
- `const val`(primitive/String만) → 컴파일 시점 상수, outer class static final field
- **field reflection을 요구하는 프레임워크**(JUnit5 Testcontainers `@Container`, Mockito `@InjectMocks` 등)는 `@JvmField`가 필요
- Testcontainers JUnit5 확장에서 클래스 레벨 `@Container` static field는 모든 테스트 전 start, 모든 테스트 후 stop을 자동 수행

**의미**
- 원래 쓰던 `@JvmStatic val + init { .start() }` 패턴은 **동작은 하지만** stop을 보장하지 못한다는 한계가 있음 → 리소스 누수 위험
- Kotlin ↔ Java interop에서 "static처럼 보인다 ≠ 진짜 static field"라는 구분을 의식
- 프레임워크가 어떤 reflection을 쓰는지(메서드 탐색 vs 필드 탐색)에 따라 interop annotation 선택이 달라짐

---

## 핵심 내용

### 키워드
- **Bean Validation**: `@NotBlank`, `@NotNull`, `@Size`, `MissingKotlinParameterException`, `MethodArgumentNotValidException`, `HttpMessageNotReadableException`
- **Spring Data Pagination**: `spring.data.web.pageable.one-indexed-parameters`, `PageableHandlerMethodArgumentResolver`, `Page.getNumber`, `PagedResourcesAssembler`
- **Kotlin + Testcontainers**: `@Testcontainers`, `@Container`, `@JvmField`, `@JvmStatic`, `companion object`

### 요약

**Bean Validation null 처리 (Jakarta 3.0 스펙)**
- 거부: `@NotNull`, `@NotEmpty`, `@NotBlank`
- 허용: `@Size`, `@Pattern`, `@Min`, `@Max` — null이면 검사 자체를 skip
- `@NotBlank` = null 거부 + 빈 문자열 거부 + 공백만 있는 문자열 거부 (String 전용)

**Spring Data Pageable 동작 흐름**
```
GET /api/v1/events?page=1
  ↓ PageableHandlerMethodArgumentResolver (one-indexed-parameters=true)
Pageable(pageNumber=0)   # 내부는 항상 0-based
  ↓ Repository
Page(number=0)            # getNumber() 여전히 0-based
  ↓ PageResponse.from()
{ "page": 1 }             # DTO에서 +1 보정
```

**Testcontainers 수명관리**
- 클래스 레벨 `@Container` static field → 테스트 클래스당 1회 start/stop
- 인스턴스 레벨 `@Container` non-static field → 각 테스트마다 start/stop
- Kotlin companion object의 static field는 `@JvmField val`로만 진짜 static field가 됨 (`@JvmStatic val`은 getter만 static)

### 코드/명령어

**DTO null 처리 패턴**
```kotlin
data class EventCreateRequest(
    @field:NotBlank @field:Size(max = 200)
    val title: String,                    // String은 non-null + @NotBlank
    @field:NotNull @field:Min(1)
    val totalQuantity: Int?,              // 나머지는 nullable + @NotNull
    @field:NotNull
    val startedAt: Instant?,
    @field:NotNull
    val endedAt: Instant?,
) {
    fun toEntity() = Event(
        title = title,                    // @NotBlank로 보장
        totalQuantity = totalQuantity!!,  // @NotNull로 보장
        period = DateRange(startedAt!!, endedAt!!),
    )
}
```

**Pageable 1-indexed 보정**
```yaml
spring:
  data:
    web:
      pageable:
        one-indexed-parameters: true
        max-page-size: 100
```

```kotlin
data class PageResponse<T>(
    val content: List<T>,
    val page: Int,
    val size: Int,
    val totalElements: Long,
    val totalPages: Int,
) {
    companion object {
        fun <T : Any> from(page: Page<T>) = PageResponse(
            content = page.content,
            page = page.number + 1,   // ← 응답 대칭을 완성
            size = page.size,
            totalElements = page.totalElements,
            totalPages = page.totalPages,
        )
    }
}
```

**Testcontainers 전환 before/after**
```kotlin
// Before — 수동 start, stop 누락 (리소스 누수 위험)
companion object {
    @JvmStatic
    val postgres = PostgreSQLContainer(DockerImageName.parse("postgres:18-alpine"))

    init {
        postgres.start()
        // stop 없음 — JUnit5 종료 시 정리 보장 안 됨
    }
}

// After — 확장이 lifecycle 자동 관리
companion object {
    @Container
    @JvmField
    val postgres: PostgreSQLContainer<*> =
        PostgreSQLContainer(DockerImageName.parse("postgres:18-alpine"))

    @Container
    @JvmField
    val redis: GenericContainer<*> =
        GenericContainer(DockerImageName.parse("redis:7-alpine"))
            .withExposedPorts(6379)

    @Container
    @JvmField
    val kafka: KafkaContainer =
        KafkaContainer(DockerImageName.parse("apache/kafka-native:latest"))
}
```

### 참고 자료
- Jakarta Bean Validation 3.0 `@NotBlank`: https://jakarta.ee/specifications/bean-validation/3.0/apidocs/jakarta/validation/constraints/notblank
- Spring Boot Pageable properties: https://docs.spring.io/spring-boot/appendix/application-properties/index.html
- Testcontainers JUnit 5: https://java.testcontainers.org/test_framework_integration/junit_5/
- Kotlin Java interop — @JvmField: https://kotlinlang.org/docs/java-to-kotlin-interop.html#instance-fields
