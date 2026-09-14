---
title: "[TIL-260429] Swagger UI X-Device-Id 자동 주입 + Kotlin 코드 스타일(.editorconfig) 정착"
date: 2026-04-29
tags: ["Swagger", "SpringDoc", "editorconfig", "Kotlin", "DX"]
categories: ["TIL"]
description: "SpringDoc SwaggerIndexPageTransformer + MutationObserver로 X-Device-Id 자동 주입, .editorconfig로 trailing comma·EOF newline·star import 일괄 정착"
---

## 잘한 점

### Swagger UI X-Device-Id 자동 주입 — 매번 헤더 입력하던 마찰 제거

**상황**
- 모든 API가 `X-Device-Id` 헤더를 요구하는데, Swagger UI에서 매 요청마다 손으로 UUID 입력하던 상황
- API 5개 테스트하면 5번 복붙 — 작은 마찰이지만 일과 통증

**액션**
- `SwaggerConfig` 에 `SwaggerIndexPageTransformer` 확장으로 `swagger-initializer.js` 에 `swagger-custom.js` 로더 주입
- `swagger-custom.js`: `sessionStorage` 에 `X-Device-Id` UUID v4 한 번 생성·저장, 이후 모든 요청에서 재사용
- `MutationObserver` 로 React 기반 Swagger UI input 노드를 감지해서 자동으로 채움

**칭찬**
- 작은 마찰을 그냥 참지 않고 30분 들여서 영구히 없앤 것 — 누적되면 진짜 시간 도둑
- React input은 그냥 value 박으면 안 채워지는 함정도 잘 피해갔음 (`MutationObserver` + native setter)

---

### `.editorconfig` 정비 — Kotlin trailing comma 제거 + EOF newline + star import 비활성화

**상황**
- IntelliJ 기본값이 star import 임계값 5 → `java.util.*` 같은 on-demand import가 자꾸 PR에 섞여 들어옴
- Kotlin 컨벤션상 마지막 파라미터에 trailing comma 안 쓰는 게 우리 팀 결정인데 IDE마다 결과가 달랐음
- POSIX 표준 "EOF newline" 도 일부 파일이 빠져 있어서 `git diff` 가 한 줄로 시끄러움

**액션**
- `.editorconfig` 에 명시:
  - `ij_kotlin_name_count_to_use_star_import = 99` → 사실상 star import 비활성화
  - `ij_kotlin_packages_to_use_import_on_demand =` (빈 값) → `java.util.*` 같은 강제 on-demand 제거
  - trailing comma 제거 규칙
  - `insert_final_newline = true`
- 비Kotlin 언어 섹션(CSS·Java·XML 등) 제거 — 우리 프로젝트가 안 쓰는 언어 규칙은 노이즈
- 부록: `BankController` `@Tag` 오타 ("수취 은행 을관리" → "수취 은행 관리") 발견·수정

**칭찬**
- 진짜 우리 코드베이스가 쓰는 규칙만 남긴 것 — "있을 법한 미래" 규칙 안 박은 절제

---

## 개선점

### `swagger-initializer.js` 직접 patch는 SpringDoc 마이너 버전 업에 깨질 수 있음

**문제**
- `SwaggerIndexPageTransformer` 인터페이스에 의존하는 패치라, SpringDoc 내부 변경에 민감
- 깨졌을 때 "왜 X-Device-Id가 안 들어가지?" 디버깅이 한 번 더 어려움

**원인**
- Swagger UI 자체가 헤더 자동 주입을 공식적으로 지원 안 함 → patch 외엔 마땅한 방법 없음

**액션플랜**
- SpringDoc 버전 업 시 `swagger-initializer.js` 동작 회귀 테스트 (수동이라도)
- 장기적으로는 `OperationCustomizer` 쪽으로 이전 가능한지 추적

---

### IntelliJ star import 임계값 5 가 묵묵히 만든 부채

**문제**
- `java.util.*` `kotlin.collections.*` 같은 on-demand import가 누적된 PR이 여러 건
- 코드 리뷰에서 import만 보면 화면이 한 번 깜빡거림

**원인**
- IntelliJ 기본값을 "맞나 보다" 하고 그대로 둔 게 누적
- `.editorconfig` 안 쓰는 동안 IDE 설정에 의존했음

**액션플랜**
- 새 프로젝트 부트스트랩 시 첫 PR에 `.editorconfig` 박기
- IDE 기본값은 의심부터 — 컨벤션이 없으면 IDE가 결정해버림

---

## 배운 점

### 작은 마찰 = 큰 비용 (누적이라서)

**배움**
- Swagger 헤더 한 줄 입력이 별 거 아닌 것 같지만, 하루 50회 × 30일 = 1500번 복붙
- 30분 투자해서 영구 제거하는 게 거의 항상 이득

**의미**
- "매번 손으로 하는 게 짜증나는 일" 이 떠오르면 바로 자동화 후보로 메모

---

### `.editorconfig` 는 IDE 설정 PR을 막는 핵심 도구

**배움**
- `.editorconfig` 없이 IDE 설정에 맡기면 "누가 어떤 IDE로 열었느냐" 가 PR diff에 섞임
- 한 명이 VS Code 쓰고 한 명이 IntelliJ 쓰면 더 심함
- 트리비얼한 포맷 차이가 리뷰 시간을 잡아먹음

**의미**
- 새 레포는 `.editorconfig` 가 첫 커밋
- 우리 팀 컨벤션을 명시해야 IDE 기본값이 침범 못 함

---

## 핵심 내용

### 키워드
- `SwaggerIndexPageTransformer`, `swagger-initializer.js`, `MutationObserver`, `sessionStorage`, `.editorconfig`, `ij_kotlin_name_count_to_use_star_import`, `trailing_comma`, `insert_final_newline`

### 요약
- **Swagger 자동 주입**: SpringDoc Transformer 확장으로 `swagger-initializer.js` 에 custom JS loader 주입. React input은 `MutationObserver` + native value setter 로 채움.
- **editorconfig 핵심 키**:
  - `ij_kotlin_name_count_to_use_star_import = 99` — 사실상 star import 끔
  - `ij_kotlin_packages_to_use_import_on_demand =` (빈 값) — `java.util.*` 강제 on-demand 차단
  - `insert_final_newline = true`
- **trailing comma**: Kotlin 마지막 파라미터 후행 쉼표 제거 (팀 컨벤션)

### 코드/명령어
```javascript
// swagger-custom.js — sessionStorage UUID 한 번 생성, MutationObserver로 input 채움
(function () {
  const KEY = 'X-Device-Id';
  if (!sessionStorage.getItem(KEY)) {
    sessionStorage.setItem(KEY, crypto.randomUUID());
  }
  const observer = new MutationObserver(() => {
    document.querySelectorAll('input[placeholder="X-Device-Id"]').forEach((input) => {
      if (!input.value) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(input, sessionStorage.getItem(KEY));
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
```

```ini
# .editorconfig (Kotlin 핵심)
[*.{kt,kts}]
ij_kotlin_name_count_to_use_star_import = 99
ij_kotlin_packages_to_use_import_on_demand =
ij_kotlin_allow_trailing_comma = false
ij_kotlin_allow_trailing_comma_on_call_site = false
insert_final_newline = true
```

### 참고 자료
- `src/main/kotlin/com/bubaum/buws/global/config/SwaggerConfig.kt`
- `src/main/resources/static/swagger-custom.js`
- `.editorconfig`
- 커밋: `44a5b27` (Swagger + editorconfig star import), `99c8a38` (trailing comma + EOF)
