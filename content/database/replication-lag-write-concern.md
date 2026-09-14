---
title: "DB 리플리케이션 지연(Lag)을 해결하는 방법: Write-Concern 패턴 적용기"
date: 2026-01-06
tags: ["mysql", "replication", "spring-boot", "aop", "datasource-routing", "database"]
description: "Master/Slave 분리 후 '방금 쓴 글이 안 보이는' 문제. 최근 쓰기 이력을 ThreadLocal·Request·Cookie 3계층으로 추적해 일정 시간 Master로 라우팅. P6Spy가 라우팅을 무력화한 함정까지."
source: https://velog.io/@co-vol/Spring-Boot-DB-%EB%A6%AC%ED%94%8C%EB%A6%AC%EC%BC%80%EC%9D%B4%EC%85%98-%EC%A7%80%EC%97%B0Lag%EC%9D%84-%ED%95%B4%EA%B2%B0%ED%95%98%EB%8A%94-%EB%B0%A9%EB%B2%95-Write-Concern-%ED%8C%A8%ED%84%B4-%EC%A0%81%EC%9A%A9%EA%B8%B0
---

대규모 트래픽 처리를 위해 데이터베이스를 **Master(Write)**와 **Slave(Read)**로 분리하는 것은 백엔드 개발에서 흔한 패턴입니다. 하지만 이 구조를 도입하자마자 마주치는 고질적인 문제가 하나 있습니다. 바로 **'리플리케이션 지연(Replication Lag)'**입니다.

오늘은 Master/Slave 구조에서 발생한 데이터 불일치 문제를 해결하기 위해, **사용자의 최근 쓰기 이력을 추적하여 동적으로 DB를 라우팅한 경험**을 공유하려 합니다.

## 1. 문제 상황: "방금 쓴 글이 안 보여요"

저희 서비스는 읽기 성능을 높이기 위해 `AbstractRoutingDataSource`를 사용하여 트랜잭션의 `@Transactional(readOnly = true)` 여부에 따라 쿼리를 분기 처리하고 있습니다.

- **쓰기(Write):** Master DB
- **읽기(Read):** Slave DB

하지만 Master에 저장된 데이터가 Slave로 복제되기까지는 아주 짧지만 물리적인 시간(Lag)이 소요됩니다. 이로 인해 사용자가 데이터를 수정하고 즉시 목록 페이지로 리다이렉트되었을 때, **Slave DB에는 아직 데이터가 도달하지 않아 수정 전의 내용이 노출되는 문제**가 발생했습니다. 이는 사용자 경험(UX)에 치명적이었습니다.

## 2. 해결 전략: "방금 쓴 사람은 Master를 보게 하자"

이 문제를 해결하기 위해 **"최근에 쓰기 작업을 수행한 사용자는 일정 시간 동안 강제로 Master DB에서 읽게 한다"**는 전략을 세웠습니다. 이를 구현하기 위해 세 가지 범위(Scope)에서의 추적이 필요했습니다.

1. **현재 스레드(Thread):** 한 트랜잭션 내에서 쓰기 후 바로 읽는 경우.
2. **현재 요청(Request):** 하나의 HTTP 요청 안에서 쓰기 로직 수행 후, 다른 로직에서 읽기를 수행하는 경우.
3. **사용자 세션(Client):** 쓰기 요청이 끝나고 **다음 요청(새로고침 등)**으로 넘어왔을 때.

저는 이 상태를 관리하기 위해 `WriteTracker`라는 컴포넌트를 설계했고, 다음과 같은 흐름을 만들었습니다.

- **쓰기 발생 시:** 타임스탬프를 기록하고, 응답 쿠키(Cookie)에 마지막 쓰기 시간을 구워줍니다.
- **읽기 발생 시:** 쿠키나 내부 상태를 확인해 `현재 시간 - 마지막 쓰기 시간 < 설정된 Lag 시간`이라면 **강제로 Master DB**를 바라보게 합니다.

## 3. 구현 상세

### 3.1. 핵심 로직: `WriteTracker`와 범위별 추적

가장 먼저 `WriteTracker` 클래스를 통해 쓰기 상태를 판단하는 로직을 중앙화했습니다.

```java
// WriteTracker.java (요약)
public boolean shouldForceReadFromMaster() {
    // 1. ThreadLocal 체크 (현재 스레드 내 쓰기)
    if (isWithinLagWindow(WRITE_TIMESTAMP.get())) return true;

    // 2. Request Attribute 체크 (현재 요청 내 쓰기)
    if (request.getAttribute(txCommitFlag) != null) return true;

    // 3. Cookie 체크 (이전 요청에서의 쓰기 - 리다이렉트 등)
    Long lastWrite = extractFromCookie(request);
    return lastWrite != null && isWithinLagWindow(lastWrite);
}
```

여기서 중요한 점은 **ThreadLocal, Request Attribute, Cookie**를 순차적으로 확인하여, 서버 내부의 로직 흐름뿐만 아니라 클라이언트의 재요청 시나리오까지 커버했다는 점입니다.

### 3.2. AOP를 통한 투명한 추적 (`WriteTrackingAspect`)

개발자가 비즈니스 로직마다 `tracker.markWrite()`를 호출하는 것은 실수할 여지가 많습니다. 그래서 AOP를 사용하여 `@Transactional` 어노테이션이 붙은 메서드를 가로챘습니다.

```java
// WriteTrackingAspect.java
@Around("@annotation(transactional)")
public Object trackWriteTransaction(ProceedingJoinPoint joinPoint, Transactional transactional) {
    if (transactional.readOnly()) {
        return joinPoint.proceed();
    }

    // 1. 쓰기 시작 마킹
    writeTracker.markWriteStarted();
    
    Object result = joinPoint.proceed();

    // 2. 트랜잭션 동기화 매니저에 핸들러 등록
    if (TransactionSynchronizationManager.isActualTransactionActive()) {
        TransactionSynchronizationManager.registerSynchronization(new WriteSyncHandler(...));
    }
    return result;
}
```

트랜잭션이 성공적으로 커밋된 시점(`afterCommit`)에 쿠키를 생성하여 클라이언트에게 내려줌으로써, 다음 요청부터는 이 쿠키를 들고 오게 만들었습니다.

### 3.3. 동적 라우팅 (`TransactionRoutingDataSource`)

마지막으로 `AbstractRoutingDataSource`를 상속받은 라우팅 소스에서 `WriteTracker`의 판단 결과를 반영했습니다.

```java
// TransactionRoutingDataSource.java
@Override
protected Object determineCurrentLookupKey() {
    boolean isReadOnly = TransactionSynchronizationManager.isCurrentTransactionReadOnly();

    // 1. 쓰기 트랜잭션이면 무조건 Master
    if (!isReadOnly) return DataSourceType.MASTER;

    // 2. 읽기 트랜잭션이지만, 최근 쓰기 이력이 있다면 Master (Lag 방지)
    if (writeTracker.shouldForceReadFromMaster()) {
        log.debug("Routing to MASTER (avoiding replication lag)");
        return DataSourceType.MASTER;
    }

    return DataSourceType.SLAVE;
}
```

## 4. 트러블 슈팅 및 주의할 점

### ThreadLocal 메모리 누수 방지

`ThreadLocal`을 사용할 때는 반드시 사용 후 정리가 필요합니다. 톰캣과 같은 스레드 풀 환경에서는 스레드가 재사용되기 때문입니다. 이를 위해 `WriteTrackerCleanupFilter`를 구현하여 요청이 끝나는 시점에 `writeTracker.clear()`를 호출하도록 `HighestPrecedence`로 설정했습니다.

### `LazyConnectionDataSourceProxy`의 필수성

Spring의 트랜잭션 처리는 트랜잭션 시작 시점에 Connection을 확보하려 합니다. 라우팅 로직이 동작하기도 전에 이미 커넥션을 잡아버리는 문제를 방지하기 위해 `LazyConnectionDataSourceProxy`를 사용하여 **실제 쿼리가 실행되는 시점까지 커넥션 획득을 지연**시켰습니다.

### P6Spy와 무조건적인 Master 라우팅 이슈

개발 과정에서 쿼리 파라미터를 편하게 확인하기 위해 **P6Spy (v1.21.1)** 라이브러리를 적용했습니다. 그런데 P6Spy 적용 직후, **분명히 Slave로 가야 할 읽기 전용 트랜잭션들까지 전부 Master DB로 쏠리는 현상**이 발견되었습니다.

### 원인 분석

원인은 P6Spy의 작동 방식에 있었습니다. P6Spy(정확히는 관련 Spring Boot Starter)는 빈 후처리기(BeanPostProcessor)를 통해 애플리케이션의 `DataSource` 빈을 감싸서(Decorate) 프록시 객체를 만듭니다.

문제는 이 과정에서 P6Spy가 **`LazyConnectionDataSourceProxy`나 `RoutingDataSource`보다 상위에서 감싸버리거나, 커넥션 객체를 미리 요청**해버린다는 점입니다. 이로 인해 트랜잭션의 속성(`readOnly`)을 확인하고 분기 처리를 하기도 전에 이미 커넥션이 맺어져 버렸고, 결과적으로 기본값인 Master DB 커넥션만 계속 사용하게 된 것입니다.

### 해결 방법

이 문제를 해결하기 위해 P6Spy의 데코레이터 설정에서 **라우팅 로직이 포함된 `dataSource` 빈은 감싸지 않도록 제외(exclude)** 처리했습니다.

```yaml
# application.yml

decorator:
  datasource:
    # RoutingDataSource는 이미 내부적으로 분기 처리를 하므로 P6Spy가 감싸지 않도록 설정
    ignore-routing-data-sources: true
    # 우리가 직접 만든(Lazy+Routing) 최종 dataSource 빈은 P6Spy 적용 제외
    exclude-beans: dataSource
```

위와 같이 `exclude-beans: dataSource` 설정을 추가하여 P6Spy가 최상단 `dataSource` 빈을 건드리지 않게 하자, `LazyConnectionDataSourceProxy`가 정상적으로 지연 로딩을 수행하면서 라우팅이 다시 올바르게 작동했습니다.

## 5. 마치며

이 구조를 도입한 후, 사용자가 "수정했습니다"라는 메시지를 보고 목록으로 돌아갔을 때 데이터가 반영되지 않는 문제는 완벽하게 사라졌습니다.

물론, "최근 글을 쓴 사용자"의 트래픽이 일시적으로 Master DB로 몰릴 수 있다는 트레이드오프가 있습니다. 하지만 데이터의 정합성이 UX에 미치는 영향이 훨씬 크다고 판단했으며, `replicationLagMs` 시간을 적절히 조절(예: 2초)하여 Master 부하를 최소화했습니다.

이번 개발을 통해 **데이터베이스 아키텍처는 단순히 인프라 설정뿐만 아니라, 애플리케이션 레벨에서의 정교한 핸들링이 더해졌을 때 비로소 완성된다**는 것을 배웠습니다.

---

원문: [velog · 2026-01-06](https://velog.io/@co-vol/Spring-Boot-DB-%EB%A6%AC%ED%94%8C%EB%A6%AC%EC%BC%80%EC%9D%B4%EC%85%98-%EC%A7%80%EC%97%B0Lag%EC%9D%84-%ED%95%B4%EA%B2%B0%ED%95%98%EB%8A%94-%EB%B0%A9%EB%B2%95-Write-Concern-%ED%8C%A8%ED%84%B4-%EC%A0%81%EC%9A%A9%EA%B8%B0)
