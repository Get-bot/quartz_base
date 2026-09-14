---
title: "[TIL-260414] Kotest 6.1.0 전면 도입 — DescribeSpec + withData로 도메인 테스트 작성"
date: 2026-04-14
tags: ["Kotest", "DescribeSpec", "withData", "Power Assert", "Spring Boot", "Kotlin"]
categories: ["TIL"]
description: "Kotest 5.9.1에서 6.1.0으로 업그레이드하고, ProjectConfig·SingleInstance·Sequential 전역 설정 구성. L1 Domain Unit 테스트 5종을 DescribeSpec + withData로 작성."
---

## 잘한 점

### Kotest 6.1.0 Specs 전면 도입 + L1 테스트 5종 작성

**상황**
- spring-event-lab 프로젝트에 event-crud 코드가 DDD 리팩토링까지 끝났는데, 검증하는 테스트가 하나도 없었다
- v0.3 Plan에서는 Kotest 5.9.1 assertions만 쓰고 runner는 JUnit 5로 가려고 했는데, Kotest 6.1.0이 안정판으로 나와서 방향을 바꿨다
- Kotest 6는 `@AutoScan` 제거, `ProjectConfig` 필수 위치 변경, `specExecutionMode` 도입 등 꽤 큰 변화가 있어서 리서치가 좀 필요했다

**액션**
- Kotest 5.9.1 → 6.1.0 업그레이드하고, `kotest-extensions-spring`, `kotest-framework-datatest` 신규 추가
- `io.kotest.provided.ProjectConfig`에 SpringExtension + SingleInstance + Sequential 전역 설정 구성
- L1 Domain Unit 테스트 5종 작성: `DateRangeTest`, `EventStatusTest`, `EventQueryOrdersTest`, `EventCreateRequestTest`, `EventResponseTest`
- `EventFixture` 테스트 픽스처로 중복 제거
- Power Assert(`-Xpower-assert`) 컴파일러 옵션 추가

**칭찬**
- Kotest 6 마이그레이션 가이드 읽고 ProjectConfig부터 테스트까지 한 세션에 다 끝낸 것
- `withData`로 데이터 드리븐 테스트 구성한 건 좀 잘한 듯 — 경계값 케이스를 빠짐없이 커버하면서도 코드가 깔끔하다

---

## 개선점

### Plan 문서 방향 전환이 잦았다

**문제**
- Plan 문서가 v0.1(JUnit 5 only) → v0.2(MockK 추가) → v0.3(Kotest assertions) → v0.4(Kotest 6 Specs 전면 도입)로 4번 바뀜
- 처음부터 Kotest 6 출시 상태를 확인했으면 v0.1에서 바로 방향을 잡을 수 있었다

**원인**
- 초기에 "보수적으로 가자"는 판단이 너무 강했다. Kotest 6이 안정판인지 확인도 안 하고 5.9.1로 시작함
- 매 단계마다 "이것도 되네? 그럼 더 가보자"식으로 점진적으로 확장하다 보니 불필요한 반복이 생김

**액션플랜**
- 테스트 프레임워크 같은 핵심 도구 결정은 초기에 최신 버전 안정성부터 확인하자
- "보수적 접근"과 "리서치 부족"은 다르다 — 보수적이더라도 옵션은 다 파악하고 선택해야 한다

---

## 배운 점

### Kotest 6 ProjectConfig의 필수 위치 규칙

**배움**
- Kotest 5.x에서는 `@AutoScan`으로 아무 패키지에나 config를 두면 됐는데, 6.x에서는 반드시 `io.kotest.provided.ProjectConfig`에 위치해야 한다
- 이유가 있었다 — 클래스패스 전체 스캐닝을 제거해서 테스트 시작 속도가 빨라졌다

**의미**
- 프레임워크가 "관례(convention)"를 강제하는 데는 성능이나 예측 가능성 같은 이유가 있다. 그냥 외우지 말고 왜 바뀌었는지까지 파악하면 비슷한 결정을 할 때 판단 기준이 된다

### SingleInstance + Sequential 조합의 이유

**배움**
- `SingleInstance` 격리 모드(Spec 인스턴스 1개 공유)에서 `Concurrent` 실행하면 race condition이 터진다
- 여러 테스트가 같은 인스턴스의 mock이나 변수에 동시 접근하기 때문
- `beforeTest { clearAllMocks() }`로 mock 상태를 격리하는 게 이 조합의 핵심 패턴

**의미**
- 격리 모드(isolation)와 실행 모드(execution)는 독립적인 축이 아니라 서로 제약을 건다. 조합 가능하다고 다 안전한 건 아니다

---

## 핵심 내용

### 키워드
- `Kotest 6.1.0`, `DescribeSpec`, `FunSpec`, `withData`, `ProjectConfig`, `SpringExtension`, `SingleInstance`, `Power Assert`

### 요약
- Kotest 6.1.0 주요 변경: `@AutoScan` 제거 → `io.kotest.provided.ProjectConfig` 필수 위치. `parallelism` 제거 → `specExecutionMode`/`testExecutionMode`로 대체. `PackageConfig` 도입으로 패키지별 타임아웃/격리 모드 세분화 가능.
- `SingleInstance` + `Sequential` 조합이 Spring 컨텍스트 캐싱과 가장 잘 맞다. mock 상태 격리는 `beforeTest { clearAllMocks() }`로.
- `withData`는 경계값/전이 규칙 테스트에 적합. 각 데이터 포인트가 독립 테스트로 리포트되어 실패 원인을 바로 파악 가능.

### 코드/명령어
```kotlin
// io.kotest.provided.ProjectConfig — 반드시 이 패키지 경로
package io.kotest.provided

object ProjectConfig : AbstractProjectConfig() {
    override val extensions = listOf(SpringExtension())
    override val isolationMode = IsolationMode.SingleInstance
    override val specExecutionMode = SpecExecutionMode.Sequential
}
```

```kotlin
// withData 데이터 드리븐 테스트
describe("canTransitionTo") {
    withData(
        Triple(READY, OPEN, true),
        Triple(READY, CLOSED, false),
        Triple(OPEN, CLOSED, true),
    ) { (from, to, expected) ->
        from.canTransitionTo(to) shouldBe expected
    }
}
```

```kotlin
// build.gradle.kts — Power Assert 활성화
kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xpower-assert")
    }
}
```

### 참고 자료
- Kotest 6 Migration Guide: https://kotest.io/docs/next/framework/migration/migration-6.0.html
