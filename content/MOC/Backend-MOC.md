---
title: 백엔드 MOC
tags:
  - moc
description: 백엔드 지식베이스의 주제별 진입점
date: 2026-09-14
---

MOC(Map of Content)는 목차가 아니라 **지도**입니다. 폴더는 파일이 어디 있는지만 알려주지만, 여기서는 무엇과 무엇이 이어지는지를 적습니다.

## 데이터베이스

인덱스와 실행계획, 스토리지 엔진, 트랜잭션.

- [[TIL-260708-explain-cardinality-index|EXPLAIN + 카디널리티로 인덱스 잡기]]
- [[TIL-260708-innodb-buffer-pool-sizing|InnoDB 전환 전 buffer_pool 사이징]]
- [[TIL-260708-myisam-transaction-ignored|MyISAM은 트랜잭션을 조용히 무시한다]]
- [[TIL-260703-codeigniter3-transaction-managed-manual|CodeIgniter3 트랜잭션 managed vs manual]]

## Redis와 정합성

캐시가 아니라 상태 저장소로 쓸 때 생기는 문제들.

- [[TIL-260415-redis-lua-coupon-issue|Redis Lua 선착순 쿠폰 발급 — WRONGTYPE 버그]]
- [[TIL-260416-redis-db-consistency-patterns|Redis-DB 정합성 패턴 5가지]]
- [[TIL-260506-pre-check-save-race-window|사전 체크와 save 사이의 race window]]

## JPA

- [[TIL-260409-kotlin-jpa-entity-pattern|Kotlin JPA Entity 패턴]]
- [[TIL-260422-jpa-auditing-created-by|@CreatedBy 자동 주입 메커니즘]]
- [[TIL-260521-jpa-version-detached-entity|@Version 함정과 detached entity]]
- [[TIL-260602-kotlin-jpa-embeddable-transient|@Embeddable 파생 필드 함정]]

## 도메인 설계

객체지향 원론에서 시작해 DDD 실전까지.

- [[객체지향 패러다임의 핵심 역할(Role) 책임(Responsibility) 협력(Collaboration)|역할 · 책임 · 협력]]
- [[설계 품질과 트레이드오프]]
- [[TIL-260410-ddd-domain-design|DDD 도메인 설계 3원칙]]
- [[TIL-260429-ddd-rich-domain-aggregate-vo|Rich Domain — Aggregate 분리와 금융 VO]]

## 대용량 트래픽

부하를 흡수할 것인가, 거절할 것인가.

- [[TIL-260420-kafka-consumer-peak-load-shifting|Kafka Consumer로 Peak Load Shifting]]
- [[TIL-260425-backpressure-queue-pattern|Backpressure 패턴 — Queue ≠ Rate Limiter]]

## 인증과 보안

- [[TIL-260422-jwt-access-refresh-hybrid|JWT Access+Refresh 하이브리드]]
- [[TIL-260429-aes-gcm-rbac-aop|AES-GCM 컬럼 암호화 + @RequireRole AOP]]
- [[TIL-260602-alb-nginx-xff-client-ip|ALB · nginx 뒤에서 진짜 Client IP 잡기]]

## 테스트

느린 테스트와 거짓 통과를 잡는 법.

- [[TIL-260414-kotest6-describespec-withdata|Kotest 6 DescribeSpec + withData]]
- [[TIL-260414-springmockk-gap-analysis|springmockk와 Gap Analysis]]
- [[TIL-260422-testcontainers-lazy-vs-skip|Testcontainers — Skip 대신 Lazy]]
- [[TIL-260521-pessimistic-write-integration-test|PESSIMISTIC_WRITE 실효성 검증]]
- [[TIL-260602-spring-test-context-cache-key|통합테스트가 느린 진짜 이유]]
- [[TIL-260429-test-infra-fixture-cleanup|테스트 인프라 정비]]

## 관측성과 운영

- [[TIL-260429-mdc-filter-logback-json|MDC 필터로 traceId 일원화]]
- [[TIL-260506-logback-replace-turbofilter|Logback %replace + TurboFilter]]
- [[TIL-260602-profile-vs-feature-toggle|환경 프로필을 기능 토글로 쓰면 안 되는 이유]]

## Spring 기초

- [[Spring Framework가 필요한 이유|Spring이 필요한 이유]]
- [[강한결합과 느슨한결합|강한 결합과 느슨한 결합]]
- [[IoC and DI]]
- [[Spring Container]]
- [[Spring Annotation]]
- [[AOP]]

## Java

- [[TIL-260411-spring-boot-kotlin-patterns|Spring Boot + Kotlin 관용 패턴]]
- [[TIL-260412-kotlin-spring-code-quality|Kotlin/Spring 코드 품질 패턴]]
- [[TIL-260429-swagger-device-id-editorconfig|Swagger X-Device-Id 주입과 .editorconfig]]

### 이것이 자바다

[[this-is-java/ch02/Readme|2. 변수와 타입]] · [[this-is-java/ch03/Readme|3. 연산자]] · [[this-is-java/ch12/Readme|12. java.base 모듈]] · [[this-is-java/ch13/Readme|13. 제네릭]] · [[this-is-java/ch14/Readme|14. 멀티 스레드]] · [[this-is-java/ch15/Readme|15. 컬렉션 자료구조]] · [[this-is-java/ch16/Readme|16. 람다식]] · [[this-is-java/ch17/Readme|17. 스트림과 병렬 처리]]

### 모던 자바 인 액션

[[modern_java_in_action/ch05_스트림_활용/Readme|5. 스트림 활용]] · [[modern_java_in_action/ch06_스트림으로_데이터_수집/Readme|6. 스트림으로 데이터 수집]] · [[modern_java_in_action/ch07_병렬_데이터_처리와_성능/Readme|7. 병렬 데이터 처리와 성능]] · [[modern_java_in_action/ch08_컬렉션_API_개선/Readme|8. 컬렉션 API 개선]] · [[modern_java_in_action/ch09_리팩터링_테스팅_디버깅/Readme|9. 리팩터링, 테스팅, 디버깅]]

## 알고리즘

- [[Time_Complexity|시간 복잡도]]
- [[Bubble_Sort|거품 정렬]] · [[Selection_Sort|선택 정렬]] · [[Insertion_Sort|삽입 정렬]] · [[Merge_Sort|병합 정렬]]

## 일하는 방식

- [[TIL-260425-pdca-1-day-cycle|PDCA 1-day Cycle]]
- [[TIL-260506-slice-design-decision-log|슬라이스 Design 작성법]]
- [[TIL-260412-simplify-skill-doc-dedup|스킬 문서 중복 제거와 정본화]]
- [[TIL-260409-claude-custom-skill-til-manager|Claude Custom Skill 개발]]
