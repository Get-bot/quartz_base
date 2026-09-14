---
title: 백엔드 MOC
tags: ["moc"]
description: 폴더를 가로지르는 지도. 하나의 문제가 여러 영역을 어떻게 관통하는지.
date: 2026-09-14
---

폴더는 노트가 **어디 있는지**를, 이 지도는 노트가 **어떻게 이어지는지**를 보여줍니다. 영역별 입구는 각 폴더의 첫 페이지에 있고, 여기서는 폴더를 가로지르는 실 몇 가닥을 따라갑니다.

## 영역별 입구

- [[spring/index|Spring]] — 프레임워크가 대신 해주는 것과 내가 책임질 것의 경계
- [[database/index|데이터베이스]] — 엔진·인덱스·복제, 그리고 JPA가 얹는 추상화의 함정
- [[concurrency/index|동시성과 대용량 트래픽]] — 선착순 쿠폰 시스템으로 배운 락·보상·부하 흡수
- [[security/index|인증과 보안]] — 토큰을 어디에 두고 누구를 믿을 것인가
- [[testing/index|테스트]] — 느린 테스트와 가짜 그린
- [[architecture/index|설계]] — 경계를 어디에 그을 것인가
- [[observability/index|관측성]] — 로그가 문제를 말해주게 하기
- [[workflow/index|일하는 방식]] — 설계 문서 먼저, AI는 팀원처럼
- [[books/index|책]] — 이것이 자바다, 모던 자바 인 액션
- [[cs/index|CS 기초]] — 정렬과 시간 복잡도

## 실 1 — 락은 바깥으로 밀려난다

선착순 쿠폰 시스템 한 편의 이야기. 병목이 발견될 때마다 락의 위치가 한 겹 바깥으로 이동합니다.

1. DB row lock이 커넥션 풀을 말린다 → [[redis-lua-first-come-coupon|Redis Lua 원자 블록]] (동시성)
2. Redis는 지켰는데 DB INSERT가 피크에 무너진다 → [[TIL-260420-kafka-consumer-peak-load-shifting|Kafka로 시간축 분산]] (동시성)
3. 그래도 5만 명이 동시에 오면 → [[TIL-260425-backpressure-queue-pattern|대기열, 거절 대신 지연]] (동시성)
4. 각 단계마다 "정말 안전한가"를 증명해야 했다 → [[TIL-260521-pessimistic-write-integration-test|락 실효성 테스트]] (동시성), [[TIL-260422-testcontainers-lazy-vs-skip|Strict Parity]] (테스트)
5. 그리고 매 단계는 하루짜리 PDCA로 → [[TIL-260425-pdca-1-day-cycle|1-day Cycle]] (일하는 방식)

## 실 2 — 요청 컨텍스트는 어디에 실리는가

"이 요청은 누구의 것이고 무엇을 했는가"를 파라미터로 끝까지 넘기지 않고 ThreadLocal에 싣는 결정을 여러 번 했습니다. 같은 도구, 다른 목적, 같은 함정(`finally { clear() }`, `@Async`에 전파되지 않음).

- 접근 권한 → [[jooq-threadlocal-multitenancy|jOOQ 멀티테넌시]] (Spring)
- 최근 쓰기 여부 → [[replication-lag-write-concern|Write-Concern 라우팅]] (데이터베이스)
- 추적 식별자 → [[TIL-260429-mdc-filter-logback-json|MDC traceId]] (관측성)
- 인증 주체 → [[TIL-260422-jpa-auditing-created-by|@CreatedBy와 SecurityContextHolder]] (Spring)

## 실 3 — 조용한 실패

에러를 내지 않아서 더 위험한 것들.

- MyISAM은 트랜잭션을 무시하고 성공을 돌려준다 → [[TIL-260708-myisam-transaction-ignored|MyISAM]]
- Spring Data의 `@Version`은 락을 걸지 않고도 컴파일된다 → [[TIL-260521-jpa-version-detached-entity|@Version 함정]]
- `@Embeddable`의 init 블록은 no-arg 재로드에서 돌지 않는다 → [[TIL-260602-kotlin-jpa-embeddable-transient|@Embeddable 파생 필드]]
- Mockito stub은 인자가 다르면 아무 말 없이 무시된다 → [[mockmvc-argument-matching|MockMvc 인자 매칭]]
- 조건부 skip은 통과처럼 보인다 → [[TIL-260422-testcontainers-lazy-vs-skip|Skip 대신 Lazy]]
- P6Spy는 라우팅 DataSource를 감싸 Master로만 보낸다 → [[replication-lag-write-concern|Write-Concern 패턴]]

## 실 4 — 패턴을 꺼낸 시점과 이유

- 순차 검사·중단 → Chain of Responsibility, Strategy 아님 → [[chain-of-responsibility-fraud-detection|이상거래 감지]]
- Provider별 분기 → Strategy → [[02-multi-provider-strategy-pattern|OAuth2 멀티 Provider]]
- 응답 파서 선택 → Factory → [[03-user-info-factory-pattern|Provider별 응답 파싱]]
- 도메인 경계 → Aggregate 분리, VO 추출 → [[TIL-260410-ddd-domain-design|DDD 3원칙]], [[TIL-260429-ddd-rich-domain-aggregate-vo|Rich Domain]]

## 실 5 — Stateless와 Stateful 사이

- Access는 서명만, Refresh는 저장소 → [[TIL-260422-jwt-access-refresh-hybrid|JWT 하이브리드]]
- OAuth2 진행 상태는 세션 대신 쿠키 → [[04-cookie-based-state-csrf-spa|쿠키 기반 상태]]
- 그 쿠키를 프록시 뒤에서 IP와 함께 믿으려면 → [[TIL-260602-alb-nginx-xff-client-ip|진짜 Client IP]]
