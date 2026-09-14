---
title: CS 기초
description: 정렬 알고리즘과 시간 복잡도. 면접용이 아니라 "이 코드가 왜 느린가"를 설명하기 위한 언어.
date: 2026-09-14
---

알고리즘 노트는 2024년 초에 정리한 정렬 다섯 편입니다. 실무에서 정렬을 직접 구현할 일은 없지만, 시간 복잡도라는 언어는 매일 씁니다. [[TIL-260708-explain-cardinality-index|EXPLAIN에서 `type: ALL`을 읽는 것]]도, [[TIL-260703-shared-function-contract-count|COUNT 최적화가 무한루프를 만든 것]]도 결국 O(n)과 O(n²)의 이야기입니다.

## 알고리즘 (`algorithms/`)

- [[time-complexity|시간 복잡도]] — 빅오 표기법, 최선과 최악, 공간 복잡도
- [[bubble-sort|거품 정렬]] · [[selection-sort|선택 정렬]] · [[insertion-sort|삽입 정렬]] — O(n²) 삼형제와 각각의 장단점
- [[merge-sort|병합 정렬]] — 분할 정복, O(n log n)

## 다음에 채울 자리

- 네트워크 — HTTP 기초 정리가 2022년 벨로그에 있지만 MDN 요약 수준이라 옮기지 않았습니다. [[TIL-260602-alb-nginx-xff-client-ip|프록시 뒤 IP 문제]]처럼 실전 맥락이 붙을 때 다시 씁니다
- 자료구조 — 해시와 트리. Redis Sorted Set(skip list)과 InnoDB B+Tree를 이해하는 데 필요한 만큼만
