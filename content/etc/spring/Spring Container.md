# Spring Container란?

스프링 컨테이너는 스프링 프레임워크이 핵심 요소 중 하나로, 애플리케이션의 객체(Bean)를 생성, 관리, 설정하는 역할을 한다. 이를 통해 개발자는 객체 간의 의존성을 관리할 수 있으며, 애플리케이션의 구성 요소를 더욱 유연하게 관리할 수 있다.

## 핵심기능

- **의존성 주입 (DI)** : 스프링 컨테이너는 빈 사이의 의존성을 자동으로 주입해 준다. 이를 통해 개발자는 객체 간의 결합도를 낮추고, 유지 보수성을 향상시킬 수 있다.
- **빈(Bean)의 생명주기 관리** : 스프링 컨테이너는 빈의 생성부터 소멸까지의 생명주기를 관리해준다. 이를 통해 개발자는 빈의 초기화 및 소멸과 관련된 로직을 쉽게 구현할 수 있다.

## 장점

- **코드의 간결화** : 스프링 컨테이너를 사용함으로써 복잡한 의존성 관리 로직을 프레임워크에 위임할 수 있으며(Ioc), 결과적으로 코드가 더 간결해지고 명확해진다.
- **유연한 구성 및 관리** : XML파일이나 자바 어노테이션을 사용하여 빈의 설정 정보를  관리할 수 있다.  이를 통해 애플리케이션의 설정을 유연하게 변경할 수 있으며, 개발과 운영 환경 간의 설정을 쉽게 전환할 수 있다.

## BeanFactory 와 ApplicationContext

### BeanFactory

- 스프링 컨테이너의 가장 기본적인 형태, 빈의 정의를 로딩, 빈 인스턴스 생성, 의존성 주입
- 빈의 생성과 관리에 초점을 맞추어, 상대적으로 가벼운 리소스 사용, Iot등 리소스가 제한적인 환경에서 주로 사용

### ApplicationContext

- BeanFactory의 확장 형태로, 빈팩토리가 제공하는 기능 외에도 국제화,AOP와의 손쉬운 통합, 웹 애플리케이션에서 쉬운 사용,애플리케이션 특정 기능 접근 등 추가적인 기능 제공
- 풍부한 기능을 제공하기 떄문에, 대규모 애플리케이션 개발에 적합
- 코드

    ```java
    public static void main(String[] args) {
    
        ApplicationContext context = new AnnotationConfigApplicationContext(SimpleSpringLauncherApplication.class);
        Arrays.stream(context.getBeanDefinitionNames()).forEach(System.out::println);
    
    }
    ```


## Java Bean vs POJO vs Spring Bean

### Java Bean

재사용 가능한 소프트웨어 컴포넌트를 만들기 위한 표준 방식 제공

- 클래스 public이고 기본 생성자를 가진다.
- 프로퍼티 접근을 위한 getter 및 setter를 가진다
- 직렬화가 가능해야 한다. → java.io.Serializable인터페이스 구현
- 이벤트 처리가 가능하다.

### POJO (Plain Old Java Object)

POJO는 특정 규약이나 프레임워크를 따르지 않는 간단한 Java 객체를 말한다. POJO개념의 도입 목적은 개발자가 특정 인터페이스를 구현하거나 클래스를 상속 받는 등의 제약 없이 자유롭게 객체를 정의할 수 있게 하는 것이다. EJB(EnterpriseJavaBeans)와 같이 기술적 복잡한 요구 사항을 가진 기술에 대한 반작용으로 생겨남

- 특정 기술에 종속되지 않는다.
- 직렬화나 인터페이스 구현을 요구하지 않는다.
- Java의 객체 지향적 특성을 최대한 활용할 수 있다.
- 즉, 모든 자바 객체는 POJO

### Spring Bean

Spring IoC Container 컨테이너가 관리하는 객체이다. Spring Framework에서 Bean은 애플리케이션의 핵심을 이루는 객체이며, Spring Container에 의해 인스턴스화,조립, 관리된다. Spring Bean의 생명주기와 의존성은 Spring Container에 의해 관리된다

- Spring 설정 파일이나 어노테이션을 통해 정의
- Spring Container는 Bean의 생성, 의존성 주입, 생명주기 관리 등을 담당.
- Component, Service, Repository, Controller 등 다양한 역할을 가진 객체들을 Spring Bean으로 정의 가능

# 컨테이너 사용 방법

## 스프링 설정 방법

- **XML 기반 설정** : 과거에는 주로 XML파일을 사용하여 스프링 빈의 정보를 관리했다. 빈의 설정을 한눈에 볼 수 있으나, 설정 파일이 커질 경우 관리가 어려워진다.

    ```java
    <?xml version="1.0" encoding="UTF-8"?>
    <beans xmlns="http://www.springframework.org/schema/beans"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:context="http://www.springframework.org/schema/context"
           xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
            http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">
        <!-- bean definitions here -->
        <bean id="name" class="java.lang.String">
            <constructor-arg value="Some name"/>
        </bean>
    
        <bean id="age" class="java.lang.Integer">
            <constructor-arg value="35"/>
        </bean>
    
        <!--컴포넌트 스캔-->
        <context:component-scan base-package="com.in28minutes.learnspringframework.game"/>
    
        <!--개별 등록-->
        <bean id="game" class="com.in28minutes.learnspringframework.game.PackManGame"/>
        <bean id="gameRunner" class="com.in28minutes.learnspringframework.game.GameRunner">
            <constructor-arg ref="game"/>
        </bean>
    
    </beans>
    ```

- **자바 기반 설정** : 애노테이션(@Configuration, @Bean 등)을 통해 Bean의 설정 정보를 직관적으로 관리할 수 있다.

    ```java
    @Configuration
    public class GamingConfiguration {
    
        @Bean
        public GamingConsole game() {
            return new PackManGame();
        }
    
        @Bean
        public GameRunner run(GamingConsole game) {
            return new GameRunner(game);
        }
    }
    ```
- Annotations vs XML Configuration

    | 구분 | Annotations  | XML 구성 |
    | --- | --- | --- |
    | 사용의 용이성 | 매우 쉬움 (소스 가까이에서 정의됨 - 클래스, 메소드 및/또는 변수) | 번거로움 |
    | 간결함 | 예 | 아니요 |
    | POJOs의 깔끔함 | 아니오. POJOs가 Spring Annotations로 인해 오염됨 | java 코드에 변경이 없음 |
    | 유지보수의 용이성 | 예 | 아니요 |
    | 사용 빈도 | 거의 모든 최근 프로젝트에서 사용 | 거의 없음 |
    | 추천사항 | 둘 중 하나를 사용해도 좋지만 일관성을 유지할 것 |  |
    | 디버깅의 난이도 | 어려움 | 보통 |

## **스프링 컨테이너로 빈 관리하기:**

- **빈 정의하기:** 스프링 컨테이너에 의해 관리되어야 하는 객체를 빈으로 정의한다. 빈의 정의에는 빈의 클래스 타입, 생명주기, 의존성 등이 포함된다.
- **빈 의존성 주입하기:** 빈 사이의 의존성은 스프링 컨테이너에 의해 자동으로 주입된다. 이를 위해 @Autowired와 같은 애노테이션을 사용할 수 있다.

```java
@Component
class YourBusinessClass {

    //필드주입
    @Autowired
    Dependency1 dependency1;

    @Autowired
    Dependency2 dependency2;

    //세터주입
    @Autowired
    public void setDependency1(Dependency1 dependency1) {
        System.out.println("Setter Injection - setDependency1");
        this.dependency1 = dependency1;
    }

    @Autowired
    public void setDependency2(Dependency2 dependency2) {
        System.out.println("Setter Injection - setDependency2");
        this.dependency2 = dependency2;
    }

    //생성자 주입
    public YourBusinessClass(Dependency1 dependency1, Dependency2 dependency2) {
        System.out.println("Constructor Injection - YourBusinessClass");
        this.dependency1 = dependency1;
        this.dependency2 = dependency2;
    }

    @Override
    public String toString() {
        return "Using " + dependency1 + "and" + dependency2;
    }
}

@Component
class Dependency1 {

}

@Component
class Dependency2 {

}

@Configuration
@ComponentScan
public class DepInjectionLauncherApplication {
    public static void main(String[] args) {

        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DepInjectionLauncherApplication.class)) {
            Arrays.stream(context.getBeanDefinitionNames()).forEach(System.out::println);

            System.out.println(context.getBean(YourBusinessClass.class).toString());

        }

    }
}
```