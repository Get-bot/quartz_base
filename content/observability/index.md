---
title: 관측성
description: 로그가 문제를 말해주게 만드는 일. traceId 일원화, 구조화 로깅, 노이즈 차단.
date: 2026-09-14
---

장애가 났을 때 첫 질문은 "이 요청이 어디까지 갔나"입니다. 그 질문에 로그가 답하려면 요청 하나를 꿰는 식별자가 있어야 하고, 사람이 아니라 기계가 읽을 수 있는 형식이어야 하고, 정작 필요한 줄이 노이즈에 묻히지 않아야 합니다. 이 폴더는 그 세 조건을 하나씩 채운 기록입니다. 아직 두 편이지만 운영 경험이 쌓일수록 가장 빨리 자라날 자리입니다.

## traceId와 구조

- [[TIL-260429-mdc-filter-logback-json|전역 MDC 필터로 traceId 일원화 + JSON 구조화 로깅]] — MDC 필터를 **가장 바깥**에 둬야 인증 실패 로그에도 traceId가 남는다. logstash-logback-encoder로 JSON, BaseAuditLogger로 감사 로그 추상화

## 노이즈

- [[TIL-260506-logback-replace-turbofilter|Logback %replace + TurboFilter]] — Outbox 폴러의 SQL 로그를 스레드 단위로 정밀 차단. 빈 MDC 토큰은 `%replace`로 숨김

## 연결되는 곳

- MDC와 같은 ThreadLocal 계열 해법을 다른 목적으로 쓴 사례: [[jooq-threadlocal-multitenancy|멀티테넌시 접근 제어]], [[replication-lag-write-concern|Write-Concern 라우팅]]
- 어떤 로그를 남길지는 보안 설계와 겹칩니다: [[TIL-260422-jwt-access-refresh-hybrid|JWT 하이브리드]]의 Replay 탐지 로그(IP/UA/timestamp)

## 다음에 채울 자리

- 메트릭 — 로그만 있고 숫자가 없다. HikariCP 풀 대기, Kafka consumer lag, Redis 대기열 길이부터
- 분산 트레이싱 — Kafka를 넘어가는 순간 traceId가 끊긴다. Consumer까지 이어 붙이기
