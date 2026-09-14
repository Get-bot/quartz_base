---
title: "[TIL-260412] Claude Code /simplify로 스킬 문서 중복 제거 및 정본화"
date: 2026-04-12
tags: ["Claude Code", "simplify", "Single Source of Truth", "문서 리팩토링"]
categories: ["TIL"]
description: "/simplify 3-agent 병렬 리뷰로 til-manager 스킬 문서 중복 6건 발견, reference 정본화 패턴 적용"
---

## 잘한 점

### /simplify 3-agent 병렬 리뷰로 문서 중복 6건 발견

**상황**
- til-manager 스킬을 며칠에 걸쳐 기능 추가하다 보니 SKILL.md가 점점 뚱뚱해짐
- reference 파일로 분리한 내용이 SKILL.md에도 그대로 남아 있어서 같은 규칙이 2~3곳에 중복
- 어디가 정본인지 모호해지면 나중에 하나만 고치고 다른 곳은 안 고치는 drift가 생긴다

**액션**
- Claude Code /simplify 스킬로 Code Reuse / Code Quality / Efficiency 3개 에이전트를 병렬 실행
- 6건의 중복·비효율 발견: Notion MCP 코드블록, 문체 가이드, slug 규칙, 커밋 형식, 하드코딩 URL, trailing newline
- 각 reference 파일을 "유일한 정본(single source of truth)"으로 지정하고, SKILL.md는 포인터만 남김

**칭찬**
- 문서도 코드처럼 리팩토링 대상이라는 걸 의식적으로 실천한 점
- 3-agent 병렬 리뷰가 꽤 효과적이었다 — 혼자 읽었으면 slug 3곳 중복은 놓쳤을 듯

---

## 개선점

### SKILL.md가 글로벌 스킬과 로컬 스킬 두 벌로 존재

**문제**
- 글로벌 설치된 스킬(`~/.claude/skills/`)과 로컬 레포(`D:/claude-toolkit/`)의 SKILL.md가 따로 논다
- 글로벌 쪽은 이전 버전 그대로라 /simplify에서 수정한 내용이 실제 스킬 실행 시 반영 안 됨

**원인**
- skills CLI로 글로벌 설치한 뒤 로컬에서만 수정하고 글로벌에 sync를 안 함
- 배포 파이프라인이 없어서 수동으로 복사해야 하는 구조

**액션플랜**
- 로컬 수정 후 글로벌에 반영하는 워크플로우 정리 필요
- 또는 심볼릭 링크로 한 벌만 유지하는 방법 검토

---

## 배운 점

### Single Source of Truth 패턴은 문서에도 적용된다

**배움**
- 코드에서 DRY 원칙 지키듯, 스킬 문서도 같은 규칙이 여러 파일에 있으면 drift가 생긴다
- "정본 파일 + 포인터" 패턴이 깔끔하다 — SKILL.md는 "뭘 해야 하는지", reference는 "어떻게 하는지"
- /simplify의 3-agent 병렬 리뷰가 사람 눈으로 놓치기 쉬운 cross-file 중복을 잘 잡아냈다

**의미**
- 스킬 문서가 커질수록 정본 관리가 중요해진다
- 새 reference 파일을 만들 때 "이 내용의 정본은 어디인가?"를 먼저 확인하는 습관이 필요

---

## 핵심 내용

### 키워드
- `Single Source of Truth`, `/simplify`, `3-agent parallel review`, `reference 정본화`

### 요약
- /simplify는 Code Reuse, Code Quality, Efficiency 3개 에이전트를 병렬로 돌려서 변경사항을 리뷰한다.
- 문서 리팩토링에서도 "정본 파일 + 포인터" 패턴이 유효하다. SKILL.md(항상 로드됨)는 최소 지시만, 상세는 reference 파일에.
- frontmatter-spec.md를 slug/파일명 규칙의 유일한 정본으로 지정. SKILL.md에서 slug 관련 인라인 설명 전부 제거.

### 적용한 변경
- SKILL.md 문체 가이드 13줄 → 4줄 (Quick Reference 포인터)
- SKILL.md slug 규칙 2곳 → frontmatter-spec.md 참조 포인터
- frontmatter-spec.md에 slug 생성 규칙 보강 (변환 테이블 추가)
- notion-setup.md 하드코딩 DB 정보 → 동적 메모리 기반 설정
- PR: Get-bot/claude-toolkit#10
