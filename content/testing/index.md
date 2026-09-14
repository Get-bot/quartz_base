---
title: 테스트
description: 느린 테스트와 거짓 통과를 잡는 법. 테스트 프레임워크 선택보다 "무엇이 진짜 검증되고 있는가"가 반복되는 질문.
date: 2026-09-14
---

테스트 노트에서 가장 많이 등장하는 단어는 "**가짜 그린**"입니다. 통과했지만 아무것도 증명하지 못한 테스트. 클래스 레벨 `@Transactional`이 락 경쟁을 없애버리거나, Docker가 없으면 조용히 skip되거나, 인자 매칭이 실패해 `thenThrow`가 발동하지 않는 경우들. 두 번째로 많은 단어는 "**느림**"인데, 원인은 대개 테스트 개수가 아니라 컨텍스트 부팅 횟수였습니다.

## 프레임워크와 도구

- [[TIL-260414-kotest6-describespec-withdata|Kotest 6 DescribeSpec + withData]] — 테이블 드리븐으로 도메인 테스트 쓰기
- [[TIL-260414-springmockk-gap-analysis|springmockk와 Gap Analysis]] — MockK DSL 통일, 설계 문서 대비 누락 테스트 찾기
- [[TIL-260429-test-infra-fixture-cleanup|테스트 인프라 정비]] — Fixture 공통화, 96줄 DbCleanupListener 삭제

## 느린 테스트의 진짜 원인

- [[TIL-260602-spring-test-context-cache-key|통합테스트가 느린 진짜 이유]] — 캐시 키는 MergedContextConfiguration. 슬라이스·`@MockkBean`·`@ActiveProfiles`·properties·`@Import` 중 하나만 달라도 새로 부팅한다. 단, mock을 공유하면 verify 카운트가 오염된다는 트레이드오프
- [[TIL-260422-testcontainers-lazy-vs-skip|Skip 대신 Lazy]] — Kotlin `object`는 클래스 로딩 시 init이 돈다. 조건부 skip은 False Positive를 만든다

## 가짜 그린

- [[TIL-260521-pessimistic-write-integration-test|PESSIMISTIC_WRITE 실효성 검증]](동시성) — 락이 잡히는지 증명하려면 트랜잭션을 테스트 밖으로 밀어내야 한다
- [[mockmvc-argument-matching|MockMvc 인자 매칭 오류]] — 2023년 기록. equals가 다르면 stub은 조용히 무시된다
- [[redis-lua-first-come-coupon|이중 래치 동시성 테스트]](동시성) — 스레드를 만드는 것과 동시에 출발시키는 것은 다르다. 실패한 테스트의 스레드 풀이 다음 테스트를 오염시킨 이야기도

## 반복해서 나오는 원칙

- 테스트가 "환경에 따라" 다르게 동작하면 그 테스트는 없는 것과 같다 (Strict Parity)
- 검증 대상이 락·트랜잭션·동시성이면, 테스트 자체가 그 메커니즘을 바꾸고 있지 않은지 먼저 본다
- 통합 테스트 속도는 어노테이션 조합의 표준화 문제다

## 다음에 채울 자리

- 테스트 계층(L1 Domain → L4 Integration) 정의를 한 노트로 — 지금은 여러 TIL에 흩어져 있다
- 계약 테스트 — Kafka 메시지 스키마가 바뀔 때 Producer와 Consumer를 함께 깨뜨리는 방법
