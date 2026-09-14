---
title: 동시성과 대용량 트래픽
description: 선착순 쿠폰 시스템 하나를 DB 락 → Redis Lua → Kafka → 대기열로 밀어올리며 배운 동시성 제어와 부하 흡수 전략.
date: 2026-09-14
---

이 폴더는 하나의 시스템에서 나왔습니다. **선착순 쿠폰 발급.** 요구사항은 한 줄이지만 "동시에 1만 명이 1천 장을 두고 경쟁한다"는 조건이 붙으면 락을 어디에 둘지, 실패를 어떻게 되돌릴지, 부하를 거절할지 지연시킬지가 전부 설계 결정이 됩니다.

노트를 쓴 순서가 곧 사고의 순서입니다. 락의 위치가 **DB 행 → Redis 명령 → 시간축 → 대기열**로 바깥으로 밀려나갑니다. 각 단계는 앞 단계의 병목을 풀지만 새 실패 모드를 들여옵니다.

## 1. 락을 DB에서 Redis로

DB row lock은 정확하지만 줄을 세웁니다. 커넥션 풀이 먼저 마릅니다.

- [[redis-lua-first-come-coupon|Redis Lua로 선착순 쿠폰 발급 만들기]] — 전체 그림. "개별 명령은 원자적이지만 조합은 아니다", `@Transactional` 범위를 쪼개야 하는 이유, 실패 유형별 보상 전략, 이중 래치 테스트
- [[TIL-260415-redis-lua-coupon-issue|WRONGTYPE 버그와 PDCA 검증]] — 같은 작업의 당일 기록. 키 타입은 생성 시점에 고정된다, 매진은 409가 아니라 410
- [[TIL-260416-redis-db-consistency-patterns|Redis-DB 정합성 패턴 5가지]] — Redis는 성공했는데 DB가 실패하면. deferred flush, readOnly 전파, UK-aware 보상

## 2. 쓰기 피크를 시간축으로

Redis로 재고는 지켰지만 DB INSERT가 피크에 무너집니다. 총량은 못 줄이니 펴야 합니다.

- [[TIL-260420-kafka-consumer-peak-load-shifting|Kafka Consumer로 Peak Load Shifting]] — 멱등성을 Consumer 로직이 아니라 메시지(pre-gen UUID v7)에 심는다. 영원히 실패할 예외는 retry에서 뺀다

## 3. 거절할 것인가, 기다리게 할 것인가

Rate Limiter는 공정하지만 429를 돌려줍니다. 대기열은 200과 순번을 돌려줍니다.

- [[TIL-260425-backpressure-queue-pattern|Backpressure 패턴 — Queue ≠ Rate Limiter]] — Sorted Set 대기열로 5만 동시 요청 평탄화. ZPOPMIN의 destructive 특성이 남기는 유실 위험과 Redis Streams라는 다음 단계

## 4. 락이 정말 잡히는가

- [[TIL-260506-pre-check-save-race-window|사전 체크와 save 사이의 race window]] — "확인하고 저장"에는 언제나 틈이 있다. 최후 방어선은 UNIQUE 제약
- [[TIL-260521-pessimistic-write-integration-test|PESSIMISTIC_WRITE 실효성 검증]] — 클래스 레벨 `@Transactional`이 만들던 가짜 그린. 락 테스트는 mutation testing처럼

## 반복해서 나오는 원칙

- **원자성의 경계를 먼저 그린다.** Redis 명령 하나, Lua 블록 하나, DB 트랜잭션 하나. 경계 밖은 보상으로 메운다
- **보상은 실패 유형별로 다르다.** UK 위반과 네트워크 오류를 같은 방식으로 되돌리면 데이터가 어긋난다
- **동시성 테스트는 동시에 출발시켜야 한다.** 스레드를 만드는 것과 동시에 실행하는 것은 다르다

## 다음에 채울 자리

- Redis Streams(`XREADGROUP` + PEL)로 대기열 유실 문제 닫기
- 분산 락(Redisson)과 Lua 원자 블록의 선택 기준 — 언제 락이 필요하고 언제 원자 연산으로 충분한가
