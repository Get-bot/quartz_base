---
title: "[TIL-260506] 슬라이스 Design 작성법 — Parent 인용 + Decision Log"
date: 2026-05-06
tags: ["Design Document", "PDCA", "기술 글쓰기", "Architecture", "Slice Design"]
categories: ["TIL"]
description: "Parent design을 손대지 않고 슬라이스 design을 매핑+갭화해+Decision Log 3가지 책임으로 좁게 작성하는 방법"
---

## 잘한 점

### withdrawal-safety-cron design을 "갭 매핑 + 결정 박제"만 쓰게 좁힘

**상황**
- `withdrawal-core.design` 에 두 cron(Zombie Detector / Daily Reset Job)의 클래스 시그니처·cron 식·락 키·임계값까지 이미 lock되어 있음
- 이걸 한 슬라이스로 구현하려는 design을 새로 쓰는 상황 — parent의 architecture 결정을 다시 풀어쓰면 출처가 두 곳이 되고 동기화 부담 발생

**액션**
- 슬라이스 design을 3가지 책임만 갖게 좁힘:
  - Plan ↔ Parent Design ↔ 본 design 매핑 표 (어느 섹션의 spec을 어디로 옮기는지)
  - Plan ↔ Parent Design 갭 화해 (Plan이 parent와 미세하게 다를 때 어느 쪽 채택할지 + 근거)
  - Decision Log 7개 (D1~D7) — 옵션·채택·근거를 한 줄씩 lock
- "Architecture 결정 재서술 금지" 룰을 design 서두에 명시, parent 라인 번호로 인용

**칭찬**
- "design은 길어야 좋다"는 관성을 깨고 부모-자식 design을 따로 쓸 때의 책임 분리를 명확히 한 것
- Plan 작성 후 parent design을 재독해서 "Plan이 잘못 썼는지, parent가 illustrative한지" 갭 화해 표를 따로 만든 것 — 나중에 의문 생겨도 결정 근거가 박제됨

---

## 배운 점

### Decision Log는 "왜"를 박제하는 가장 싼 방법

**배움**
- 결정 자체보다 "왜 이걸 채택했는지"가 6개월 후 읽을 때 훨씬 가치 있음
- 옵션-채택-근거 3컬럼 표 한 줄이면 충분 (한 결정에 한 줄)
- 예: "Reset batch SQL = JPQL 1차 → 실패 시 native fallback" — 근거: "Money VO `@AttributeOverride` JPQL 호환 미검증". 6개월 후 누가 native로 바꾼 걸 의심해도 즉시 답변 가능

**의미**
- 디자인 문서가 길어지는 이유는 "결정 후보를 다 풀어쓰고 싶어서"인데, Decision Log 한 줄로 압축 가능
- 본문에는 "어떻게"만, Decision Log에는 "왜"만 — 두 책임 섞이면 본문이 늘어짐
- 다음 design부터 Decision Log 섹션 default로 들어가게 하자
- Plan은 "무엇을 할지", Parent Design은 "전체 그림", 슬라이스 Design은 "갭 + 결정" — 3단 분리가 명확해질수록 각 문서가 짧아짐

---

## 핵심 내용

### 키워드
- `slice design`, `Decision Log`, `Plan ↔ Design 갭 화해`, `parent design 인용`, `surgical design`

### 요약
- **부모-자식 design 분리 시 자식의 책임**: ① 매핑 표 (parent의 어느 섹션 → 본 design의 어느 섹션) ② 갭 화해 표 (Plan vs Parent 차이 + 채택 근거) ③ Decision Log (옵션-채택-근거 한 줄). Architecture 재서술 금지.
- **Decision Log 형식**: `# / 결정 항목 / 옵션 / 채택 / 근거` 5컬럼. 한 줄에 한 결정. 본문에서는 "D1 결정에 따라 ..."로만 인용해서 본문 짧게 유지.
- **Plan 갭 화해 절차**: Plan 작성 후 parent design을 재독한다. Plan이 parent와 미세하게 다르면 "Plan 채택 / Parent 채택 / 둘 다 변경" 중 결정해서 표로 박제. parent 코드 스니펫이 illustrative인지 lock인지 구분이 핵심.

### 코드/명령어

```markdown
<!-- Decision Log 템플릿 -->
## 1.5 Decision Log (본 design이 Plan 위에 lock하는 결정)

| # | 결정 항목 | 옵션 | 채택 | 근거 |
|---|----------|------|------|------|
| D1 | Reset batch SQL | JPQL only / JPQL→native fallback | JPQL→native fallback | Money VO @AttributeOverride JPQL 호환 미검증 |
| D2 | cooldown 저장소 | RedisTemplate SETEX / Redisson RBucket | Redisson RBucket | 기존 IdempotencyStore 패턴 일치, 의존성 1개 |
| D3 | dailyReset audit 발행 위치 | tx 내부 / commit 후 | commit 후 | tx 롤백이 batch UPDATE 무효화하는 risk 차단 |
```

```markdown
<!-- Plan ↔ Parent Design 갭 화해 템플릿 -->
## 1.3 Plan ↔ Parent Design 갭 화해

| 갭 | Plan | Parent Design | 본 design 결정 |
|----|------|---------------|--------------|
| Audit 시그니처 | (id, status, ageMinutes, cause) | (id, status) — illustrative | Plan 채택 (확장) — 운영 alert 분기에 cause 필수 |
| 임계값 분리 | READY≥5min / SUBMITTED≥30min 분리 | 단일 thresholdMinutes 코드 스니펫 | Plan 채택 — properties는 분리되어 있음 (kt:50-52) |
```

```markdown
<!-- Parent Design 매핑 표 템플릿 -->
## 1.1 본 슬라이스 범위

| Parent Design 섹션 | 본 슬라이스 매핑 | 비고 |
|--------------------|-----------------|------|
| §3.1.2 SubAccount.resetDailyUsage() (line 548-550) | §4.2 + §5.3 batch UPDATE | entity 메서드는 이미 존재, batch path만 신규 |
| §9.4 Zombie Reaper (line 2871-2906) | §4.1 + §5.1 + §6.2 + §9 | 클래스 시그니처 / 쿼리 / event / gauge |
```
