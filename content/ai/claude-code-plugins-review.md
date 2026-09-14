---
title: "Claude Code 플러그인 18개 깔아보고 정리한 후기"
date: 2026-04-14
tags: ["claude-code", "ai", "dx", "tooling"]
description: "Spring Boot + Kotlin 프로젝트 기준으로 18개 플러그인을 써보고 남긴 것. 워크플로우 플러그인은 하나만, LSP는 스택에 맞는 것만, 권한 화이트리스트는 처음에."
source: https://velog.io/@co-vol/Claude-Code-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-18%EA%B0%9C-%EA%B9%94%EC%95%84%EB%B3%B4%EA%B3%A0-%EC%A0%95%EB%A6%AC%ED%95%9C-%ED%9B%84%EA%B8%B0
---

## 내 프로젝트 맥락

- Spring Boot 4 + Kotlin + PostgreSQL + Redis + Kafka
- DDD 기반 설계 (Aggregate 분리, Value Object, Rich Domain Model)
- Flyway 마이그레이션, QueryDSL (KSP), Testcontainers
- 혼자 개발하지만 AI와 페어 프로그래밍하는 느낌으로 진행

이 맥락에서 "나한테 효과적이었는가"를 기준으로 평가한다. 프론트엔드 프로젝트나 팀 프로젝트라면 결론이 달라질 수 있다.

---

## 핵심 플러그인: 이것만 있어도 된다

### bkit (PDCA 워크플로우)

내 개발 흐름을 가장 많이 바꾼 플러그인이다.

`/pdca plan event-crud` → `/pdca design event-crud` → 구현 → `/pdca analyze` 순서로 진행하니까, "그냥 코드부터 치는" 습관이 사라졌다. Plan 문서에서 API 스펙과 에러코드를 먼저 정의하고, Design 문서에서 패키지 구조와 엔티티 설계를 잡고, 그 다음에 코드를 쓴다.

실제로 Event CRUD API를 구현할 때 Plan 단계에서 `DateRange` Value Object를 별도 설계하기로 결정했고, 이게 나중에 Coupon 유효기간에도 재사용됐다. 코드부터 쳤으면 Entity 안에 startedAt/endedAt을 날것으로 박아뒀을 거다.

단점도 있다. 문서 템플릿이 상당히 무겁다. feature 하나에 Plan + Design 문서가 각각 수백 줄이고, 에이전트가 18개 이상 정의되어 있어서 시스템 프롬프트가 길다. 간단한 버그 수정에도 "PDCA 사이클을 시작하시겠습니까?"라고 물어올 때가 있다. 토큰 소모가 체감된다.

**평점: 4/5** — 문서 주도 개발 습관을 만들어주지만, 가벼운 작업에는 과하다.

### commit-commands

`/commit` 한 번이면 변경 사항을 분석하고, 최근 커밋 스타일에 맞춰서 메시지를 만들어준다. 내 프로젝트 커밋 로그를 보면 `feat:`, `refactor:`, `fix:` 접두사가 일관되게 붙어 있는데, 이게 이 플러그인 덕이다.

`/commit-push-pr`도 있는데 이건 브랜치 생성 → 커밋 → 푸시 → PR 생성까지 원스톱이다. 단독 개발이라 PR을 자주 만들진 않지만, 가끔 코드 리뷰를 받을 때 유용했다.

단점은 특별히 없다. 단순하고, 하는 일이 명확하다.

**평점: 5/5** — 모든 Claude Code 사용자에게 추천.

### kotlin-lsp

Kotlin 프로젝트면 필수다. go-to-definition, 참조 찾기, 리팩토링 지원이 된다. Claude가 코드를 수정할 때 LSP 정보를 참고하니까 "이 메서드 어디서 호출되지?" 같은 질문에 정확한 답을 준다.

설치에 `brew install JetBrains/utils/kotlin-lsp`가 필요한데, Linux/WSL 환경이면 별도 설정이 필요할 수 있다.

**평점: 4/5** — Kotlin 프로젝트라면 무조건. 아니면 무시.

---

## 유용하지만 선택적인 플러그인

### code-review + code-simplifier

`/code-review`는 4개 에이전트가 병렬로 PR을 분석한다. CLAUDE.md 준수 여부, 버그 스캔, git blame 기반 히스토리 분석까지. 신뢰도 80점 이하는 필터링되니까 "이건 아닌데..." 싶은 지적이 적다.

`/simplify`는 코드 중복, 불필요한 복잡성을 찾아서 직접 수정해준다. Event CRUD 구현 후 돌렸더니 QueryDSL의 where 표현식 중복을 `EventQuery` object로 추출하라고 제안했다.

다만 두 플러그인 모두 PR이 있어야 제대로 동작한다. 로컬에서 커밋 없이 작업 중이면 분석 대상이 제한적이다.

**평점: 각각 3.5/5** — PR 기반 워크플로우라면 효과적. 혼자 개발하면 가끔 쓰는 정도.

### pr-review-toolkit

code-review의 상위 호환 같은 플러그인인데, 에이전트가 6개다. 주석 정확도, 테스트 커버리지, 에러 핸들링, 타입 설계, 코드 품질, 코드 간소화를 각각 전문 에이전트가 본다.

솔직히 code-review와 겹치는 부분이 많다. 둘 다 깔아놓으면 비슷한 리뷰를 두 번 받는 느낌이다. 하나만 고르라면 pr-review-toolkit이 더 세분화되어 있어서 이걸 추천한다.

**평점: 3.5/5** — code-review랑 중복. 하나만 골라라.

### context7 (MCP + Plugin)

라이브러리 문서 조회 도구다. "Spring Boot 4에서 Flyway 설정이 어떻게 바뀌었지?" 같은 질문에 최신 공식 문서를 기반으로 답해준다. 학습 데이터에 없는 최신 변경사항을 잡아준다는 점에서 가치가 있다.

여기서 삽질 에피소드가 하나 있다. **MCP 서버와 Plugin이 별개라는 걸 모르고 둘 다 설치했다.** MCP 서버(`npx -y @upstash/context7-mcp`)가 실제 문서 조회 엔진이고, Plugin은 "라이브러리 질문이 들어오면 context7 MCP를 써라"라는 트리거 지침일 뿐이다. Plugin만 깔고 MCP를 안 깔면 아무것도 안 된다. 반대로 MCP만 있어도 잘 동작한다.

**평점: MCP 서버 4/5, Plugin 2/5** — MCP 서버가 본체. Plugin은 있으면 좋지만 필수는 아니다.

### superpowers

개발 워크플로우 전체를 관리하는 야심찬 플러그인이다. 브레인스토밍 → 스펙 → 구현 계획 → 서브에이전트 병렬 실행까지 자동화한다는 콘셉트인데, bkit와 역할이 겹친다.

bkit가 PDCA라는 명확한 프레임워크를 제공하는 반면, superpowers는 TDD와 YAGNI 원칙을 강조하면서 좀 더 유연하게 접근한다. 둘 다 "코드부터 치지 마라"라는 철학은 같다.

내 경우 bkit를 먼저 도입해서 PDCA에 익숙해진 상태라 superpowers는 거의 안 썼다. 그런데 bkit 없이 시작하는 사람이라면 superpowers가 진입장벽이 낮을 수 있다.

**평점: 3/5** — bkit와 양자택일. 둘 다 쓸 필요는 없다.

### claude-md-management

`/revise-claude-md`로 세션 중 배운 내용을 CLAUDE.md에 반영할 수 있다. 프로젝트가 커지면서 컨벤션이 쌓이는데, 이걸 수동으로 관리하는 건 귀찮다.

내 CLAUDE.md에 "Kotlin `@field:` target 필수", "QueryDSL 정렬 필드는 화이트리스트 Map으로 관리" 같은 항목이 들어간 게 이 플러그인 덕이다.

**평점: 3.5/5** — 장기 프로젝트에서 CLAUDE.md를 관리하고 있다면 가치 있다.

---

## 안 써도 됐던 것들

### 불필요했던 LSP 플러그인 3개

jdtls-lsp (Java), typescript-lsp, gopls-lsp (Go)를 전부 깔았다. Kotlin 프로젝트인데.

플러그인 마켓에서 "LSP? 좋은 거 아니야?" 하고 다 깔았는데, 이 프로젝트에 Java/TypeScript/Go 파일이 한 개도 없다. 세션 시작할 때 불필요한 LSP 프로세스가 뜨고, 시스템 프롬프트에 쓸데없는 지침이 들어간다.

**교훈: 자기 프로젝트 기술 스택에 맞는 LSP만 설치하라.**

### figma, atlassian, gitlab

figma는 디자인 파일이 없으면 쓸 일이 없다. atlassian은 Jira/Confluence 연동인데, 인증 설정을 안 해서 매 세션마다 "Needs authentication" 경고가 뜬다. gitlab은 아예 연결 실패 상태.

이런 플러그인들이 문제인 게, 설치만 해도 시스템 프롬프트에 도구 설명이 추가된다. figma 하나만 봐도 도구 20개 이상의 설명이 주입된다. 안 쓰는 플러그인이 토큰을 잡아먹는 구조다.

여기서 느낀 건, 플러그인은 프로젝트 단위로 다르게 가져가야 한다는 거다. figma나 atlassian이 쓸모없는 플러그인이 아니라, **이 프로젝트에서** 쓸모없는 거다. 프론트엔드 프로젝트라면 figma가 핵심일 수 있고, 팀 프로젝트에서는 atlassian이 Jira 티켓 → 코드 흐름을 이어주는 허브가 된다. `.claude/settings.local.json`이 프로젝트별로 존재하는 이유가 이거다. 글로벌에 다 깔아두지 말고, 프로젝트 설정에서 필요한 것만 켜라.

**교훈: "나중에 쓸지도 몰라"로 깔지 마라. 필요할 때 깔아도 30초면 된다.**

### explanatory-output-style

코드 작성 전후에 `★ Insight` 블록으로 교육적 설명을 붙여주는 기능이다. 단순히 코드를 고쳐주는 게 아니라, 왜 이렇게 고치는 게 나은지 원리와 베스트 프랙티스를 같이 설명해준다.

새로운 언어나 프레임워크를 학습하면서 개발하는 상황이라면 꽤 쓸 만하다. 나도 Kotlin QueryDSL을 처음 잡았을 때 "왜 where 표현식을 이렇게 분리하는 게 좋은지" 설명을 보면서 감을 잡은 적이 있다. 코드 리뷰를 받는 것과 비슷한 효과라서, 주니어 개발자나 팀에 새로 합류한 사람이 코드베이스를 파악하면서 쓰기에 좋다.

문제는 토큰이다. 매 응답에 Insight가 붙으니까, 같은 작업에 대한 응답이 체감상 2-3배 길어진다. README에도 "토큰 비용 증가 주의"라고 적혀 있다. 이미 익숙한 코드를 수정할 때는 "이거 아는데..."하면서 스크롤하게 된다.

끄고 켜면서 학습 모드와 작업 모드를 오가는 게 이상적이긴 하다. 다만 현실적으로는 몇 번 읽다가 결국 끄게 되는 종류의 기능이다. 학습이 목적이면 켜두고, 속도가 목적이면 끄자.

---

## 삽질에서 배운 것들

### 권한 설정이 하나씩 쌓이는 문제

`.claude/settings.local.json`을 열어보니 `permissions.allow` 배열에 46개 항목이 있었다. `Bash(./gradlew compileKotlin)`, `Bash(curl -s "https://search.maven.org/...")` 같은 구체적인 명령어가 하나하나 들어가 있다.

이건 매번 Claude가 명령어를 실행할 때마다 "허용"을 누른 결과다. 처음에는 보안상 좋다고 생각했는데, 실제로는 `ls` 한 번 치는 것도 허가를 받아야 했다.

해결은 글로벌 설정에 읽기 전용 명령어를 일괄 허용하는 것이었다:

```json
{
  "permissions": {
    "allow": [
      "Bash(ls:*)",
      "Bash(pwd:*)",
      "Bash(which:*)",
      "Bash(tree:*)"
      // ... 등등
    ]
  }
}
```

**교훈: 프로젝트 시작할 때 안전한 명령어 화이트리스트를 먼저 설정하라.** 나중에 하면 이미 수십 개가 쌓여 있다.

### MCP 서버와 Plugin의 관계

context7에서 겪은 건데, 같은 이름의 MCP 서버와 Plugin이 있으면 뭐가 뭔지 헷갈린다. 정리하면:

- **MCP 서버** = 실제 동작하는 엔진. 프로세스가 떠서 도구(tool)를 제공한다.
- **Plugin** = 시스템 프롬프트에 지침을 주입하는 래퍼. "이런 상황에서 이 MCP 도구를 써라"라고 알려준다.

MCP 서버 없이 Plugin만 있으면 껍데기다. Plugin 없이 MCP 서버만 있으면 잘 돌아가지만, 자동 트리거가 약해질 수 있다.

### bkit vs superpowers 충돌

둘 다 "코딩 전에 생각하라"는 워크플로우 플러그인이다. 동시에 활성화하면 세션 시작할 때 두 플러그인이 각각 지침을 주입한다. 토큰 낭비인 데다가, 가끔 superpowers가 브레인스토밍을 제안하는데 bkit은 PDCA를 제안하는 상황이 생긴다.

**교훈: 워크플로우 플러그인은 하나만 쓰자.**

---

## 내 추천 조합

Kotlin/Spring Boot 서버 개발 기준으로, 이 조합이면 충분하다:

| 카테고리 | 플러그인 | 이유 |
|---------|---------|------|
| 워크플로우 | bkit **또는** superpowers | PDCA 기반이면 bkit, TDD 기반이면 superpowers |
| 커밋 | commit-commands | 커밋 메시지 자동화 |
| LSP | kotlin-lsp | 기술 스택에 맞는 LSP만 |
| 문서 조회 | context7 (MCP 서버) | Plugin은 선택 |
| 코드 리뷰 | pr-review-toolkit **또는** code-review | 하나만 |
| 프로젝트 관리 | claude-md-management | CLAUDE.md 유지보수 |

총 5-6개. 나머지는 필요할 때 추가하면 된다.

---

## 마무리

18개 깔아보고 느낀 건, 플러그인은 많다고 좋은 게 아니라는 거다. 각 플러그인이 시스템 프롬프트에 지침을 추가하고, MCP 서버는 프로세스를 띄운다. 안 쓰는 플러그인이 토큰과 리소스를 잡아먹는 구조다.

시작은 커밋 플러그인 하나로 충분하다. 거기서 "문서화가 아쉽네" 싶으면 bkit를, "최신 라이브러리 문법을 모르겠네" 싶으면 context7을 추가하면 된다. 한 번에 다 깔지 말고, 불편함이 생길 때 그걸 해결하는 플러그인을 찾아라.

```bash
# 최소 시작 세트
/plugin install commit-commands@claude-plugins-official
/plugin install kotlin-lsp@claude-plugins-official  # 본인 언어에 맞는 LSP
```

나머지는 진짜 필요해질 때 설치해도 늦지 않다.

---

원문: [velog · 2026-04-14](https://velog.io/@co-vol/Claude-Code-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-18%EA%B0%9C-%EA%B9%94%EC%95%84%EB%B3%B4%EA%B3%A0-%EC%A0%95%EB%A6%AC%ED%95%9C-%ED%9B%84%EA%B8%B0)
