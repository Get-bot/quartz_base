---
title: 일하는 방식
description: 설계 문서를 먼저 쓰는 습관과 PDCA 사이클. 결정의 이유를 남기는 법.
date: 2026-09-14
---

2026년부터 코드부터 치지 않습니다. Plan → Design → 구현 → Check를 돌리고, 문서와 구현의 차이를 Match Rate로 잽니다. 이 폴더는 그 방식이 **실제로 무엇을 바꿨고 어디서 삐끗했는지**의 기록입니다. 도구(Claude Code, 플러그인, CLAUDE.md) 이야기는 [[ai/index|AI와 일하기]]로 뺐고, 여기엔 도구가 없어도 남는 것만 둡니다.

## 설계 문서를 먼저 쓴다

- [[TIL-260425-pdca-1-day-cycle|PDCA 1-day Cycle과 Design Self-Inconsistency]] — 5개 feature를 적층해 마지막은 하루에 완주. Match Rate 99%여도 design 문서 자체가 모순일 수 있다
- [[TIL-260506-slice-design-decision-log|슬라이스 Design 작성법]] — Parent를 손대지 않고 매핑·갭·Decision Log 세 가지 책임으로 좁게 쓴다

## 반복해서 나오는 원칙

- 검증(Check)은 양방향이다. 구현이 설계를 따랐는지만이 아니라 설계가 스스로 일관적인지도
- "왜"는 Decision Log 한 줄에. 본문에는 "어떻게"만. 두 책임을 섞으면 문서가 늘어진다
- 새 feature의 속도는 **기존 자원 재사용도 × 신규 코드 격리도**의 함수다. 5번째 feature가 하루에 끝난 이유

## 연결되는 곳

- 이 방식을 SDLC 전체로 넓혀 보면 [[ai-native-sdlc-playbook|AI-Native SDLC 플레이북]]의 intent → spec → plan 산출물 체인과 거의 겹칩니다. Decision Log는 거기 없는 내 추가

## 다음에 채울 자리

- 설계 문서가 구현보다 먼저 낡는 문제 — Match Rate가 높아도 Decision Log가 갱신되지 않으면 문서는 거짓말을 시작한다
- TIL은 매일 쌓이는데 주 단위로 묶어 돌아보는 기록이 없다
