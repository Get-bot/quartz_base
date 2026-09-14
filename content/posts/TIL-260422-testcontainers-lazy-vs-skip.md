---
title: "[TIL-260422] 테스트 환경에서 Skip 대신 Lazy를 선택한 이유"
date: 2026-04-22
tags: ["Kotlin", "Testcontainers", "Spring Boot", "Testing", "Docker", "JVM"]
categories: ["TIL"]
description: "False Positive가 만드는 환경 파편화를 막기 위해 Conditional Skip 대신 Strict Parity + by lazy를 선택한 과정. Kotlin object의 클래스 로딩 시점 함정까지"
---

## 잘한 점

### Kotlin object의 클래스 로딩 타이밍을 짚어 근본 원인 찾기

**상황**
- Unit/Slice 테스트에서도 Docker 컨테이너가 부팅되는 문제 발생
- 단순 "느림"이 아니라 무언가 구조적 문제가 있다고 감지

**액션**
- `object SharedTestContainers`가 싱글톤이라 **클래스 로더가 처음 로드하는 순간 init block이 자동 실행**된다는 걸 확인
- 내부 `val postgres = PostgreSQLContainer(...).apply { start() }`가 실제 필요 시점보다 훨씬 앞당겨 실행되고 있었음
- `by lazy`로 감싸서 최초 접근 시점에만 `start()`가 발동하도록 변경

**칭찬**
- 테스트가 느린 증상을 "어쩔 수 없음"으로 넘기지 않고 **아키텍처 수준의 초기화 시점 문제**로 파고든 점
- 단순 최적화가 아니라 설계 결함 수정으로 끌고 간 흐름

### Strict Parity + Lazy의 하이브리드 선택

**상황**
- "Docker를 강제할 것인가, 없으면 skip할 것인가" 의사결정 필요

**액션**
- 조건부 skip(`@ConditionalOnProperty` + DockerClientFactory ping) 폐기
- 모든 환경에서 Docker 강제(Strict Enforcement, Fail-Fast) + `by lazy`로 필요한 시점까지 지연
- Local↔CI 완벽 일치 + 컨테이너 실패 시 즉시 예외 + Unit/Slice는 컨테이너 미부팅으로 빠름

**칭찬**
- "빼야 할 것(silent skip)"과 "유지해야 할 것(Unit/Slice 성능)"을 분리해서 둘 다 잡은 판단
- False Positive라는 위험을 명확히 언어화하고 문서에 Risk로 박아둔 점

---

## 개선점

### 초기 문서의 "graceful skip" 용어가 모호했음

**문제**
- 초안 계획에서 Docker-less 환경을 "graceful하게 skip"이라고 표현했는데, 실제로는 "조건부로 테스트를 건너뛴다"는 의미였음
- 이 모호함 때문에 논의 초반이 헤맸다

**원인**
- Skip(테스트 건너뛰기)과 Lazy(초기화 지연)의 개념을 구분하지 않고 같이 쓴 것

**액션플랜**
- 최종 문서에서 "Skip은 테스트 건너뛰기, Lazy는 초기화 지연"으로 재정의
- "Conditional Skip은 False Positive 위험이 있어 도입 안 한다"를 명시적으로 기재

### object 클래스 로딩 시점 문제를 늦게 발견

**문제**
- 처음엔 `by lazy`만 붙이면 된다고 생각
- 뒤늦게 "object 자체가 클래스 로딩 시점에 init된다"는 걸 깨달음

**원인**
- Kotlin 싱글톤 패턴과 JVM 클래스 로더 동작을 충분히 고려하지 않고 속성(by lazy)만 먼저 생각함

**액션플랜**
- plan.md §3.2 Phase 1에 "object 클래스 로딩 = init block 실행" 주석 추가
- 후속 개발자가 같은 실수 반복하지 않도록 명시

---

## 배운 점

### Skip과 Lazy는 완전히 다른 전략이다

**배움**
- Skip = "테스트 자체를 조건부로 건너뛴다"
- Lazy = "필요한 시점까지 리소스 초기화를 미룬다"
- 두 개념이 섞이면 안 된다. 효과도, 위험도 전혀 다르다.

| 전략 | 초기화 시점 | 테스트 결과 | False Positive | 성능 | 환경 파편화 |
|------|-----------|-----------|----------------|------|-----------|
| Conditional Skip | 조건 체크 시 | 조건 불충족 → skip(초록불) | **매우 높음** | 빠름 | 환경별 상이 |
| Lazy + 강제 | Bean resolve 시 | 컨테이너 불가 → 즉시 실패 | **없음** | 필요 시만 느림 | 동일 |

**의미**
- "조용히 지나가는 것"이 가장 위험하다. 거짓 성공은 배포 후 장애로 돌아온다
- Fail-Fast가 불편해 보여도 그게 정직한 피드백이고 신뢰성을 준다
- PDCA의 조기 피드백 원칙을 테스트 전략에 그대로 적용할 수 있다

### Kotlin object의 JVM 초기화 타이밍

**배움**
- Kotlin `object`는 Java `static final` 싱글톤과 동등. 클래스 로더가 클래스를 처음 로드하는 순간 `<clinit>` (object init block)이 실행된다
- 필드에 `by lazy`를 붙여도 **object 자체는 여전히 그 시점에 초기화**됨 (lazy는 필드 접근 시점을 지연할 뿐)

**의미**
- "싱글톤은 안전하다"는 막연한 믿음 말고, **언제 초기화되는지** 실제로 확인하자
- Unit/Slice 테스트에서 실수로 `SharedTestContainers`를 import하면 `by lazy`가 없을 땐 즉시 컨테이너가 부팅되는 덫이 있다

---

## 핵심 내용

### 키워드
- `Kotlin object`, `Class Loading`, `by lazy`, `Testcontainers`, `Strict Parity`, `Fail-Fast`, `False Positive`

### 요약
- `object SharedTestContainers`의 필드를 `by lazy`로 감싸서 최초 접근 시점에만 컨테이너 start
- `TestcontainersConfiguration`은 조건부 가드 없이 항상 등록 → IT는 반드시 Docker를 거친다 (Fail-Fast)
- Unit/Slice는 해당 Configuration을 import 안 하므로 `by lazy` 미발동 → 컨테이너 비부팅 (빠름)
- 결과: Local↔CI 완벽 일치 + 빠른 단위 테스트 + silent skip 불가능

### 코드/명령어

**Before — object 로딩 시점에 즉시 start()**
```kotlin
object SharedTestContainers {
    val postgres: PostgreSQLContainer =
        PostgreSQLContainer(DockerImageName.parse("postgres:18-alpine"))
            .apply { start() }   // ❌ 클래스 로딩 시점에 즉시 실행

    val valkey: GenericContainer<*> =
        GenericContainer(DockerImageName.parse("valkey/valkey:8.0-alpine"))
            .withExposedPorts(6379)
            .apply { start() }   // ❌ Unit/Slice 테스트도 컨테이너 부팅
}
```

**After — by lazy로 지연**
```kotlin
object SharedTestContainers {
    val postgres: PostgreSQLContainer by lazy {
        PostgreSQLContainer(DockerImageName.parse("postgres:18-alpine"))
            .apply { start() }   // ✅ 최초 접근 시점에만
    }

    val valkey: GenericContainer<*> by lazy {
        GenericContainer(DockerImageName.parse("valkey/valkey:8.0-alpine"))
            .withExposedPorts(6379)
            .apply { start() }
    }
}
```

**Strict Enforcement — 조건부 가드 없이 항상 등록**
```kotlin
@Configuration
class TestcontainersConfiguration {
    // @ConditionalOnProperty 같은 조건부 가드 없음!

    @Bean
    @ServiceConnection
    fun postgresContainer(): PostgreSQLContainer = SharedTestContainers.postgres
    // 이 메서드 호출 시점 = by lazy 최초 발동 = Docker 없으면 즉시 예외 (Fail-Fast)

    @Bean
    @ServiceConnection
    fun valkeyContainer(): GenericContainer<*> = SharedTestContainers.valkey
}
```

**실행 결과**
```bash
# IT (Docker 있음) → 성공
./gradlew test --tests "*IT"

# IT (Docker 없음) → 즉시 실패 (silent skip 없음)
# "start() failed: Cannot find Docker daemon" 같은 직관적 에러

# Unit/Slice (Docker 유무 무관) → 빠르게 통과
# TestcontainersConfiguration을 import 안 하므로 by lazy 미발동
./gradlew test --tests "*ControllerTest"
```

### 참고 자료
- `docs/archive/2026-04/auth-rbac-pr-fixes/plan.md` §3.2 Phase 1 — Testcontainers Strict Enforcement + Lazy Initialization 결정 근거
- `src/test/kotlin/com/bubaum/buws/SharedTestContainers.kt` — 실제 적용 코드
- Kotlin Delegated Properties (`by lazy`): https://kotlinlang.org/docs/delegated-properties.html#lazy
