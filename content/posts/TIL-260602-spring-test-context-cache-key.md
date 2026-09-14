---
title: "[TIL-260602] Spring 통합테스트가 느린 진짜 이유 — ApplicationContext 캐시 키"
date: 2026-06-02
tags: ["Spring Boot", "테스트", "Kotest", "MockK", "ApplicationContext", "성능최적화"]
categories: ["TIL"]
description: "통합 테스트 느림의 원인은 테스트 개수가 아니라 Spring context 부팅 횟수. 캐시 키는 MergedContextConfiguration(슬라이스·@MockkBean·@ActiveProfiles·properties·@Import)으로 결정된다."
---

## 잘한 점

### "1086 통과인데 왜 1분 더?" 끝까지 파봄

**상황**
- 통합 테스트가 1,086개 통과했다고 떴는데 그 뒤로 1분 정도 더 켜져 있었음
- 화면의 4개 Spec은 끝난 것처럼 보이는데 뭔가 계속 도는 느낌

**액션**
- 화면에 깔리는 `Hibernate: set client_min_messages = WARNING` 로그가 단위 테스트가 아니라 병렬로 부팅 중인 `@SpringBootTest` 로그란 걸 확인
- context 캐시 키가 몇 종류인지 직접 분석 (`cache=DEBUG` 켜서 missCount 실측)

**칭찬**
- "그냥 느린가보다" 하고 넘기지 않고 부팅 횟수까지 실측해서 원인을 못 박은 거

---

## 개선점

### @MockkBean 합쳐서 캐시 키 줄이려다 멈춤

**문제**
- 캐시 키를 줄이려고 audit logger 3개를 공통 `@TestConfiguration`의 `@Bean mockk`로 합치려 했음

**원인**
- 확인해보니 3개 spec 다 `verify(exactly=N)`로 호출 횟수를 정밀 검증하고 있었다
- `@MockkBean`은 springmockk가 테스트마다 자동 reset해주는데, 공통 `@Bean mockk`는 안 됨 → 병렬 context 공유 시 카운트 오염
- DailyReset은 자체 `clearMocks`도 없어서 더 위험했음

**액션플랜**
- mock 통합은 안 하기로. verify 카운트 정밀 검증하는 mock은 `@MockkBean` 유지
- 캐시 키를 줄이려면 mock보다 `@ActiveProfiles`/`properties`/`@Import` 표준화부터 손대자

---

## 배운 점

### context 캐시 키 = MergedContextConfiguration

**배움**
- Kotest는 동적 디스커버라 IntelliJ가 전체 테스트 개수를 미리 못 잡는다. 그래서 "1086 통과"가 끝이 아니었음
- 통합 테스트 느림의 진짜 원인은 테스트 개수가 아니라 **Spring context 부팅 횟수**
- 부팅 횟수 = context 캐시 키 종류. 캐시 키는 ①슬라이스 종류 ②`@MockkBean` 조합 ③`@ActiveProfiles` ④`properties` ⑤`@Import`로 결정. 하나라도 다르면 새로 부팅한다

**의미**
- 통합 테스트 빠르게 하려면 어노테이션 조합을 표준화해서 캐시 키 종류를 줄이는 게 정석
- 근데 mock 공유는 상태 오염 리스크가 있어서 무작정 합치면 안 됨. 트레이드오프가 있다

---

## 핵심 내용

### 키워드
- `MergedContextConfiguration`, `ContextCache`, `@MockkBean`, springmockk auto-reset, `LimitedConcurrency`, missCount

### 요약
- Spring TestContext의 context 캐시 키 = `MergedContextConfiguration`. 결정 요소 5가지: 슬라이스 종류(`@SpringBootTest`/`@WebMvcTest`/`@DataJpaTest`), `@MockkBean` 조합, `@ActiveProfiles`, `properties`/`@TestPropertySource`, `@Import`.
- 우리 프로젝트는 48 spec → 약 28종 캐시 키. full `@SpringBootTest` 6종이 부팅 비용을 지배(Hikari+Redisson+JPA+Security 전체).
- `missCount` = 실제 부팅 횟수(핵심 실측치), `hitCount` = 캐시 재사용. `ContextCacheUtils` 기본 상한 32 초과 시 LRU 축출로 재부팅이 더 발생.
- `@MockkBean`(springmockk)은 테스트마다 자동 reset. 공통 `@Bean mockk`로 바꾸면 reset이 안 돼서 병렬 context 공유 시 verify 카운트가 오염된다.

### 코드/명령어
```yaml
# context 캐시 통계 실측 — 부팅 횟수 = missCount
logging.level.org.springframework.test.context.cache: DEBUG
# 로그: Spring test ApplicationContext cache statistics: [missCount=.., hitCount=.., size=..]
```
