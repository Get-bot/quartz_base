---
title: "Spring Boot에서 jOOQ와 AOP 사용 시 실행 속도 저하 문제 해결"
date: 2024-04-07
tags: ["spring", "aop", "jooq", "performance", "troubleshooting"]
description: "전역 로깅 AOP를 붙이자 기동이 1분 넘게 걸린 원인. execution 포인트컷이 DSLContext의 모든 메서드를 매칭하던 문제를 within으로 좁혀 해결."
source: https://velog.io/@co-vol/Spring-Boot%EC%97%90%EC%84%9C-Jooq%EC%99%80-AOP-%EC%82%AC%EC%9A%A9-%EC%8B%9C-%EC%8B%A4%ED%96%89-%EC%86%8D%EB%8F%84-%EC%A0%80%ED%95%98-%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0
---

### Jooq 소개
Jooq는 Java 객체 지향 쿼리를 위한 프레임워크로, SQL을 타입 안전하게 작성할 수 있게 해준다. 이는 복잡한 SQL 쿼리를 간편하게 작성하고 관리할 수 있게 해준다.

### AOP(Aspect-Oriented Programming) 이해
AOP는 프로그래밍에서 공통적으로 사용되는 기능(예: 로깅, 보안)을 모듈화하는 프로그래밍 패러다임이다. 이는 코드의 재사용성과 가독성을 향상시키는 데 도움을 준다.

### 발생한 문제
Spring Boot, Jooq, 그리고 전역 오류 로깅을 위한 AOP 설정 후 스프링 실행 속도가 1분 이상 걸리는 문제가 발생하였다. 문제 해결을 위한 디버깅 과정에서 AOP를 제거하고 실행하니 문제 없이 실행되었다. 이로 인해 AOP의 문제인가?? 라고 생각하게 되었다.

## 문제 진단

### AOP 설정의 영향
AOP를 제거한 후 애플리케이션의 실행 속도가 정상으로 돌아온 것으로 보아, AOP 설정이 실행 속도 저하의 직접적인 원인임을 확인할 수 있었다.

### 실행 속도 저하의 원인 분석
#### AOP 추적
디버깅 과정에서 org.aspectj.weaver.internal.tools.PointcutExpressionImpl의 canMatchJoinPointsInType 메서드가 항상 true를 반환하고, 이로 인해 DefaultDSLContext의 모든 메서드에 포인트 컷을 적용할 수 있는지 확인하는 과정에서 성능 저하가 발생하는 것을 발견하였다.

#### Pointcut 표현식의 영향
execution 대신 within을 사용하였을 때 문제가 해결되었다는 사실로 미루어 볼 때, Pointcut 표현식의 선택이 성능에 큰 영향을 미칠 수 있음을 알 수 있었다.

### 해결 방안
#### execution 대신 within 사용하기
Pointcut 표현식에서 execution 대신 within을 사용함으로써, 포인트컷의 적용 범위를 좁히고, 이를 통해 DefaultDSLContext의 모든 메서드에 대한 포인트컷 적용을 피함으로써 성능 문제를 해결할 수 있었다.
#### execution
```java
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;

@Aspect
public class LoggingAspect {

    @Pointcut("execution(* com.example.service.*.*(..))")
    public void serviceLayerExecution() {
        // Pointcut body, usually empty
    }
}
```
#### within
```java
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;

@Aspect
public class LoggingAspect {

    @Pointcut("within(com.example.service..*)")
    public void serviceLayerWithin() {
        // Pointcut body, usually empty
    }
}
```
#### execution과 within의 차이점
execution과 within은 AspectJ에서 사용되는 Pointcut 지시자들로, 조인 포인트(join points)를 지정하는 방식에서 중요한 차이를 가집니다. 이 차이는 어떤 메서드나 객체에 대한 관점(Aspect)의 적용 범위를 결정하는 데 큰 영향을 미칩니다.

execution 지시자는 메소드 실행 시의 조인 포인트를 지정합니다. 이는 특정 메소드가 실행될 때 해당 메소드에 관점을 적용하고자 할 때 사용됩니다. execution 지시자는 메소드의 시그니처를 기반으로 매우 구체적인 타겟을 정할 수 있으며, 이를 통해 특정 메소드나 메소드 그룹에 대해 세밀한 관점 적용이 가능합니다. 예를 들어, execution(public String com.example.MyClass.myMethod(..))는 com.example.MyClass에 있는 myMethod 메소드의 실행 시점에만 관점을 적용하도록 지정합니다.

within 지시자는 특정 타입 내의 모든 조인 포인트를 지정하여 사용 범위가 execution보다 제한적일 수 있습니다. within은 특정 클래스나 패키지 내의 모든 메소드 실행을 포인트컷의 대상으로 지정합니다. 이는 해당 타입 내에서 실행되는 모든 메소드에 관점을 일괄적으로 적용하고자 할 때 유용합니다. 예를 들어, within(com.example.MyClass)는 com.example.MyClass 내의 모든 메소드에 대해 관점을 적용합니다.

이러한 차이는 포인트컷의 적용 범위와 성능 최적화에 중요한 영향을 미칩니다. execution 지시자는 매우 구체적인 적용 범위를 제공하지만, 많은 메소드에 대해 개별적으로 적용될 때 성능 저하의 원인이 될 수 있습니다. 반면, within 지시자는 특정 클래스나 패키지 내의 모든 조인 포인트에 대한 일괄적인 적용을 가능하게 하여, 성능 최적화에 도움을 줄 수 있습니다. 그러나 이는 적용 범위의 정밀도가 다소 떨어질 수 있다는 점을 의미하기도 합니다.

---

원문: [velog · 2024-04-07](https://velog.io/@co-vol/Spring-Boot%EC%97%90%EC%84%9C-Jooq%EC%99%80-AOP-%EC%82%AC%EC%9A%A9-%EC%8B%9C-%EC%8B%A4%ED%96%89-%EC%86%8D%EB%8F%84-%EC%A0%80%ED%95%98-%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0)
