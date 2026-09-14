---
title: "if-else 지옥 탈출기: 이상거래 감지 시스템을 Chain of Responsibility로 구원하기"
date: 2026-01-20
tags: ["design-pattern", "chain-of-responsibility", "java", "spring-boot", "refactoring", "architecture"]
description: "출금 이상거래 감지 조건이 늘수록 비대해지던 if-else를 Chain of Responsibility로 재구성. Template Method, Spring List 주입 자동 등록, 불변 체인, DB 기반 동적 순서까지."
source: https://velog.io/@co-vol/if-else-%EC%A7%80%EC%98%A5-%ED%83%88%EC%B6%9C%EA%B8%B0-%EC%9D%B4%EC%83%81%EA%B1%B0%EB%9E%98-%EA%B0%90%EC%A7%80-%EC%8B%9C%EC%8A%A4%ED%85%9C%EC%9D%84-Chain-of-Responsibility%EB%A1%9C-%EA%B5%AC%EC%9B%90%ED%95%98%EA%B8%B0
---

> 복잡하게 얽힌 if-else 로직을 Chain of Responsibility 패턴으로 리팩토링하여 유연성과 확장성을 확보한 경험을 공유합니다.

## 문제 상황: 증식하는 if-else와 유지보수의 한계

담당하고 있는 **이상거래 모니터링 시스템**은 출금 요청 발생 시 다양한 조건을 검사하여 이상 징후를 포착해야 한다. 서비스 초기에는 조건이 단순했으나, 비즈니스 성장에 따라 초과 출금, 집중 출금, 실패 출금, 시간대 제한, 휴일 제한 등 감지해야 할 조건이 지속적으로 증가했다.

가장 큰 문제는 **코드의 구조**였다. 새로운 감지 조건이 추가될 때마다 서비스 클래스 내의 비대해진 `if-else` 블록을 수정해야 했다.

```java
// [기존 코드] 여러 서비스에 분산되고 중복된 감지 로직
public AppValidateWithdrawBlockDto validateWithdrawBlockByCond(
        AppWithdrawDetectReqDto reqDto,
        AppWithdrawBlockDetectCondDto detectCondDto) {

    List<WithdrawLogStatusDto> logStatusDtos = new ArrayList<>();

    // 1. 초과 출금 감지
    if (detectCondDto.overWithdrawBlock() != null && detectCondDto.overWithdrawBlock().isActive()) {
        int count = withdrawRepository.countByOverBlock(reqDto.storeCode(), ...);
        if (count >= threshold) {
            logStatusDtos.add(new WithdrawLogStatusDto(DetectStatus.DETECT, ...));
        }
    }

    // 2. 집중 출금 감지
    if (detectCondDto.focusWithdrawBlock() != null && detectCondDto.focusWithdrawBlock().isActive()) {
        int count = withdrawRepository.countByFocusBlock(reqDto.storeCode(), ...);
        if (count >= threshold) {
            logStatusDtos.add(new WithdrawLogStatusDto(DetectStatus.DETECT, ...));
        }
    }

    // ... 끝없는 if-else의 반복 ...
}
```

> "새로운 감지 조건 하나를 추가하기 위해 수정해야 할 포인트가 너무 많다."

단순한 코드량 증가를 넘어 구조적인 한계가 명확했다.

1. **로직의 파편화:** 유사한 검증 로직이 여러 서비스 메서드에 흩어져 있어, 수정 시 누락으로 인한 버그 발생 위험이 높았다.
2. **경직된 유연성:** "결제 앱(PayApp)별로 감지 순서를 다르게 설정하고 싶다"는 운영팀의 요구사항을 수용하기에는 `if-else` 기반의 하드코딩된 순서를 변경하기 어려웠다.

운영 편의성과 시스템 확장성, 두 마리 토끼를 잡기 위해 근본적인 구조 변경이 필요했다.

## 해결책: Chain of Responsibility 패턴

GoF의 디자인 패턴 중 **Chain of Responsibility(책임 연쇄)** 패턴을 도입하기로 결정했다. 요청을 처리할 수 있는 핸들러들을 체인(사슬)으로 연결하고, 요청을 체인을 따라 전달하면서 적절한 핸들러가 처리하도록 하는 방식이다.

> Why Not Strategy Pattern?
Strategy 패턴도 고려했으나, 현재 요구사항은 "단일 전략 선택"이 아닌 **"순차적으로 여러 조건을 검사하다가, 하나라도 걸리면 즉시 탐지(중단)"**하는 파이프라인 구조였다. 따라서 핸들러의 순서를 제어하고 책임을 다음 객체로 전파하는 Chain of Responsibility가 가장 적합했다.

### 설계 아키텍처
![](https://velog.velcdn.com/images/co-vol/post/356a356c-0618-4675-aa53-0508e9be46fc/image.jpg)

**핵심 설계 원칙:**

1. **단일 책임 원칙 (SRP):** 각 핸들러는 오직 하나의 감지 조건(초과, 집중, 시간대 등)만 담당한다.
2. **개방-폐쇄 원칙 (OCP):** 새 조건 추가 시 기존 코드를 수정하지 않고, 새로운 핸들러 클래스만 추가하여 확장한다.
3. **동적 우선순위 관리:** 감지 순서를 코드가 아닌 DB에서 관리하여, **배포 없이 운영팀이 제어**할 수 있게 한다.

## 구현: Step by Step

### Step 1. 추상 핸들러와 템플릿 메서드

모든 감지 핸들러가 상속받을 추상 클래스다. `handle()` 메서드를 `final`로 선언하여 **Template Method 패턴**을 적용, 전체적인 처리 흐름을 하위 클래스에서 변경할 수 없도록 강제했다.

```java
// [WithdrawDetectHandler.java]
public abstract class WithdrawDetectHandler<T extends WithdrawBlockDetectCondBase> {

    // 처리 흐름의 골격 정의 (Template Method)
    public final ValidateDetectDto handle(
            T detectCondDto,
            List<WithdrawLogType> allowedLogTypes,
            ValidateParamDto paramDto
    ) {
        // 1. 처리 가능 여부 확인
        if (!canHandle(detectCondDto, allowedLogTypes)) {
            return null; // Pass -> 다음 핸들러로
        }

        // 2. 실제 감지 로직 수행 (추상 메서드 위임)
        DetectStatus detectStatus = doDetect(detectCondDto, paramDto);

        // 3. 감지된 경우 결과 반환 (체인 중단)
        if (DetectStatus.DETECT == detectStatus) {
            return ValidateDetectDto.builder()
                    .detectStatus(detectStatus)
                    .logType(getLogType())
                    .build();
        }

        return null; // Pass
    }

    protected abstract boolean canHandle(T detectCondDto, List<WithdrawLogType> allowedLogTypes);
    protected abstract DetectStatus doDetect(T detectCondDto, ValidateParamDto paramDto);
    // ... 기타 메타데이터 메서드
}
```

제네릭 타입 `T`를 활용해 앱 기반 감지(`App...Dto`)와 매장 기반 감지(`Store...Dto`)를 유연하게 처리할 수 있도록 설계하여 타입 안정성을 확보했다.

### Step 2. 구체 핸들러 구현 (단일 책임)

이제 각 감지 로직은 독립된 클래스로 분리된다. 아래는 '초과 출금'을 감지하는 핸들러의 예시다.

```java
// [AppOverWithdrawBlockHandler.java]
@Component
@RequiredArgsConstructor
public class AppOverWithdrawBlockHandler extends WithdrawDetectHandler<AppWithdrawBlockDetectCondDto> {

    private final WithdrawRepository withdrawRepository;

    @Override
    protected boolean canHandle(AppWithdrawBlockDetectCondDto detectCondDto, List<WithdrawLogType> allowedLogTypes) {
        // 예외 허용 목록에 있거나, 조건이 비활성화된 경우 스킵
        if (allowedLogTypes != null && allowedLogTypes.contains(getLogType())) return false;

        AppOverWithdrawBlockDto overBlock = detectCondDto.overWithdrawBlock();
        return overBlock != null && overBlock.isActive();
    }

    @Override
    protected DetectStatus doDetect(AppWithdrawBlockDetectCondDto detectCondDto, ValidateParamDto paramDto) {
        // 순수한 비즈니스 로직에만 집중
        AppOverWithdrawBlockDto overBlock = detectCondDto.overWithdrawBlock();
        int detectCount = withdrawRepository.countAppWithdrawByOverBlock(paramDto.storeCode(), overBlock);

        return detectCount >= overBlock.thresholdCount()
                ? DetectStatus.DETECT
                : DetectStatus.PASS;
    }

    @Override
    protected WithdrawLogType getLogType() { return WithdrawLogType.OVER_WITHDRAW_BLOCK_LOG; }

    // ...
}
```

### Step 3. Spring DI를 활용한 핸들러 자동 등록

새로운 핸들러를 추가할 때마다 등록 코드를 수동으로 수정해야 한다면 OCP 위반이다. Spring의 `List` 주입 기능을 활용해 이를 해결했다.

```java
// [WithdrawHandlerRegistry.java]
@Component
@RequiredArgsConstructor
public class WithdrawHandlerRegistry {

    // Spring이 WithdrawDetectHandler 타입을 상속받은 모든 빈(Bean)을 자동으로 주입해준다.
    private final List<WithdrawDetectHandler<?>> handlers;

    // 조회 성능을 위한 캐싱 맵
    private final Map<WithdrawHandlerKey, WithdrawDetectHandler<?>> handlerIndex = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        // 주입받은 핸들러들을 메타데이터 기반으로 인덱싱하여 빠른 조회 지원
        for (WithdrawDetectHandler<?> handler : handlers) {
            // ... 인덱싱 로직 ...
        }
    }

    // ...
}
```

이 구조 덕분에 개발자는 핸들러 클래스를 만들고 `@Component`만 붙이면, 별도의 설정 변경 없이 자동으로 시스템에 통합된다.

### Step 4. Thread-Safety를 위한 불변 체인(Immutable Chain)

웹 애플리케이션은 멀티스레드 환경이므로, 체인을 구성하는 리스트가 요청 처리 도중 변경되어서는 안 된다. 이를 방지하기 위해 체인을 **불변(Immutable)** 객체로 설계했다.

```java
// [ImmutableHandlerChain.java]
public class ImmutableHandlerChain<T extends WithdrawBlockDetectCondBase> {

    private final List<WithdrawDetectHandler<T>> handlers;

    public ImmutableHandlerChain(List<WithdrawDetectHandler<T>> handlers) {
        // 생성 시점에 방어적 복사(Defensive Copy) 수행
        this.handlers = List.copyOf(handlers);
    }

    public ValidateDetectDto execute(T detectCondDto, ...) {
        for (WithdrawDetectHandler<T> handler : handlers) {
            try {
                ValidateDetectDto result = handler.handle(...);
                if (result != null) return result; // 감지됨!
            } catch (Exception e) {
                // 하나의 핸들러가 실패해도 전체 프로세스는 멈추지 않도록 예외 격리
                log.error("Handler failed", e);
            }
        }
        return ValidateDetectDto.pass();
    }
}
```

`List.copyOf()`를 사용해 불변 리스트를 생성함으로써, 원본 리스트가 외부에서 변경되어도 실행 중인 체인은 영향을 받지 않아 Thread-Safety가 보장된다.

### Step 5. DB 기반의 동적 체인 구성

마지막 단계는 '순서의 제어'다. DB에 저장된 우선순위 설정(`PriorityConfig`)을 읽어 체인을 동적으로 조립한다.

```java
// [WithdrawDetectChainBuilder.java]
public ImmutableHandlerChain<...> buildChain(UUID detectCondId) {
    // 1. DB에서 설정된 순서 조회 (예: 초과 -> 시간대 -> 휴일)
    List<WithdrawBlockType> orderedTypes = priorityConfigRepository.findOrderedTypes(...);

    // 2. 순서에 맞춰 핸들러 매핑
    List<WithdrawDetectHandler<T>> orderedHandlers = orderedTypes.stream()
            .map(handlerRegistry::getHandler)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());

    // 3. 불변 체인 생성 후 반환
    return new ImmutableHandlerChain<>(orderedHandlers);
}
```

이제 운영팀이 관리자 페이지에서 감지 순서를 변경하면, 다음 요청부터 즉시 반영된다. **서버 재배포는 필요 없다.**

## 운영 유연성: 공용 조건과 개별 조건의 조화

시스템은 두 가지 층위의 규칙을 소화해야 했다.

1. **공용 규칙:** 결제앱(PayApp)마다 정해진 기본 감지 순서.
2. **개별 예외:** 특정 VIP 회원이나 매장에 대한 예외 처리.

공용 규칙은 위에서 설명한 `PriorityConfig`로 해결했고, 개별 예외는 `allowedLogTypes` 파라미터를 통해 구현했다. 각 핸들러의 `canHandle` 메서드에서 이 목록을 체크하여, 특정 조건 검사를 건너뛰도록(Skip) 처리했다. 이를 통해 **일관성 있는 정책** 위에 **유연한 예외 처리**를 얹을 수 있었다.

## 결과 및 회고

이 리팩토링을 통해 얻은 성과는 다음과 같다.

1. **확장성 확보:** 새로운 감지 조건이 필요하면 핸들러 클래스(`@Component`) 하나만 추가하면 된다. 기존 코드를 수정할 위험(Side Effect)이 사라졌다.
2. **운영 효율성 증대:** 개발자의 개입 없이 운영팀이 직접 감지 우선순위를 조정할 수 있게 되어 업무 효율이 높아졌다.
3. **안정성 강화:** 각 핸들러가 격리되어 있고, 불변 체인을 통해 동시성 문제로부터 안전하다. 또한 단위 테스트 작성이 훨씬 용이해졌다.

> "코드가 고통스러워질 때가 바로 리팩토링의 적기다."

초기에는 단순했던 요구사항이 복잡해지면서 코드는 점차 유지보수하기 힘든 상태가 되었다. 하지만 적절한 시점에 디자인 패턴을 도입함으로써, 기술적 부채를 해결하고 비즈니스의 빠른 변화를 뒷받침할 수 있는 견고한 구조를 구축할 수 있었다.

**참고 자료**

- GoF Design Patterns - Chain of Responsibility
- Spring Framework Reference - IOC & DI
- Java Concurrency - Immutable Objects

---

원문: [velog · 2026-01-20](https://velog.io/@co-vol/if-else-%EC%A7%80%EC%98%A5-%ED%83%88%EC%B6%9C%EA%B8%B0-%EC%9D%B4%EC%83%81%EA%B1%B0%EB%9E%98-%EA%B0%90%EC%A7%80-%EC%8B%9C%EC%8A%A4%ED%85%9C%EC%9D%84-Chain-of-Responsibility%EB%A1%9C-%EA%B5%AC%EC%9B%90%ED%95%98%EA%B8%B0)
