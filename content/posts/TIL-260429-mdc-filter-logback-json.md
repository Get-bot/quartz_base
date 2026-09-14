---
title: "[TIL-260429] 전역 MDC 필터로 traceId 일원화 + Logback JSON 구조화 로깅"
date: 2026-04-29
tags: ["Logback", "MDC", "Spring Security", "Observability", "JSON 로깅", "Kotlin"]
categories: ["TIL"]
description: "MdcContextFilter를 가장 바깥에 배치해 인증 실패 로그까지 traceId 보장, logstash-logback-encoder로 JSON 구조화, BaseAuditLogger 추상화"
---

## 잘한 점

### MdcContextFilter 신설 — JwtAuthenticationFilter 앞 배치

**상황**
- 그동안 MDC(traceId / memberId) 주입과 clear가 `JwtAuthenticationFilter` 안에 들어 있었음
- 인증 실패하는 요청은 traceId 없이 로그가 남거나, 더 안 좋게는 이전 요청의 MDC 값이 남는 케이스가 의심됨
- 출금 같은 도메인은 "인증 실패 자체"도 추적해야 하는 이벤트라서 traceId 누락이 곤란

**액션**
- `global/web/MdcContextFilter` 신규 추가 — 요청 진입 시 traceId(UUID) + memberId 주입, 응답 후 `MDC.clear()`
- SecurityConfig에서 `MdcContextFilter`를 `JwtAuthenticationFilter` **앞**에 등록 → 인증이 실패해도 MDC는 무조건 채워진 상태
- `JwtAuthenticationFilter`의 `finally { MDC.clear() }` 제거 — clear 책임을 가장 바깥 필터로 이전

**칭찬**
- "필터 책임 분리"라는 평범한 개선이지만 인증 실패 로그까지 traceId가 따라붙게 만든 건 운영 들어가면 진짜 도움 되는 변화

---

### Logback + logstash-logback-encoder JSON 구조화 로깅

**상황**
- 로그가 사람 읽기용 텍스트 포맷이라 ELK·CloudWatch에서 `traceId`로 필터링하려면 정규식부터 짜야 했음
- 운영 들어가면 traceId·memberId·eventType 키로 검색이 일상

**액션**
- `logstash-logback-encoder` 의존성 추가 + `build.gradle.kts`에 버전 변수로 추출
- `logback-spring.xml`에 JSON 인코더 등록 → 모든 로그가 한 줄 JSON으로
- `application.yaml`에서 의미 없어진 `custom-js` 설정 정리

---

### `BaseAuditLogger<T>` 추상화로 AuthAuditLogger 중복 제거

**상황**
- 출금 노티 도메인 들어가면 감사 로거가 도메인마다 늘어날 예정
- `AuthAuditLogger`를 보면 KotlinLogging 세팅·`eventType` + `payload` 직렬화 패턴이 매번 반복될 모양

**액션**
- `global/audit/BaseAuditLogger<T>` 추상 클래스 — KotlinLogging 기반, `eventType` + `payload` 구조화 로깅
- `AuthAuditLogger`를 상속으로 전환 → 본문 거의 0줄
- `AuthAuditEvent.occurredAt` 제거 — 로그 자체 timestamp랑 중복이라 의미 없음

---

## 개선점

### MDC clear 책임이 안쪽 필터에 있던 게 위험했음

**문제**
- `JwtAuthenticationFilter.finally { MDC.clear() }` 패턴은 "이 필터를 통과한 경우"에만 안전 — 그 앞에서 예외 터지면 MDC가 다음 요청으로 새는 잠재적 버그
- 스레드풀 재사용 환경에서 이게 진짜 문제로 나타남

**원인**
- 처음 만들 때 "인증 끝나는 지점에서 정리하면 되겠지" 식으로 짠 게 누적
- 요청 단위 컨텍스트는 가장 바깥 필터에서 관리해야 한다는 원칙을 늦게 적용

**액션플랜**
- 요청-스코프 자원 (MDC, RequestId, 트랜잭션 외 컨텍스트) 은 **항상 가장 바깥 필터**에서 set/clear
- 코드 리뷰 체크리스트에 "MDC.clear는 어느 필터에 있는가?" 항목 추가

---

### 감사 이벤트에 occurredAt 들고 있던 건 사실상 중복

**문제**
- `AuthAuditEvent.occurredAt: Instant` 가 있었는데, JSON 로그에 자동으로 timestamp가 박히니 의미 없음
- 두 timestamp가 미세하게 어긋날 위험만 있음 (이벤트 생성 시점 vs 로그 적재 시점)

**원인**
- 도메인 이벤트라는 단어 들으면 반사적으로 occurredAt 박는 습관

**액션플랜**
- 감사 로그 = 로그 timestamp가 곧 발생 시점. 이벤트 객체에 별도 시점 필드 두지 않기
- 정말 "발생 시점 ≠ 로깅 시점" 인 비동기 케이스에서만 명시적 필드

---

## 배운 점

### 책임은 "가장 바깥"에서 관리한다

**배움**
- MDC 같은 요청-스코프 자원의 set/clear는 **가장 바깥 필터** 한 곳에서만 — 안쪽으로 내려갈수록 누수 위험
- `try { ... } finally { clear }` 패턴은 책임이 안쪽에 있을 때 위험을 못 막아줌

**의미**
- 다음에 "요청 단위 컨텍스트" 키워드 들으면 무조건 가장 바깥 필터부터 의심

---

### 추상화는 두 번째 케이스 등장할 때

**배움**
- 처음 `AuthAuditLogger` 짤 때 추상화 안 한 게 다행 — 그땐 한 도메인뿐이라 추상 베이스 필요 없었음
- 두 번째 도메인 감사 로거 들어갈 시점에 추상화하니까 **실제로 공통인 것만** 베이스로 올라감

**의미**
- "DRY는 두 번째에" — 첫 번째 중복은 그냥 두는 게 보통 정답

---

## 핵심 내용

### 키워드
- `MDC`, `MdcContextFilter`, `logstash-logback-encoder`, `LoggingEventCompositeJsonEncoder`, `BaseAuditLogger<T>`, `KotlinLogging`

### 요약
- **MDC 책임**: 요청 단위 컨텍스트는 **가장 바깥 Filter**에서 set/clear. 안쪽 필터는 읽기만.
- **JSON 로깅**: `logstash-logback-encoder` + `LoggingEventCompositeJsonEncoder` 조합. 운영 ELK/CloudWatch에서 키 검색이 무조건 빨라짐.
- **감사 로거 추상화**: `BaseAuditLogger<T>` — `eventType` + `payload` 구조만 베이스에. 도메인별 Logger는 `<T>` 만 박으면 끝.

### 코드/명령어
```xml
<!-- logback-spring.xml — JSON 인코더 등록 -->
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
    <providers>
      <timestamp/>
      <logLevel/>
      <loggerName/>
      <message/>
      <mdc/>
      <stackTrace/>
    </providers>
  </encoder>
</appender>
```

```kotlin
// SecurityConfig — Mdc가 가장 바깥
http.addFilterBefore(mdcContextFilter, JwtAuthenticationFilter::class.java)
```

### 참고 자료
- `src/main/kotlin/com/bubaum/buws/global/web/MdcContextFilter.kt`
- `src/main/kotlin/com/bubaum/buws/global/audit/BaseAuditLogger.kt`
- 커밋: `8b7c2d7` (MDC + JSON), `5fda76a` (BaseAuditLogger)
