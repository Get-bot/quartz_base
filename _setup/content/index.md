---
title: 홈
description: 백엔드 엔지니어링 지식베이스
---

기록하지 않은 학습은 사라집니다. 여기는 읽고 만들고 디버깅하면서 알게 된 것들을 문장으로 남겨두는 곳입니다.

## 시작점

- [[Backend-MOC|백엔드 MOC]] — 주제별 진입점
- [[writing-guide|작성 규칙]] — 노트 작성 컨벤션
- [[quartz-guide|Quartz 사용법]] — Obsidian ↔ Quartz 사용법

## 노트 쓰는 흐름

1. Obsidian에서 `content/notes/` 에 새 노트 작성
2. frontmatter에 `title`, `tags` 채우기
3. 관련 노트를 `[[위키링크]]` 로 연결
4. 완성 전이면 `draft: true` — 배포에서 제외됨
5. `git push` → GitHub Actions가 자동 배포
