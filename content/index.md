---
title: 홈
description: 백엔드 엔지니어링 지식베이스
date: 2026-09-14
---

기록하지 않은 학습은 사라집니다. 여기는 읽고 만들고 디버깅하면서 알게 된 것들을 문장으로 남겨두는 곳입니다.

## 시작점

- [[Backend-MOC|백엔드 MOC]] — 주제별 지도. 여기서 출발하는 게 가장 빠릅니다
- [[writing-guide|작성 규칙]] — 노트 작성 컨벤션
- [[quartz-guide|Quartz 사용법]] — Obsidian ↔ Quartz 사용법

## 어디에 무엇이 있나

| 폴더                      | 내용                                          |
| ------------------------- | --------------------------------------------- |
| `posts/`                  | TIL — 그날 실제로 부딪힌 문제와 배운 것       |
| `etc/spring/`             | Spring 핵심 개념 정리                         |
| `this-is-java/`           | 이것이 자바다 챕터 정리                       |
| `modern_java_in_action/`  | 모던 자바 인 액션 챕터 정리                   |
| `object/`                 | 오브젝트 — 역할·책임·협력, 설계 품질          |
| `CS/Algorithm/`           | 정렬 알고리즘과 시간 복잡도                   |

## 노트 쓰는 흐름

1. Obsidian에서 주제에 맞는 폴더에 새 노트 작성 — TIL이면 `posts/`
2. frontmatter에 `title`, `date`, `tags` 채우기 — `date`가 없으면 커밋일로 잡혀서 최근 노트 순서가 흐트러집니다
3. 관련 노트를 `[[위키링크]]`로 연결하고, [[Backend-MOC|MOC]]에도 한 줄 추가
4. 완성 전이면 `draft: true` — 배포에서 제외됩니다
5. `git push` → GitHub Actions가 자동 배포
