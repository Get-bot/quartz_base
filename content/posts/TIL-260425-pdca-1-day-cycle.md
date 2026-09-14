---
title: "[TIL-260425] PDCA 1-day Cycle과 Design Self-Inconsistency"
date: 2026-04-25
tags: ["PDCA", "bkit", "Software Methodology", "Design Validation", "Architecture", "Roadmap"]
categories: ["TIL"]
description: "Flash Sale Roadmap 5/5를 1일 PDCA cycle로 완주. Match Rate 99%여도 design 자기 모순 3건 발견 → Check phase는 양방향 검증임을 체감"
---

## 잘한 점

### PDCA 5-phase를 1일 만에 완주

**상황**
- 선착순 쿠폰 시스템 Flash Sale Roadmap 5/5(Waiting Queue) 작업
- Plan은 2026-04-09에 미리 작성해뒀고, Design부터 Archive까지 동일자(2026-04-25)에 처리해야 했음
- 보통 한 feature당 12~17일 걸리던 사이클을 단 하루로 압축

**액션**
- Design → Do → Check → Report → Archive를 같은 날 모두 끝냄
- gap-detector가 Match Rate 99.0% 첫 시도에 임계값(90%) 통과 → iteration 0회
- 신규 코드 ~600 lines는 모두 신규 추가 (`coupon/scheduler/` 패키지 전체 신규 등)
- 기존 파일 수정은 RedisConfig + ErrorCode + EventRepository + application.yaml 4개에 1~3줄짜리 추가뿐

**칭찬**
- 1일 사이클이 가능했던 이유를 분명하게 알게 된 것 — "기존 인프라 재사용 정도 × 신규 코드의 격리도"의 함수
- redis-stock(Lua) → concurrency-test(latch) → kafka-consumer(Peak Load) → waiting-queue(Backpressure)로 적층되는 학습 구조를 의도적으로 설계해온 게 5번째에 결실
- Roadmap 5/5 완주의 누적적 가치를 직접 체감

---

## 개선점

### Design self-inconsistency를 늦게 발견

**문제**
- gap-detector가 Match Rate 99%인데도 P2 결함 3건을 발견
- 모두 design 문서 *내부의* 자기 모순:
  - §2.5 Dependencies 표는 메서드명을 `findAllByEventStatusAndStartedAtBeforeAndEndedAtAfter`로 표기
  - §3.8 본문 코드 예시와 실제 구현은 명시적 `@Query` + 메서드명 `findAllOpenAt`
  - §3.8 인터페이스 시그니처에 `EventQueryRepository` 표기 (실제 프로젝트는 분리 구조)
- 다행히 구현자가 §3.8 본문을 따른 덕분에 컴파일은 됐지만, design을 그대로 복사했다면 컴파일 에러

**원인**
- design 문서의 §2.5(요약 표)와 §3.8(상세 코드)을 작성한 시점이 미묘하게 달랐을 가능성
- 작성자가 다른 프로젝트 패턴을 차용해서 §3.8 인터페이스를 표기했을 수도
- design-validator agent를 Design phase 직후 돌리지 않아서 자기 모순 검증이 누락됨

**액션플랜**
- 다음 PDCA 사이클부터는 Design 직후 design-validator agent 실행 → 자기 모순 자동 탐지
- Match Rate 99%여도 P2가 잡히는 이유가 design 자체 결함일 수 있다는 인식
- 이번 P2는 archive 후라 사실상 historical — 수정 가치 낮으나 다음 cycle을 위한 교훈

### Auto-tracking hook의 false-positive

**문제**
- `.bkit/state/pdca-status.json`의 자동 추적 hook이 패키지 디렉토리명을 feature로 오인
- waiting-queue 구현 중 `coupon/scheduler/`, `coupon/service/`, `global/config/` 등의 디렉토리명 7개가 feature로 등록됨
- `activeFeatures: ["config", "repository", "exception", "response", "service", "controller", "scheduler"]` 같은 노이즈

**원인**
- hook이 파일 경로의 디렉토리 이름을 무차별로 feature 식별자로 추출
- 실제 feature 이름 패턴(`^\d{2}-[\w-]+$`)에 대한 검증이 없음
- 매번 같은 일이 재발할 수밖에 없는 시스템적 결함

**액션플랜**
- `/update-config`로 hook 설정에 feature name regex 추가하거나 hook 자체 비활성화
- `/pdca` 명령으로만 state를 업데이트하는 방식이 더 결정적
- 본 사이클은 `/pdca cleanup`으로 7개 정리 + archived 3건 summary 보존으로 처리

---

## 배운 점

### PDCA Check phase는 양방향 검증이다

**배움**
- Match Rate 99%로 매우 높은데도 design 측 결함이 잡힌 게 인상적
- "코드가 design을 따르는가"만 검증하는 게 아니라 "design 자체가 자기 일관성이 있는가"도 함께 검증됨
- 즉 Check phase는 단방향(설계 → 구현)이 아니라 양방향 — 양쪽 모두 결함 가능

**의미**
- 다음 사이클부터는 design-validator를 Design phase 직후 돌리는 습관
- Match Rate가 높다고 무조건 통과로 보지 말 것 — P2도 그 자체의 학습 가치가 있음
- 검증 도구의 일관성 체크 능력을 적극 활용

### 1-day cycle은 적층 구조의 함수

**배움**
- Roadmap의 의의는 "feature를 따로따로 만든 것"이 아니라 "이전 feature를 100% 재사용"한 것
- waiting-queue가 1일 만에 끝난 이유: Scheduler가 `CouponIssueService.issue()`를 그대로 호출 → redis-stock의 Lua + kafka-consumer의 Producer 보상 경로 무변경
- 신규 코드는 enter/scheduler/result 3개의 추가만, 기존 코드는 1~3줄짜리 변경만

**의미**
- 신규 feature를 설계할 때 "기존 자원을 어떻게 재사용할 것인가"를 먼저 묻는 습관
- "신규 코드의 격리도"가 클수록 회귀 위험이 줄어들고 사이클이 빨라짐
- Roadmap을 만들 때 각 단계가 이전 단계의 결과물에 의존하지만 변경하지 않도록 설계

---

## 핵심 내용

### 키워드
- `PDCA cycle`, `Match Rate`, `gap-detector`, `design-validator`, `bkit:pdca`, `1-day cycle`, `roadmap stacking`, `auto-tracking false-positive`

### 요약
- **PDCA 5-phase**: Plan(요구사항) → Design(상세 설계) → Do(구현) → Check(gap 분석) → Report(통합 보고서) → Archive(문서 이동 + summary 보존).
- **Match Rate 임계값**: ≥ 90% → Report 진입 가능, < 90% → pdca-iterator로 자동 개선 반복(최대 5회).
- **자기 모순(Self-inconsistency)**: design 문서 내부의 §2.5 표와 §3.8 본문이 메서드명/인터페이스 시그니처에서 불일치 → design-validator로 사전 탐지 가능.
- **적층 구조의 효과**: Roadmap 5/5에서 신규 코드는 11개, 기존 수정은 1~3줄짜리 4개 → 1-day cycle 가능.

### 코드/명령어

```bash
# PDCA 5-phase 명령
/pdca plan {feature}      # 요구사항 + Executive Summary 4-perspective
/pdca design {feature}    # 상세 설계 (architecture, sequence, error matrix)
/pdca do {feature}        # 구현 (TaskCreate로 추적)
/pdca analyze {feature}   # gap-detector → docs/03-analysis/
/pdca iterate {feature}   # Match Rate < 90% 시 pdca-iterator (max 5)
/pdca report {feature}    # report-generator → docs/04-report/features/
/pdca archive {feature} --summary  # docs/archive/YYYY-MM/{feature}/ + summary 보존
/pdca cleanup             # archived/false-positive 정리

# 일자 표기 차이
# - 파일명/슬러그: YYMMDD (260425)
# - 커밋/frontmatter: YYYY-MM-DD (2026-04-25)
```

### Roadmap 메트릭 비교

| Feature | Match | Iter | Duration | 신규 비중 |
|---|---|---|---|---|
| Event CRUD (DDD) | 95% | 0 | 17d | baseline 다수 |
| Redis Stock (Lua) | 97% | 1 (78→97) | 8d | 신규 9 + 기존 수정 |
| Concurrency Test | 100% | 0 | 3d | 신규 1 (test only) |
| Kafka Consumer | 97% | 0 | 12d | 신규 4 + 기존 6 + 삭제 1 |
| **Waiting Queue** | **99%** | **0** | **1d** ⭐ | 신규 11 + 기존 4 (1~3줄) |

### 참고 자료
- bkit PDCA Skill: `/bkit:pdca`
- 본 PR: https://github.com/Get-bot/spring-event-lab/pull/7
- Spring Event Lab repo: https://github.com/Get-bot/spring-event-lab
