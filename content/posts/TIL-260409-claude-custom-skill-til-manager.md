---
title: "[TIL-260409] Claude Custom Skill 개발 — TIL Manager"
date: 2026-04-09
tags: ["Claude Custom Skill", "MCP", "Notion API", "skill-creator", "Prompt Engineering"]
categories: ["TIL"]
description: "Claude Custom Skill로 TIL 워크플로우 자동화, Notion MCP 연동, Phase 0 범용화, AI 문체 가이드 설계"
---

## 잘한 점

### 상황 1
- Claude.ai에서 매번 TIL 포맷 설명하고, Notion DB 구조 알려주고, "사람처럼 써달라"고 반복하는 게 귀찮았다. 이걸 커스텀 스킬로 만들어서 한 번에 해결하고 싶었다.

### 액션 1
- skill-creator를 활용해서 TIL Manager 스킬을 처음부터 설계했다. SKILL.md(메인 워크플로우) + 4개 reference 파일(til-template, human-writing-guide, frontmatter-spec, notion-setup) 구조로 잡았다. Notion MCP 연동까지 테스트해서 실제로 TIL DB에 페이지가 생성되는 것까지 확인.

### 칭찬 1
- 스킬 설계 → 구현 → Notion 연동 테스트 → 범용화(Phase 0) → 블로그 포스트 작성까지 하루 만에 끝낸 게 좀 뿌듯하다. 반복 작업을 자동화하는 건 역시 개발자의 미덕.

---

## 개선점

### 문제 1
- `.skill` 파일로 패키징했는데, 설치 후 내부 reference 파일들이 안 보이는 이슈가 있었다. 여러 번 재패키징하고 재설치해야 했다.

### 원인 1
- 패키징 과정에서 이전 버전 캐시가 남아있었거나, 설치 시점에 이전 `.skill` 파일을 사용한 것 같다. skill-creator의 패키징 스크립트 동작을 정확히 몰랐던 것도 원인.

### 액션플랜 1
- 스킬 업데이트 시 기존 스킬 삭제 → 새 `.skill` 업로드 순서를 명확히 하자. 설치 후 파일 목록 확인하는 습관 들이기.

---

## 배운 점

### 배움 1
- AI한테 "자연스럽게 써줘"는 안 통한다. "~하였습니다를 ~했다로 바꿔라", "유의미한 대신 구체적 숫자 써라" 같이 구체적인 규칙을 명시해야 톤이 달라진다. 감정 표현 사전("뿌듯하다", "찝찝하다")까지 넣으니까 확실히 나아졌다.

### 의미 1
- 프롬프트 엔지니어링이라는 게 결국 "모호한 요구사항을 구체적 스펙으로 바꾸는 것"이다. 이건 AI 스킬뿐 아니라 주니어 멘토링이나 요구사항 정의할 때도 똑같이 적용되는 원칙.

### 배움 2
- 처음에 Notion DB ID를 스킬에 하드코딩했는데, 다른 사람이 쓸 수 없는 구조였다. Phase 0(자동 설정)을 추가해서 memory 기반으로 설정을 저장하게 바꿨더니, 설치만 하면 바로 사용 가능한 형태가 됐다.

### 의미 2
- `.env`로 환경 변수 분리하는 것과 같은 원리. 혼자 쓸 때는 하드코딩이 편하지만, 공유할 거면 설정은 반드시 외부로 빼야 한다. 스킬에서는 memory가 그 역할을 한다.

---

## 핵심 내용

### 키워드
- `Claude Custom Skill`, `MCP (Model Context Protocol)`, `Notion API`, `notion-create-pages`, `skill-creator`, `.skill 패키징`

### 요약
- Claude Custom Skill은 SKILL.md + references 구조로 반복 워크플로우를 자동화한다. Notion MCP를 통해 DB 페이지 CRUD가 가능하고, date 속성은 `date:{property}:start` 형식으로 전달해야 한다.
- 스킬의 description에 트리거 문구를 구체적으로 넣어야 정확하게 호출된다. API 설계처럼 "사용자가 실제로 뭐라고 말할까"부터 생각하는 게 핵심.

### 코드/명령어
```
# Notion MCP로 TIL DB에 페이지 생성
Notion:notion-create-pages(
  parent: { data_source_id: "2f672cc5-..." },
  pages: [{
    properties: {
      "[1/4]": "[TIL-260409] 제목",
      "date:작성일:start": "2026-04-09",
      "date:작성일:is_datetime": 0
    },
    icon: "✍️",
    content: "TIL 본문 (Notion Markdown)"
  }]
)
```

```
# 스킬 파일 구조
til-manager/
├── SKILL.md                       # 메인 워크플로우
└── references/
    ├── til-template.md            # TIL 템플릿 + 변환 예시
    ├── frontmatter-spec.md        # Git 푸시용 Markdown 포맷
    ├── notion-setup.md            # Notion DB 연결 가이드
    └── human-writing-guide.md     # 사람 톤 가이드
```

### 참고 자료
