---
title: "[TIL-260414] springmockk 5.0.1 발견과 Gap Analysis 기반 테스트 완성"
date: 2026-04-14
tags: ["springmockk", "MockK", "Gap Analysis", "Spring Boot 4", "Kotest", "Testcontainers"]
categories: ["TIL"]
description: "springmockk 5.0.1 발견으로 전 계층 MockK DSL 통일. Gap Analysis로 누락된 EventTest를 발견하고 Match Rate 88% → 95% 달성."
---

## 잘한 점

### springmockk 5.0.1 발견으로 전 계층 MockK 통일

**상황**
- Plan v0.4에서 springmockk 4.0.2는 Spring Boot 3.0 기반이라 "도입 불가"로 판단했다
- L3 Controller Slice에서 `@MockitoBean` + Mockito DSL을 쓰고 있었는데, L2의 MockK DSL과 혼재되는 게 계속 거슬렸다
- PR 리뷰에서 "MockK로 통일하라"는 피드백이 들어옴

**액션**
- GitHub에서 springmockk 레포를 직접 확인했더니 5.0.1이 나와 있었다 — "Spring Framework 7 compatible"
- `testImplementation("com.ninja-squad:springmockk:5.0.1")` 추가 후 `./gradlew build -x test` 통과 확인
- EventControllerTest를 `@MockitoBean` → `@MockkBean`, `given().willReturn()` → `every {} returns`, `argumentCaptor` → `slot`으로 전환
- Validation 테스트 3개를 `withData`로 묶음

**칭찬**
- 리뷰어가 "불가능"이라고 했던 걸 그냥 넘기지 않고 직접 확인한 것
- 확인하는 데 5분도 안 걸렸는데, 그 5분이 전체 테스트 코드의 일관성을 바꿨다

---

## 개선점

### 초기 리서치 부족으로 Plan 방향 전환이 5회

**문제**
- Plan이 v0.1 → v0.5까지 5번 바뀌었다
- springmockk 5.0.1이 있는지 처음부터 확인했으면 v0.2에서 바로 방향을 잡았을 수 있었다

**원인**
- Maven Central에서 버전 확인만 하고, GitHub Releases를 확인 안 함
- "4.0.2가 최신이니까 안 되겠지"라는 가정으로 문서를 작성해버림

**액션플랜**
- 테스트 프레임워크/핵심 라이브러리 결정 전에는 GitHub Releases + README를 반드시 확인
- "무언가 불가능하다"고 문서화할 때는 그 근거가 언제 시점의 정보인지 명시하자

---

## 배운 점

### Gap Analysis가 누락을 잡아준다

**배움**
- Design 대비 구현을 비교했더니 Match Rate 88%가 나왔다
- 빠진 게 EventTest.kt — Event entity의 `issue()`, `open()`, `close()` 도메인 로직 테스트
- 이게 L1에서 가장 중요한 테스트인데 막상 작성하다 보니 빠뜨리고 있었다

**의미**
- "다 한 것 같은데?"라는 느낌은 믿을 수 없다. 설계 문서와 대조해야 누락이 보인다
- Gap Analysis → EventTest 구현 → 95%로 올라갔다. 이 흐름이 PDCA Check의 핵심

### Spring Boot 4 테스트 환경 트러블슈팅 3건

**배움**
- `@DataJpaTest`에서 custom `@Repository`는 `@Import` 필수 — JpaRepository 인터페이스만 자동 스캔
- `beforeSpec`에서 `entityManager.persist()` 하면 `TransactionRequiredException` — `@Transactional`이 각 테스트에만 적용되기 때문. `beforeTest`로 바꿔야 한다
- `@AutoConfigureMockMvc` 패키지가 `boot.test.autoconfigure.web.servlet` → `boot.webmvc.test.autoconfigure`로 변경됨 (SB4 모듈 재구성)

**의미**
- Spring Boot 4 마이그레이션은 패키지 경로가 많이 바뀌었다. 컴파일 에러 나면 jar 내부를 직접 확인하는 습관을 들이자

---

## 핵심 내용

### 키워드
- `springmockk 5.0.1`, `@MockkBean`, `Gap Analysis`, `@DataJpaTest`, `beforeSpec vs beforeTest`, `@AutoConfigureMockMvc`

### 요약
- springmockk 5.0.1은 Spring Framework 7의 BeanOverride API를 지원하여 `@MockkBean`을 제공한다. 4.0.2는 제거된 `@MockBean` API에 의존해서 SB4에서 사용 불가.
- Kotest + `@DataJpaTest` 조합에서 `beforeSpec`은 트랜잭션 밖에서 실행된다. `beforeTest`를 쓰면 각 테스트의 `@Transactional` 내부에서 데이터가 삽입되고 롤백된다.
- `@DataJpaTest`는 JPA 관련 빈(`@Entity`, `JpaRepository` 인터페이스)만 자동 스캔. `@Repository` 어노테이션이 붙은 커스텀 클래스(QueryDSL)는 `@Import` 필수.

### 코드/명령어
```kotlin
// springmockk 5.0.1 — @MockkBean으로 전 계층 MockK 통일
@WebMvcTest(EventController::class)
class EventControllerTest(
    private val mockMvc: MockMvc,
    @MockkBean private val eventService: EventService,
) : FunSpec({
    test("POST 정상") {
        every { eventService.create(any()) } returns response
    }
})
```

```kotlin
// @DataJpaTest + custom @Repository — @Import 필수
@DataJpaTest
@Import(JpaConfig::class, EventQueryRepository::class)
class EventQueryRepositoryTest(
    private val repo: EventQueryRepository,
    private val em: EntityManager,
) : FunSpec({
    beforeTest {  // beforeSpec 아님!
        events.forEach { em.persist(it) }
        em.flush()
    }
})
```

### 참고 자료
- springmockk GitHub: https://github.com/Ninja-Squad/springmockk
- Spring Boot 4 Migration Guide: https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide
