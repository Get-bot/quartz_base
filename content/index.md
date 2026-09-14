---
title: 홈
description: 백엔드 엔지니어링 지식베이스
date: 2026-09-14
---

기록하지 않은 학습은 사라집니다. 여기는 읽고 만들고 디버깅하면서 알게 된 것들을 문장으로 남겨두는 곳입니다.

## 시작점

- [[Backend-MOC|백엔드 MOC]] — 폴더를 가로지르는 지도. 처음이면 여기서
- [[writing-guide|작성 규칙]] — 노트 작성 컨벤션
- [[quartz-guide|Quartz 사용법]] — Obsidian ↔ Quartz

## 영역

- **[[spring/index|Spring]]** `spring/` — 핵심 개념(`core/`)과 Spring Boot 실전 패턴
- **[[database/index|데이터베이스]]** `database/` — MySQL/MariaDB 엔진·인덱스·복제, JPA 함정(`jpa/`)
- **[[concurrency/index|동시성과 대용량 트래픽]]** `concurrency/` — 선착순 쿠폰 시스템으로 배운 Redis Lua, Kafka, Backpressure
- **[[security/index|인증과 보안]]** `security/` — JWT, OAuth2 시리즈(`oauth2/`), 암호화, 프록시 뒤 IP
- **[[testing/index|테스트]]** `testing/` — Kotest, Testcontainers, 컨텍스트 캐시, 가짜 그린
- **[[architecture/index|설계]]** `architecture/` — DDD, 디자인 패턴 적용 사례
- **[[observability/index|관측성]]** `observability/` — MDC, Logback 구조화 로깅
- **[[workflow/index|일하는 방식]]** `workflow/` — PDCA, 설계 문서, Claude Code
- **[[books/index|책]]** `books/` — 이것이 자바다, 모던 자바 인 액션
- **[[cs/index|CS 기초]]** `cs/` — 정렬 알고리즘, 시간 복잡도

## 노트 쓰는 흐름

1. 주제에 맞는 영역 폴더에 노트를 만듭니다. TIL도 별도 폴더 없이 해당 영역에 바로 둡니다 (`TIL-YYMMDD-slug.md`)
2. frontmatter에 `title`, `date`, `tags`, `description`을 채웁니다. `date`가 없으면 커밋일로 잡혀 최근 노트 순서가 흐트러집니다
3. 관련 노트를 `[[위키링크]]`로 연결하고, 영역 폴더의 첫 페이지(`index.md`)에 한 줄 추가합니다. 영역을 가로지르는 이야기면 [[Backend-MOC|MOC]]에도
4. 완성 전이면 `draft: true` — 배포에서 제외됩니다
5. `git push` → GitHub Actions가 자동 배포
