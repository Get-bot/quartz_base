---
title: Spring
description: Spring 핵심 개념부터 Spring Boot 실전 패턴까지. 프레임워크가 대신 해주는 것과 내가 책임져야 하는 것의 경계.
date: 2026-09-14
---

Spring은 "대신 해준다"가 본질입니다. 객체 생성과 조립을 컨테이너가, 횡단 관심사를 프록시가, 트랜잭션 경계를 애노테이션이 맡습니다. 문제는 그 대신 해주는 지점이 눈에 보이지 않는다는 것입니다. 이 폴더의 노트 대부분은 결국 한 질문으로 모입니다. **프레임워크가 여기서 무엇을 하고 있고, 그게 내 의도와 어디서 어긋나는가.**

기초 개념은 `core/`에, 실전에서 부딪힌 것은 바로 아래에 둡니다.

## 핵심 개념 (`core/`)

왜 Spring인지부터 AOP까지, 순서대로 읽으면 하나의 이야기입니다.

- [[why-spring|Spring이 필요한 이유]]
- [[tight-vs-loose-coupling|강한 결합과 느슨한 결합]] — DI가 해결하는 문제를 코드로 먼저 겪어봅니다
- [[ioc-and-di|IoC와 DI]] — 생성자·수정자·필드 주입을 왜 구분하는지
- [[spring-container|Spring Container]] — BeanFactory와 ApplicationContext, Java Bean·POJO·Spring Bean
- [[spring-annotations|Spring Annotation]] — `@Component` vs `@Bean`, `@Primary` vs `@Qualifier`
- [[aop|AOP]]

## 프록시와 포인트컷의 대가

AOP는 공짜가 아닙니다. 어디에 걸리는지 모르면 성능과 정합성을 동시에 잃습니다.

- [[jooq-aop-pointcut-startup-slowdown|jOOQ + AOP 기동 1분 지연]] — `execution` 포인트컷이 DSLContext의 모든 메서드를 매칭하던 문제. 포인트컷은 좁을수록 싸다
- [[TIL-260602-profile-vs-feature-toggle|환경 프로필을 기능 토글로 쓰면 안 되는 이유]] — `@Profile`은 환경, `@ConditionalOnProperty`는 기능. 섞으면 테스트가 환경에 묶인다

## 요청 컨텍스트를 어디에 실을까

파라미터로 끝까지 넘길 것인가, ThreadLocal에 실을 것인가. 한 번 정하면 되돌리기 어려운 결정입니다.

- [[jooq-threadlocal-multitenancy|jOOQ ThreadLocal 멀티테넌시 접근 제어]] — 파라미터 전파를 5분 만에 포기한 이유, 그리고 `finally { clear() }` 한 줄이 보안 사고를 막는 이유
- [[TIL-260422-jpa-auditing-created-by|@CreatedBy 자동 주입 메커니즘]] — SecurityContextHolder → AuditorAware → `@CreatedBy`. 트리거는 필드명이 아니라 애노테이션
- 같은 문제를 다른 층에서 푼 예: [[replication-lag-write-concern|Write-Concern 라우팅]](데이터베이스), [[TIL-260429-mdc-filter-logback-json|MDC 필터]](관측성)

## Kotlin과 함께 쓸 때

- [[TIL-260411-spring-boot-kotlin-patterns|Spring Boot + Kotlin 관용 패턴]] — Bean Validation의 null 처리, one-indexed 파라미터 비대칭, Testcontainers 수명
- [[TIL-260412-kotlin-spring-code-quality|Kotlin/Spring 코드 품질 패턴]] — enum 전방 참조와 `by lazy`
- [[TIL-260429-swagger-device-id-editorconfig|Swagger X-Device-Id 자동 주입과 .editorconfig]]

## 다음에 채울 자리

- `@Transactional` 전파와 self-invocation — 트랜잭션 경계가 어긋나는 사례가 [[redis-lua-first-come-coupon|Redis Lua 선착순 쿠폰]]과 [[TIL-260416-redis-db-consistency-patterns|Redis-DB 정합성 패턴]]에 흩어져 있다. 한 노트로 모을 것
- Spring Boot 4 / Spring Kafka 4로 올리며 깨진 API 목록 — [[TIL-260420-kafka-consumer-peak-load-shifting|Kafka Peak Load Shifting]]의 개선점에 첫 기록이 있다
