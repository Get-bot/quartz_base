---
title: "CLAUDE.md는 매뉴얼이 아니라 라우터다 — 출금 API 서버에서 해본 하네스 엔지니어링"
date: 2026-09-14
tags: ["claude-code", "harness-engineering", "claude-md", "ai", "dx", "documentation", "architecture"]
description: "137줄 CLAUDE.md가 트리거 키워드로 docs/engine/ 가이드 12종을 라우팅한다. 가이드가 3,933줄까지 부풀었다가 절반으로 줄인 일, 에이전트가 가이드를 안 읽고 추론하다 규칙을 어긴 일, 그리고 OpenAI의 하네스 엔지니어링 글과 나란히 놓고 본 빈자리."
---

출금 API 서버(Spring Boot 4 + Kotlin, AWS 멀티 인스턴스)를 Claude Code와 같이 만들면서 CLAUDE.md를 5개월 동안 계속 고쳤다. 지금 모양은 "규칙을 다 적은 문서"가 아니라 **"이 키워드가 나오면 저 가이드를 읽어라"는 라우팅 표**다. 여기까지 오는 데 두 번 넘어졌고, OpenAI의 하네스 엔지니어링 글을 옆에 놓고 보니 넘어진 지점이 거의 같았다.

## 지금 구조

CLAUDE.md는 137줄이다. 세 덩어리로 되어 있다.

**1. 프로젝트와 무관한 원칙 5개.** Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, 그리고 나중에 추가한 Read the Guide Before You Code. 어느 레포에 붙여도 되는 내용이라 맨 위에 둔다.

**2. 이 프로젝트만의 컨텍스트.** 스택 버전, 그리고 코드만 봐서는 절대 알 수 없는 운영 조건. ALB 뒤에 API 인스턴스가 N개고 ElastiCache for Valkey 엔드포인트 하나를 공유한다는 것, Redis가 죽으면 idempotency·daily reset·zombie cooldown·outbox가 전부 멈추는 P0 인프라라는 것. 이걸 안 적어두면 에이전트는 in-memory 캐시나 `@Scheduled`를 단일 인스턴스 가정으로 넣는다. 그래서 5월 12일 정비 때 이 문단을 넣었다.

**3. Knowledge Base 표.** 핵심이다.

| 문서 | 다루는 영역 | 트리거 키워드 |
|---|---|---|
| `JPA_WRITE_GUIDE.md` | Entity 설계 · Aggregate 경계 · UUID v7 · Flyway · 락 | Entity / Repository / `@ManyToOne` / Aggregate / Flyway / `@Lock` / `SKIP LOCKED` … |
| `TEST_WRITE_GUIDE.md` | 4-Layer 피라미드 · Kotest + Testcontainers · `@Tags("integration")` 분기 | 테스트 / Fixture / `@SpringBootTest` / Testcontainers / `withData` / `@Isolate` … |
| … 10종 더 | | |

사용 규칙은 한 줄이다. "작업 지시·질문·설계 문서에 트리거 키워드가 등장하면 **구현 시작 전에** 해당 가이드를 먼저 읽는다." 가이드 12종을 합치면 2,710줄인데, 이걸 CLAUDE.md에 넣었으면 매 세션 컨텍스트의 상당 부분을 규칙 읽기에 썼을 거다. 라우팅 표로 두면 그 작업에 걸리는 가이드만 읽는다.

## 가이드 한 편의 모양

가이드는 다 같은 골격이다. 맨 위에 트리거 키워드, 그다음 **결정 트리**, 규칙과 이유, 마지막에 **셀프체크 ripgrep**.

결정 트리는 TEST 가이드가 제일 잘 보여준다.

```
이 테스트가 검증하는 대상은?
├── 1. VO/Entity/Enum 불변식·상태 전이            → L1  Spring X / mock X
├── 2. Service orchestration (Repository만 주입)  → L2  Spring X / mockk
├── 3. Repository 쿼리 (JPA/QueryDSL)             → L3-R @RepositorySliceTest + @Tags("integration")
├── 4. Controller HTTP I/O                        → L3-C @WebMvcTest + @Tags("integration")
└── 5. 다중 컴포넌트 / 컨테이너 / 동시성            → L4  @SpringBootTest + @Tags("integration")
```

"위에서부터 첫 매칭되는 줄을 그대로 적용한다." 에이전트에게 판단을 맡기는 대신 분기표를 준다. 첫 매칭 줄을 적용하라고 하면 애매한 경우가 줄어든다.

셀프체크는 작업이 끝난 뒤 에이전트가 스스로 돌리는 명령이다.

```bash
# @SpringBootTest 인데 @Tags("integration") 없는 파일 검출
rg -l -E '^@(SpringBootTest|WebMvcTest|DataJpaTest)\b' src/test \
  | while read f; do
      grep -q -E '@Tags\("integration"\)' "$f" || echo "MISSING_TAGS: $f"
    done
```

솔직히 이건 린터를 만들 시간이 없어서 택한 타협이다. 강제가 아니라 권고고, 에이전트가 안 돌리면 그만이다. 그래도 확인 명령이 있는 규칙은 어겼을 때 바로 드러난다. 없는 규칙은 리뷰에서 사람이 잡아야 한다.

## 첫 번째 실패 — 가이드가 3,933줄이 됐다

4월 17일 첫 버전엔 가이드가 TEST·DTO·JPA 3개였고 컨벤션 문장은 CLAUDE.md 본문에 같이 있었다. 문제가 생길 때마다 가이드를 하나씩 추가했다. ERROR, COMMIT, COMMENT, NAMING, SWAGGER, OBSERVABILITY, CLOCK, EXTERNAL_SYSTEM_KEYS. 5주 만에 12개.

그러다 5월 12일에 7종을 세어보니 3,933줄이었다. 예시 코드가 세 벌씩 있고 같은 설명이 §2와 §7에 반복됐다. 가이드 하나가 900줄이면 읽는 것 자체가 컨텍스트 비용이다. 규칙을 다 담고도 안 지켜지면 내용이 아니라 길이가 문제라고 봤다.

압축했다. 3,933줄 → 2,113줄. 원칙은 "**why·anti-pattern·ripgrep 명령은 전부 남기고, 예시 코드는 한 벌만**". v1은 `docs/archive/engine-v1/`에 그대로 두고 v2를 새로 썼다. 짧아진 뒤 효과를 숫자로 재두지 않은 게 아쉽다. 전후 위반 건수를 세어놨어야 했다.

## 두 번째 실패 — 가이드를 안 읽고 코드에서 추론했다

5월 20일. 에이전트가 테스트 파일에 L1 라벨을 잘못 붙이고 sealed result 클래스를 정해진 위치가 아닌 곳에 만들었다. 둘 다 가이드에 명시된 규칙이다. 확인해보니 가이드를 Read하지 않고 **기존 코드 패턴을 보고 추론**해서 작업했다.

그래서 원칙 5번을 추가했다.

> Before writing project-specific code, check whether a guide covers your work area. If yes, **open it with the Read tool first**. Inference from existing code patterns is fine as a supplementary signal, but **the guide's explicit rules take precedence**.

라우팅 표만 있으면 될 줄 알았는데, "표를 보고 실제로 읽어라"까지 적어야 했다. 코드베이스에 위반 사례가 하나라도 있으면 추론은 그걸 정답으로 배운다. 가이드가 정본이라는 걸 문장으로 박아야 한다.

## OpenAI의 하네스 엔지니어링과 나란히 놓으면

OpenAI가 2026년 2월에 낸 [Harness engineering](https://openai.com/index/harness-engineering/) 글은 7명이 5개월 동안 손으로 코드 한 줄도 안 쓰고 약 100만 줄, PR 1,500개를 만든 기록이다. 그 글의 뼈대가 이거다.

- **AGENTS.md는 ~100줄 지도.** 처음엔 거대한 한 파일로 갔다가 실패했다. 이유 넷: 컨텍스트를 잠식한다, 전부 중요하면 아무것도 중요하지 않다, 바로 썩는다, 검증할 방법이 없다.
- **docs/가 system of record.** design-docs, exec-plans, references, product-specs. "에이전트 입장에서 실행 중 컨텍스트로 접근할 수 없는 것은 존재하지 않는 것과 같다."
- **커스텀 린터와 구조 테스트**로 레이어 경계와 의존 방향을 기계적으로 강제.
- **legibility.** 앱 UI, 로그, 메트릭을 에이전트가 직접 볼 수 있게(Chrome DevTools Protocol, worktree별 로컬 관측 스택).
- **doc-gardening 에이전트**가 낡은 문서를 찾아 PR을 연다. "기술 부채는 고금리 대출이라 조금씩 계속 갚는 게 낫다."

내 것과 대응시키면 이렇다.

| OpenAI | 출금 API 서버 | 격차 |
|---|---|---|
| AGENTS.md ~100줄, 지도 | CLAUDE.md 137줄, 트리거 키워드 라우팅 | 거의 같음 |
| docs/ system of record | `docs/engine/` 12종 + PDCA `01-plan`·`02-design` | 같은 방향 |
| 커스텀 린터 + 구조 테스트 | ripgrep 셀프체크 | **강제 vs 권고** |
| 앱·로그·메트릭 legibility | `bootRun` + Swagger UI 눈으로 확인 | 약함 |
| doc-gardening 에이전트 | 손으로 한 v2 압축 1회 | 없음 |

라우팅 표와 docs 분리는 같은 결론에 도착했다. 다른 건 **강제의 층**이다. OpenAI는 규칙을 린터로 만들어 CI가 막고, 나는 에이전트가 ripgrep을 돌려주기를 기대한다. 이 차이가 "규칙을 어긴 채 머지되는 PR"의 빈도 차이로 나타날 거다.

## 하네스도 거짓 통과를 만든다

같은 레포에서 하네스라는 단어를 다른 뜻으로도 썼다. 외부 IP 허용 목록 기능을 설계할 때 XFF 스푸핑 방어를 L4 테스트로 증명해야 했는데, **테스트 하네스를 어떻게 꾸미느냐에 따라 아무것도 증명하지 못하는 PASS**가 나온다는 걸 계획 리뷰에서 잡았다.

- 위조 토큰 하나만 보내는 구성(`X-Forwarded-For: <위조된 등록 IP>`)은 loopback이 신뢰 프록시로 인식되어 그 토큰을 진짜 클라이언트로 믿는다. 통과하지만 방어 증명이 아니다. vacuous PASS.
- 두 토큰 구성(`<위조된 등록 IP>, <공격자 실제 IP>`)이어야 RemoteIpValve가 오른쪽에서 왼쪽으로 걷다 첫 비신뢰 IP에서 멈추고, 위조 토큰은 도달조차 못 한다. 이때 403이 나와야 진짜 방어다.

계획 문서에 "Interpretation A 핀, B 금지"라고 박아두고 MockMvc도 금지했다(RemoteIpValve를 안 거쳐서 거짓 안심). 에이전트를 조종하는 하네스든 테스트 하네스든, **하네스 자체가 검증 대상**이라는 점은 같다. 가이드가 틀리면 에이전트는 틀린 걸 정확하게 따른다.

## 다음에 할 것

- ripgrep 셀프체크 중 자주 걸리는 3개를 Konsist나 ArchUnit 규칙으로 승격해서 `./gradlew test`에서 실패하게 만들기. 권고에서 강제로.
- 가이드가 언급하는 클래스·애노테이션 이름이 코드에 실제로 있는지 주기적으로 대조하는 스크립트. doc-gardening의 축소판. 지금은 가이드가 낡아도 아무도 모른다.
- CLAUDE.md 137줄 중 40줄이 빌드·테스트 명령 블록이다. 뺄까 했는데 매 세션 필요한 거라 남긴다. 대신 Pagination 같은 세부 컨벤션 문장이 아직 본문에 남아 있어 그건 가이드로 보낼 것.

## 참고

- OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/) (2026-02)
- [[TIL-260425-pdca-1-day-cycle|PDCA 1-day Cycle]] — 이 레포의 설계 문서 흐름
- [[TIL-260602-alb-nginx-xff-client-ip|ALB·nginx 뒤에서 진짜 Client IP 잡기]] — 위 스푸핑 하네스의 배경
- [[ai-native-sdlc-playbook|AI-Native SDLC 플레이북 요약]] — CLAUDE.md·skills·hooks를 SDLC 전체에 놓고 본 글
