---
title: 데이터베이스
description: 스토리지 엔진, 인덱스와 실행계획, 리플리케이션, 그리고 JPA가 DB 위에 얹는 추상화의 함정.
date: 2026-09-14
---

데이터베이스 노트는 두 종류입니다. 하나는 **DB 자체**가 하는 일(엔진, 인덱스, 복제), 다른 하나는 **JPA가 DB를 대신 다루면서** 생기는 어긋남입니다. 둘의 공통점은 문제가 조용히 생긴다는 것입니다. MyISAM은 트랜잭션을 무시하면서 에러를 내지 않고, Spring Data의 `@Version`은 이름만 같을 뿐 락을 걸지 않으며, 리플리카는 몇백 ms 늦을 뿐 틀린 값을 주지는 않습니다. 그래서 이 폴더의 결론은 대부분 "**믿지 말고 확인하라**"로 끝납니다. `SHOW INDEX`로, `EXPLAIN`으로, 테스트로.

## 엔진과 트랜잭션

레거시 MariaDB를 만지며 배운 것들. 프레임워크가 트랜잭션을 시작해도 엔진이 받아주지 않으면 없는 것과 같습니다.

- [[TIL-260708-myisam-transaction-ignored|MyISAM은 트랜잭션을 조용히 무시한다]] — orphan 결제건의 원인
- [[TIL-260708-innodb-buffer-pool-sizing|InnoDB 전환 전 buffer_pool 사이징]] — 엔진 전환은 메모리 계획과 함께
- [[TIL-260703-codeigniter3-transaction-managed-manual|CodeIgniter3 트랜잭션 managed vs manual]] — 혼용 상태에서 rollback만 빼면 오히려 악화된다

## 인덱스와 실행계획

- [[TIL-260708-explain-cardinality-index|EXPLAIN + 카디널리티로 인덱스 잡기]] — `type: ALL`이면 풀스캔. 주석에 적힌 인덱스는 존재 증명이 아니다

## 읽기/쓰기 분리

- [[replication-lag-write-concern|리플리케이션 지연과 Write-Concern 패턴]] — "방금 쓴 사람은 잠시 Master를 보게 하자". ThreadLocal·Request·Cookie 3계층 추적, 그리고 P6Spy가 라우팅을 통째로 무력화한 이야기

## JPA가 DB 위에 얹는 것 (`jpa/`)

JPA는 편리한 만큼 DB와의 거리가 멉니다. 그 거리에서 생기는 버그들.

- [[TIL-260409-kotlin-jpa-entity-pattern|Kotlin JPA Entity 패턴]] — 주 생성자 + protected set, allOpen, kotlin.time과 java.time
- [[TIL-260521-jpa-version-detached-entity|@Version 함정과 detached entity]] — `jakarta.persistence.Version`만 낙관적 락이다. Spring Data의 동명 애노테이션은 silent bug
- [[TIL-260602-kotlin-jpa-embeddable-transient|@Embeddable 파생 필드 함정]] — kotlin-noarg는 init 블록을 돌리지 않는다

## 연결되는 곳

- Redis와 DB 사이의 정합성은 [[concurrency/index|동시성]]에서 다룹니다 — [[TIL-260416-redis-db-consistency-patterns|Redis-DB 정합성 패턴 5가지]], [[TIL-260506-pre-check-save-race-window|사전 체크와 save 사이의 race window]]
- 락이 실제로 잡히는지 검증하는 법: [[TIL-260521-pessimistic-write-integration-test|PESSIMISTIC_WRITE 실효성 검증]]

## 다음에 채울 자리

- PostgreSQL과 MySQL의 락 동작 차이 — 같은 `SELECT … FOR UPDATE`가 다르게 행동하는 지점
- 커넥션 풀 사이징 — HikariCP 기본 10개가 병목이 된 기록이 [[redis-lua-first-come-coupon|Redis Lua 선착순 쿠폰]]에 있다. 숫자를 정하는 기준을 따로 정리할 것
