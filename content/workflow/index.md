---
title: 일하는 방식
description: 설계 문서를 먼저 쓰는 습관, PDCA 사이클, AI 도구를 팀원처럼 쓰는 법과 그 함정.
date: 2026-09-14
---

2026년부터 개발 흐름이 바뀌었습니다. 코드부터 치지 않고 Plan → Design → 구현 → Check를 돌리고, 문서와 구현의 차이를 Match Rate로 재고, Claude Code를 페어 프로그래머로 씁니다. 이 폴더는 그 방식이 **실제로 무엇을 바꿨고 어디서 삐끗했는지**의 기록입니다. 도구 사용법이 아니라 도구가 만든 습관에 관한 노트들입니다.

## 설계 문서를 먼저 쓴다

- [[TIL-260425-pdca-1-day-cycle|PDCA 1-day Cycle과 Design Self-Inconsistency]] — 5개 feature를 적층해 마지막은 하루에 완주. Match Rate 99%여도 design 문서 자체가 모순일 수 있다
- [[TIL-260506-slice-design-decision-log|슬라이스 Design 작성법]] — Parent를 손대지 않고 매핑·갭·Decision Log 세 가지 책임으로 좁게 쓴다

## AI를 도구로, 도구를 문서로

- [[claude-code-plugins-review|Claude Code 플러그인 18개 후기]] — 워크플로우 플러그인은 하나만, LSP는 내 스택만, 권한 화이트리스트는 프로젝트 시작할 때
- [[TIL-260409-claude-custom-skill-til-manager|Claude Custom Skill 개발 — TIL Manager]] — 이 지식베이스의 TIL이 만들어지는 파이프라인
- [[TIL-260412-simplify-skill-doc-dedup|스킬 문서 중복 제거와 정본화]] — 문서에도 Single Source of Truth
- [[TIL-260708-wsl-mysql-mcp-unc-path|Windows + WSL MySQL MCP UNC 경로 함정]]

## 반복해서 나오는 원칙

- 검증(Check)은 양방향이다. 구현이 설계를 따랐는지만이 아니라 설계가 스스로 일관적인지도
- 도구는 시스템 프롬프트를 먹는다. 안 쓰는 플러그인은 비용이다
- 외부 라이브러리는 **해석된 실제 버전 → 공식 문서 → 블로그** 순서로 본다 ([[TIL-260420-kafka-consumer-peak-load-shifting|Spring Kafka 4.x 삽질]]에서)

## 다음에 채울 자리

- 설계 문서가 구현보다 먼저 낡는 문제 — Match Rate가 높아도 Decision Log가 갱신되지 않으면 문서는 거짓말을 시작한다
