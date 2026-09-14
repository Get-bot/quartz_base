---
title: "[TIL-260506] Logback %replace + TurboFilter로 로그 노이즈 정밀 차단"
date: 2026-05-06
tags: ["Logback", "MDC", "Spring Boot", "Observability", "TurboFilter"]
categories: ["TIL"]
description: "Outbox 폴러 SQL 로그를 MDC + TurboFilter로 스레드 단위 정밀 차단하고, %replace로 빈 MDC 토큰을 자동 숨김 처리한 패턴"
---

## 잘한 점

### Outbox 폴러 SQL 노이즈만 정확히 차단

**상황**
- Outbox 폴러가 1초마다 `FOR UPDATE SKIP LOCKED` 쿼리를 날리는데, Hibernate SQL 로그가 켜져 있으면 콘솔이 폴러 쿼리로 도배됨
- 그렇다고 `org.hibernate.SQL` 로거를 통째로 끄면 다른 요청 디버깅할 때도 안 보임 — 양자택일이 싫었음

**액션**
- Logback `TurboFilter`를 직접 구현, Publisher가 `MDC[outbox.poll]=true` 세팅한 동안에만 `org.hibernate.SQL` / `org.hibernate.orm.jdbc.bind` 로거를 `DENY`
- 다른 스레드(API 요청, dispatcher executor)는 MDC 없으니 영향 0
- `withdrawal.outbox.log-poll-sql=true` 토글 한 줄로 필터 통째로 비활성화 — 디버깅 시 코드 수정 없이 즉시 복원

**칭찬**
- "전역 로거 끄기" vs "전부 켜기" 양자택일 안 가고 MDC로 스레드 단위 분리한 판단
- 토글을 둬서 운영 중에도 디버깅 모드 진입 가능하게 한 것

---

## 배운 점

### Logback %replace로 빈 MDC 토큰 통째로 숨기기

**배움**
- 로그 패턴에 MDC 토큰을 넣으면 컨텍스트 없는 로그에는 `[ ]` 같은 빈 괄호가 남는 게 거슬렸음
- `%replace(...){'정규식', ''}` 으로 "비어있는 패턴"이면 토큰을 통째로 지울 수 있음
- 스케줄러처럼 HTTP 컨텍스트 없는 로그가 깔끔해짐

**의미**
- MDC를 적극적으로 쓰면 로그 컨텍스트가 풍부해지지만, 컨텍스트 없는 스레드에서 로그가 지저분해지는 게 그동안 단점이었음
- 이제 MDC 토큰을 자유롭게 추가해도 됨 — 비면 알아서 사라지니까
- 같은 패턴으로 `requestId` / `memberId` / `roles` 등 토큰을 마음껏 추가해도 노이즈가 0

---

## 핵심 내용

### 키워드
- `Logback TurboFilter`, `MDC`, `%replace`, `FilterReply.DENY/NEUTRAL`, `ch.qos.logback.classic.turbo`

### 요약
- **TurboFilter**: 일반 Filter와 달리 LoggingEvent 생성 **전**에 호출되어 비용이 거의 0. 로거 이름 + MDC 조건으로 특정 스레드의 특정 로거만 통과/차단 가능.
- **`%replace(pattern){'regex', 'replacement'}`**: pattern을 평가한 결과가 regex와 매치되면 replacement로 치환. "비어있을 때만 숨기기"는 pattern을 토큰 통째로 감싸고 regex로 "공백+빈 괄호"를 매치시키면 됨.
- 둘 다 logback-classic 표준 기능 (Spring Boot 외 추가 의존성 0).

### 코드/명령어

```kotlin
// TurboFilter — MDC 매칭으로 폴러 SQL 로그만 DENY
class OutboxPollSqlTurboFilter : TurboFilter() {
    var logPollSql: Boolean = false

    override fun decide(
        marker: Marker?, logger: Logger, level: Level,
        format: String?, params: Array<out Any>?, t: Throwable?,
    ): FilterReply {
        if (logPollSql) return FilterReply.NEUTRAL
        if (MDC.get(MDC_KEY) != "true") return FilterReply.NEUTRAL

        return if (logger.name.startsWith("org.hibernate.SQL") ||
                   logger.name.startsWith("org.hibernate.orm.jdbc.bind")) {
            FilterReply.DENY
        } else FilterReply.NEUTRAL
    }
    companion object { const val MDC_KEY = "outbox.poll" }
}
```

```xml
<!-- logback-spring.xml — Spring Property + TurboFilter 등록 -->
<springProperty name="LOG_POLL_SQL" source="withdrawal.outbox.log-poll-sql" defaultValue="false"/>
<turboFilter class="com.bubaum.buws.global.logging.OutboxPollSqlTurboFilter">
    <logPollSql>${LOG_POLL_SQL}</logPollSql>
</turboFilter>

<!-- %replace로 빈 토큰 자동 숨김 -->
<property name="CTX_HTTP"
    value="%replace( [%X{httpMethod:-} %X{httpPath:-}]){'^ \[ \]$', ''}"/>
<property name="CTX_AUTH"
    value="%replace( [ip=%X{clientIp:-} member=%X{memberId:-}]){'^ \[ip= member=\]$', ''}"/>
```

### 참고 자료
- Logback Manual — TurboFilter: https://logback.qos.ch/manual/filters.html#TurboFilter
- Logback Manual — `%replace` conversion word: https://logback.qos.ch/manual/layouts.html#replace
