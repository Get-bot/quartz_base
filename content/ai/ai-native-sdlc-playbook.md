---
title: "AI-Native SDLC 플레이북 — 6단계 요약과 내가 실제로 돌리고 있는 것"
date: 2026-09-14
tags: ["ai", "sdlc", "claude-code", "pdca", "methodology", "governance", "hooks", "evals"]
description: "Anthropic Applied AI 팀의 플레이북(2026-08)을 단계별 산출물·게이트·지표로 압축하고, 내 PDCA·CLAUDE.md·ripgrep 셀프체크가 그 위에서 어디까지 왔고 어디가 비어 있는지 대조했다."
source: https://claude.com/blog/the-ai-native-sdlc-playbook
---

Anthropic Applied AI 팀이 2026년 8월에 낸 46분짜리 글이다. 한국어 번역본으로 읽었다. 핵심은 한 문장으로 줄어든다.

> 코드가 병목이 아니게 되면 병목은 plan·review·deploy로 옮겨간다. 그러니 각 단계가 **다음 단계가 읽을 수 있는 산출물을 커밋**하고, 그 커밋이 다음 단계를 트리거하는 루프를 만들어라. 사람은 게이트에 서 있는다.

아래는 내가 다시 볼 용도로 압축한 요약이고, 마지막에 내 프로젝트(출금 API 서버, PDCA로 굴리는 중)와 대조했다.

## 왜 SDLC를 다시 짜야 하나

build가 몇 시간으로 줄어도 나머지는 사람 속도다. 그래서 세 가지가 생긴다.

- **병목이 옆으로 이동한다.** plan, review/test, deploy가 그대로 몇 주다.
- **통제 장치가 현실과 어긋난다.** 사람이 쓴 코드면 한 줄씩 리뷰하는 게 맞았다. 에이전트가 diff의 대부분을 쓰는 순간 그 방식은 못 따라간다.
- **거버넌스 비용이 오른다.** 예외 처리가 월간 위원회를 기다린다.

보안 팀이 좋은 예다. 사람 산출량에 맞춰 규모가 정해져 있어서, 에이전트가 코드를 두 배로 뽑으면 리뷰 큐가 쌓이거나 덜 리뷰된 코드가 나간다. 둘 다 안 된다면 점검이 에이전트 속도를 따라가야 한다.

## 6단계 한 장

| 단계 | 산출물 | 게이트(사람) | 지표 예 |
|---|---|---|---|
| Plan | `intent.md` — 발안자 언어 그대로 | 프로덕트 오너 승인 | 첫 대화→커밋 시간, intent 생존율 |
| Design | `spec.md` — skills가 정책을 강제 | 우려 플래그 해소 후 승인 | intent→spec 시간, plan 이후 spec 재작업 수 |
| Build | `plan.md` → diff | 계획 승인 (plan mode) | 첫 패스 머지율, diff↔plan 일치 빈도 |
| Test | 테스트 출력, 스크린샷 | 없음(기계 증거) | 첫 패스 CI 성공률, PR당 리뷰 시간 |
| Deploy | 리뷰 결과가 담긴 PR | 코드 오너 + 릴리스 hook | 첫 리뷰까지 시간, 빠져나간 결함 |
| Maintain | 인시던트 → 새 `intent.md` | 온콜 트리아지 | 위반→intent 시간, 반복 인시던트 수 |

오른쪽 열을 관통하는 실은 **커밋된 산출물**이다. 커밋 체인이 곧 감사 추적이다. 누가 요청했고, 에이전트가 뭘 만들었고, 누가 승인했는지.

## 단계별로 기억할 것

### 1. Plan — intent.md

발안자가 자기 언어로 Claude와 브레인스토밍하고 결과를 `intent.md`로 커밋한다. 문제 / 제안하는 결과 / 영향받는 사용자와 시스템 / 제약 / 열린 질문. 템플릿은 skill로 만든다. 저장 위치는 제품 레포 안 `intent/` 폴더가 가장 단순하다. 코드 옆에 산출물 체인이 놓인다.

전통 방식과의 차이는 인수인계 횟수다. 백로그 → 유저 스토리 → 리파인먼트를 거치면 엔지니어에게 도착할 때 발안자의 의도에서 여러 단계 멀어진다.

### 2. Design — spec.md

요구사항과 설계가 한 세션으로 합쳐진다. 브랜드·보안·컴플라이언스·UX 정책을 skills로 로드한 상태에서 `intent.md`를 넣고 `spec.md`를 받는다. 정책이 몇 주 뒤 리뷰가 아니라 **스펙을 쓰는 동안** 적용된다.

플래그된 우려 사항을 먼저 처리한다. 분석가라면 에스컬레이션했을 지점이다. 처음엔 손으로 프롬프팅하고, 다음엔 슬래시 커맨드, 그다음엔 intent 머지를 트리거로 비대화형 잡이 돈다.

### 3. Build — plan mode, CLAUDE.md, skills, hooks, 병렬 세션

**plan mode가 기본 출발점.** `spec.md`를 주고 계획을 받아서, 무엇을 깨뜨릴 수 있는지·어디가 위험한지·안 택한 대안은 뭔지 캐묻는다. "대화를 본 적 없는 엔지니어도 계획만으로 구현할 수 있을 때까지." 승인된 계획은 `plan.md`로 커밋하고, 구현이 벗어나면 같은 커밋에서 갱신한다.

**CLAUDE.md는 한 페이지.** 명령어, 관례, 아키텍처, 그리고 Claude가 계속 틀리는 것. 실무 규칙 하나: **같은 실수를 두 번 하면 그 교정을 CLAUDE.md에 넣는다.**

**skills는 조직 지식.** 일관되게 적용돼야 하는 정책은 skill로, CLAUDE.md나 프롬프트에 속하는 건 skill로 쓰지 않는다. 단, skill은 **권고적**이다. 위반을 드물게 만들지만 막지는 못한다.

**hooks가 그 뒤의 결정론적 층.** 보호된 경로 편집 차단, 편집 후 포매터·린터, 크리덴셜 diff 차단. 예외 없이 성립해야 하는 정책은 skill 뒤에 반드시 hook을 둔다. "skill은 위반을 드물게 만들고 hook은 거의 불가능하게 만든다."

**병렬 세션.** worktree마다 세션 하나, 두세 개가 출발점. 상한은 한 사람이 리뷰할 수 있는 흐름의 수. 반복 작업은 `.claude/agents/`의 subagent로. verifier는 앱을 띄워 동작을 확인하고 **고치지 않고 보고만** 한다.

레거시 시스템(Jira, 요구사항 도구)이 있으면 단일 진실 공급원을 하나 정한다. 레포가 원본이고 Jira가 링크만 갖거나, 반대거나. 최소한 산출물에 기록 ID, 기록에 커밋 SHA.

### 4. Test — 피드백 루프와 evals

Claude가 자기 작업을 검증할 방법을 항상 준다. 여러 명령이 필요하면 `make test` 하나로 감싼다. 목표를 정량화한다("test_status.py 전부 통과", "스크린샷이 목업과 일치").

버그 수정은 **실패하는 테스트를 먼저 커밋**하고, 그다음 "테스트 말고 코드를 고쳐"라고 한다. 수정 작업 중 테스트 파일 편집을 막는 hook으로 루프 자체를 보호한다. 코드를 고치는 에이전트가 그 코드의 점검을 약화시킬 수 있으면 안 된다.

verifier subagent와 피드백 루프는 다르다. 루프는 작업 중 계속 돌고, verifier는 끝났다고 판단한 시점에 **새 컨텍스트**로 최종 점검한다. 코드를 만든 가정에 물들지 않게.

**continuous evals**는 에이전트 설정의 회귀 테스트다. 실제 과제 20~50개를 합격 기준과 함께 모아, `CLAUDE.md`·skills·hooks가 바뀔 때마다 CI에서 돈다. 프로덕션 인시던트마다 eval을 하나 추가한다. 모델이 좋아지면 변별력 잃은 케이스는 갈아낸다.

### 5. Deploy — 리뷰, 승인 게이트, CI/CD

**PR 리뷰 루프.** 테크 리드가 `REVIEW.md`를 쓴다. 패스 세 개(버그 / 보안 / spec·plan 준수), Important의 정의("동작을 깨뜨리거나 데이터를 유출하거나 정책을 위반"), nit은 5개 캡, CI가 이미 강제하는 건 보고하지 않음. 리뷰 발견이 같은 실수를 두 번 지적하면 `CLAUDE.md`로 되돌린다. 코드를 쓴 에이전트는 승인 권한이 없다. 직무 분리.

**hooks가 승인 게이트.** hook은 차단만 아니라 **물어볼** 수도 있다. 프로덕션 배포 명령을 잡아 릴리스 승인이 없으면 `exit 2`로 막고, 이유와 승인 경로를 Claude 출력에 남긴다. 협상 불가 hook은 managed settings에 두어 개별 엔지니어가 못 끈다.

규제 산업 예시 managed settings가 실려 있다. `permissions.deny`로 시크릿 읽기와 네트워크 유출 차단, `sandbox`로 OS 수준 도메인 허용 목록, `credentials`로 `~/.ssh`·`~/.aws` 접근 거부, `allowManagedHooksOnly`·`strictKnownMarketplaces`로 로컬에서 들어오는 skill·hook·MCP 차단. 전부 기능성과의 트레이드오프라 "복사하지 말고 출발점으로".

**CI/CD.** 읽기 전용 판단(빌드 실패 트리아지, flaky 요약, 체인지로그)부터 `claude -p`로 시작한다. 쓰기는 기존 게이트 뒤에, 항상 PR로. 배포는 MCP 도구(deploy/status/rollback)로 노출해서 크리덴셜 든 셸 스크립트가 아니라 허용 목록이 되게 한다. 롤백은 파이프라인에서 가장 많이 연습된 경로여야 한다.

### 6. Maintain — 루프 닫기

결정론적 스크립트가 메트릭을 감시하고 통제 밴드가 깨지면 Claude를 실행한다. 탐지는 모델 없이, 판단만 모델.

```yaml
metric: ci_test_failure_rate
baseline: rolling_30d
rules: western_electric
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose, tools: "Read,Grep,Bash(gh run view *)" }
  3sigma: { action: propose, routes: [pull_request, runbook:rollback-deploy] }
```

에이전트는 진단 결과를 `intent.md`로 써서 Plan으로 돌려보낸다. 여기서 루프가 스스로를 먹여 돌기 시작한다. 정기 보안 스캔도 같은 처리를 받는다. 패치 하나면 PR, 그보다 크면 `intent.md`. Claude Tag로 Slack 인시던트 채널에 1차 대응자로 들어가면 채널이 곧 감사 추적이 된다.

## 내가 실제로 돌리고 있는 것과 대조

플레이북을 내 출금 API 서버 옆에 놓고 봤다.

**Plan / Design → 이미 있다, 이름만 다르다.** bkit PDCA로 `/pdca plan` → `design` → `do` → `analyze` → `report` → `archive`를 돈다. `docs/01-plan/features/`, `docs/02-design/features/`에 산출물이 쌓이고 gap-detector가 Match Rate를 낸다. 플레이북의 intent/spec/plan 3단과 거의 1:1이다. 다른 점 하나: intent.md는 "발안자의 언어"가 핵심인데, 1인 프로젝트에선 발안자가 곧 엔지니어라 그 구분이 흐릿하다. 반대로 내가 추가한 게 하나 있다. 슬라이스 design의 **Decision Log**(옵션-채택-근거 한 줄). 플레이북에는 없다. 6개월 뒤 "왜 이렇게 했지"에 답하는 가장 싼 방법이라 계속 쓸 거다.

**Check는 양방향이어야 한다는 걸 먼저 겪었다.** Match Rate 99%인데 design 문서 자체가 §2.5 표와 §3.8 본문에서 메서드명이 달랐다. 플레이북의 "머지된 diff가 plan.md와 여전히 일치하는 빈도" 지표는 코드→설계 방향만 본다. 설계 자체의 자기 일관성도 봐야 한다.

**Build → CLAUDE.md는 있고, hooks는 없다.** CLAUDE.md를 라우터로 쓰는 건 [[claude-md-router-harness-engineering|따로 정리했다]]. skills 대신 `docs/engine/` 가이드 12종을 트리거 키워드로 라우팅한다. 가드레일은 ripgrep 셀프체크인데 플레이북 기준으로 이건 **skill 단계(권고)**다. 프로젝트 `.claude/settings.json`에 hook은 하나도 없다. "예외 없이 성립해야 하는 정책은 skill 뒤에 hook"이라는 문장이 제일 아팠다.

**Test → 명령은 있고, 루프 보호와 evals는 없다.** CLAUDE.md에 `./gradlew unitTest -q --fail-fast`와 `integrationTest`를 나눠 적어놨고 "작업 후 실행"까지는 시킨다. 근데 테스트 파일 편집을 막는 hook이 없어서, 클래스 레벨 `@Transactional`이 락 경쟁을 없애버린 가짜 그린은 결국 사람이 잡았다. eval 스위트도 없다. CLAUDE.md를 고칠 때 뭐가 나아졌는지 지금은 느낌으로만 안다.

**Deploy → 리뷰는 받는데 정책 문서가 없다.** PR에 Copilot 리뷰를 받고 후속 커밋을 하고 있고, 리뷰 발견을 CLAUDE.md로 되돌리는 것도 이미 한다. 에이전트가 가이드를 안 읽고 추론하다 규칙을 어긴 걸 발견하고 원칙 5번을 추가한 게 정확히 그 사례다. 다만 `REVIEW.md`는 없다. 무엇이 Important이고 nit을 몇 개까지 받을지 정해둔 적이 없어서 리뷰 결과가 매번 다르게 온다.

**Maintain → 런북은 있지만 트리거는 사람이다.** `docs/runbook/`에 Valkey 장애, outbox, safety cron 런북 세 개가 있다. 전부 사람이 읽고 사람이 실행한다. bands.yaml 같은 결정론적 트리거도, 인시던트를 intent로 되돌리는 경로도 없다.

## 읽고 남은 생각

- 지표가 전부 **git과 PR 메타데이터에서 나온다.** 새 도구 없이 지금 레포에서 `git log`로 셀 수 있다. 내 PDCA도 Match Rate 하나만 보는데, "첫 plan 커밋 이후 design이 바뀐 횟수"를 세보면 설계가 얼마나 흔들리는지 보일 것 같다.
- 회의적인 부분도 있다. intent 생존율, PO 승인 게이트, 정책 소유자 같은 건 조직이 있을 때 얘기다. 혼자 하면 게이트가 형식이 되기 쉽다. 그래도 `plan.md`를 커밋하고 그대로 구현하는 습관은 혼자서도 효과가 있었다. 5번째 feature를 하루에 끝낸 건 앞의 네 개가 그 습관으로 쌓여 있었기 때문이다.
- "탐지는 결정론적으로, 판단만 모델에게"는 지금 바로 가져갈 수 있는 원칙이다. 3σ에서 PR 제안까지만 허용하고 머지는 사람이. 유지보수 단계 전체를 못 만들어도 이 선은 그을 수 있다.

## 다음에 할 것

1. hook 하나. 수정 작업 중 `src/test/**` 편집 차단. 플레이북에서 제일 싸고 제일 효과 큰 걸로 보인다.
2. `REVIEW.md` 초안. 패스 3개, Important 정의, nit 캡. Copilot 리뷰 설정에도 같은 기준을 넣는다.
3. eval 5개부터. 최근 CLAUDE.md 변경으로 막으려 했던 실수 5개를 과제로 만들어, CLAUDE.md가 바뀔 때 돌려본다.

## 참고

- Louis Claxton, [The AI-Native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook), Claude by Anthropic, 2026-08-21
- [[TIL-260425-pdca-1-day-cycle|PDCA 1-day Cycle과 Design Self-Inconsistency]] — 위에서 말한 양방향 Check
- [[TIL-260506-slice-design-decision-log|슬라이스 Design 작성법]] — Decision Log
- [[TIL-260521-pessimistic-write-integration-test|PESSIMISTIC_WRITE 실효성 검증]] — 사람이 잡은 가짜 그린
- [[claude-md-router-harness-engineering|CLAUDE.md는 매뉴얼이 아니라 라우터다]]
