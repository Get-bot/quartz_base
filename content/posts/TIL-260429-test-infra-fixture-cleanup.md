---
title: "[TIL-260429] 테스트 인프라 정비 — Fixture 공통화, DbCleanupListener 폐기, Entity 테스트 리팩토링"
date: 2026-04-29
tags: ["Kotest", "Testcontainers", "테스트", "Fixture", "Spring Boot"]
categories: ["TIL"]
description: "Fixture를 도메인 패키지에서 전역 support/로 끌어올림, 96줄 DbCleanupListener 삭제, Entity 테스트를 withData 테이블 드리븐으로 리팩토링"
---

## 잘한 점

### Fixture를 도메인 패키지 → 전역 `support/` 로 끌어올림

**상황**
- `MasterAccountFixture` / `SubAccountFixture` 가 `withdrawal/account/support/` 에 박혀 있었음
- Bank·Member 등 다른 도메인 테스트에서 비슷한 픽스처를 매번 재구현하던 게 누적
- Fixture는 "도메인 소유"가 아니라 "테스트 자산"이라는 게 늦게 보임

**액션**
- `src/test/kotlin/com/bubaum/buws/support/` 로 두 픽스처를 끌어올림 (rename move 추적 가능하게 git mv)
- 다른 도메인 테스트에서 import 한 줄로 재사용 가능

---

### `DbCleanupListener` (96줄) 폐기 → ProjectConfig + SharedTestContainers로 단순화

**상황**
- 테스트마다 `@Sql` / TRUNCATE 기반 정리 로직이 `DbCleanupListener` 96줄에 들어 있었음
- 그런데 SharedTestContainers의 per-class 재초기화 + JPA 트랜잭션 롤백이랑 책임이 겹쳐서 노이즈만 생김
- 어떤 테스트는 cleanup이 한 번, 어떤 테스트는 두 번 돌고 있었음

**액션**
- `DbCleanupListener` 통째로 삭제
- Kotest `ProjectConfig` 한 곳에서 글로벌 Listener 관리
- `SharedTestContainers` 가 PostgreSQL 18 + Valkey 8 컨테이너 싱글톤으로 떠 있고, 트랜잭션 롤백으로 정리 — 이거 하나로 충분

**칭찬**
- 96줄 "청소 코드"를 진짜 0줄로 줄인 것 — 안 쓰던 코드가 아니라 **잘못된 위치에 있던 코드** 였음

---

### Entity 테스트 3종 리팩토링 (`SubAccountTest`, `MasterAccountTest`, `BankPgCredentialsTest`)

**상황**
- Entity 테스트가 평탄한 `@Test fun` 나열로 짜여 있었음 — 어떤 케이스 묶음인지 한눈에 안 보임
- v1.3 재작성하면서 케이스가 늘어나니까 270줄짜리 SubAccountTest가 부담스러워짐

**액션**
- Kotest `DescribeSpec` + `withData` (테이블 드리븐) 패턴으로 통일
- "불변식 검증", "상태 전이", "한도/사용량 변경" 등 의미 단위로 그룹화
- 실패 시 어떤 row가 깨졌는지 IDE에서 한 번에 보임

---

### `TEST_WRITE_GUIDE.md` 보강

**상황**
- 이번 정비 결과가 가이드에 안 쓰이면 다음 PR에서 또 같은 패턴이 흩어질 것

**액션**
- 4-Layer Test Pyramid (L1 Domain ~ L4 Integration) 명시
- ProjectConfig + SharedTestContainers 위치·책임을 가이드에 박음

---

## 개선점

### 픽스처가 도메인 패키지에 묶여 있던 게 그동안 "보이지 않는 비용"

**문제**
- 똑같은 fixture를 도메인마다 재구현 — 코드 중복은 둘째 치고 도메인 변경 시 픽스처 동기화가 안 됨
- "왜 이 도메인엔 fixture가 있고 저 도메인엔 없지?" 질문이 안 떠올랐던 게 진짜 문제

**원인**
- 처음 한두 개 만들 때 "도메인별로 두는 게 깔끔하다" 라고 무의식적으로 결정
- 두 번째 도메인 들어갔을 때 재배치 결정을 미룸

**액션플랜**
- 새 fixture 만들 때 무조건 `support/` 패키지에서 시작
- 도메인-특수 fixture는 진짜 그 도메인에서만 쓰일 때만 도메인 패키지에 (지금까진 그런 케이스 없음)

---

### `DbCleanupListener` 가 오래 살아 있던 이유

**문제**
- 컨테이너 기반 테스트로 옮기는 동안 안전망으로 남겼다가 그대로 굳어버림
- 동작은 하니까 의심받지 않음 — "동작하는데 왜 지워?"

**원인**
- 인프라 리팩토링 끝나면 마지막에 "안전망 제거" 단계를 따로 안 잡음

**액션플랜**
- 인프라 마이그레이션 PR에 "마지막 단계: 구 안전망 제거" 항목을 미리 박아두기

---

## 배운 점

### 테스트 청소 코드는 "양" 이 아니라 "위치" 가 문제

**배움**
- 96줄짜리 cleanup 리스너를 0줄로 줄인 게 아니라 **책임이 잘못된 위치에 있는 걸 옮긴 것**
- 인프라가 트랜잭션 롤백으로 다 처리하고 있었는데, 어플리케이션 레이어에서 또 청소하던 셈

**의미**
- 코드 줄이는 작업 전에 "이 책임이 누구한테 있어야 하는가?" 부터 묻기

---

### 테이블 드리븐 테스트의 진짜 가치

**배움**
- `withData` 로 짜면 **케이스 추가 비용이 거의 0** — 한 줄 추가
- 실패 시 "어떤 입력이 깨졌는지" 가 가장 먼저 보임
- v1.3 같은 도메인 재작성 후 검증 단계에서 진짜 빛났음

**의미**
- Entity 검증 테스트는 무조건 테이블 드리븐 — 직렬 `@Test` 나열은 그만

---

## 핵심 내용

### 키워드
- `Kotest`, `DescribeSpec`, `withData`, `ProjectConfig`, `SharedTestContainers`, `Testcontainers`, `4-Layer Test Pyramid`

### 요약
- **Fixture 위치**: `src/test/kotlin/com/bubaum/buws/support/` 가 기본. 도메인 패키지엔 진짜 그 도메인 전용일 때만.
- **DB cleanup**: SharedTestContainers + 트랜잭션 롤백으로 충분. 별도 Listener는 책임 중복.
- **Entity 테스트**: `DescribeSpec` + `withData` 테이블 드리븐. 직렬 `@Test` 나열 금지.
- **4-Layer**: L1 Domain (Entity 단위) / L2 Service (MockK) / L3 Slice (`@DataJpaTest`, `@WebMvcTest`) / L4 Integration (`@SpringBootTest` + Testcontainers).

### 코드/명령어
```kotlin
// withData 테이블 드리븐 예시
class SubAccountTest : DescribeSpec({
  describe("tryUse") {
    withData(
      nameFn = { "한도=${it.limit}, 누적=${it.used}, 요청=${it.req} → ${it.expected}" },
      Row(limit = 10000, used = 0,    req = 5000,  expected = Allow),
      Row(limit = 10000, used = 5000, req = 5001,  expected = Reject),
      Row(limit = 10000, used = 10000, req = 1,    expected = Reject),
    ) { row ->
      // ...
    }
  }
})
```

```kotlin
// io/kotest/provided/ProjectConfig.kt — 글로벌 Listener 한 곳
object ProjectConfig : AbstractProjectConfig() {
  override fun extensions() = listOf(SpringExtension)
}
```

### 참고 자료
- `docs/engine/TEST_WRITE_GUIDE.md` (4-Layer Test Pyramid)
- `src/test/kotlin/com/bubaum/buws/SharedTestContainers.kt`
- `src/test/kotlin/io/kotest/provided/ProjectConfig.kt`
