## 1. 제네릭이란?
다음과 같이 Box 클래스를 선언하려고 한다. Box에 넣을 내용물로 content 필드를 선언하려고 할때, 타입을 무엇으로 해야 할까?
```java
public class Box {
	public ? content;
}
```
Box는 다양한 내용물을 저장해야 하므로 특정 클래스 타입으로 선언할 수 없다. 그래서 당음과 같이 Object 타입으로 선언한다.
```java
public class Box {
	public Object content;
}
```
Object 타입은 모든 클래스의 최상위 부모 클래스이다. 그렇기 떄문에 모든 객체는 부모 타입인 Object로 자동 타입 변환이 되므로 content 필드에는 어떤 객체는 대입이 가능하다.
```java
Box box = new Box();
box.content = 모든 객체
```
문제는 Box 안의 내용물을 얻을 때이다. content는 Object 타입이므로 어떤 객체가 대입되어 있는지 확실하지 않다. 이때 대입된 내용물의 타입을 안다면 강제 타입 변환을 거쳐 얻을 수 있다. 예를 들어 내용물이 String 타입이라면 (String)으로 강제 타입 변환해서 내용물을 얻는 식이다.
```java
String content = (String) box.content;
```
그러나 어떤 내용물이 저장되어 있는지 모른다면 instanceof 연산자로 타입을 조사할 수는 있지만 모든 종류의 클래스를 대상으로 조사할 수는 없다. 따라서 Object 타입으로 content 필드를 선언 하는 것은 좋은 방법이 아니다.

Box를 생성하기 전에 우리는 어떤 내용물을 넣을지 이미 알고있다. 따라서 Box를 생성할 때 저장할 내용물의 타입을 미리 알려주면 Box는 content에 무엇이 대입되고, 읽을 때 어떤 타입으로 제공할지를 알게 된다. 이것이 제네릭이다.

**제네릭(Generic)이란 결정되지 않은 타입을 파라미터로 처리하고 실제 사용할 때 파라미터를 구체적인 타입으로 대체시키는 기능**

다음은 Box클래스에서 결정되지 않은 content의 타입을 T라는 타입 파라미터로 정의한 것이다.
```java
public class Box<T> {
	public T content;
}
```
`<T>`는 T가 타입 파라미터임을 뜻하는 기호(단지 T를 많이 사용함 다른것도 가능)로, 타입이 필요한 자리에 T를 사용할 수 있음을 알려주는 역할을 한다. 여기에서 Box클래스는 T를 content 필드의 타입으로 사용한다. 즉 Box 클래스는 T가 무엇인지 모르지만, Box 객체가 생성될 시점에 다른 타입으로 대체된다는 것을 알고 있다.

Box의 content를 String으로 저장
```java
Box<String> box = new Box<String>();
box.content = "String";
Stirng content = box.content
```
Box의 content를 Integer로 저장
```java
Box<Integer로> box = new Box<Integer로>();
box.content = `;
int content = box.content
```
타입 파라미터를 대체하는 타입은 클래스 및 인터페이스 이므로 기본 타입은 타입 파라미터의 대체 타입이 될 수 없다. 그리고 변수 선언할 때와 동일한 타입으로 호출하고 싶다면 생성자 호출 시 생성자에는 타입을 명시 하지 않아도 된다.
```java
Box<String> box = new Box<>();
```

## 2. 제네릭 타입
제네릭 타입은 결정되지 않은 타입을 파라미터로 가지는 클래스와 인터페이스를 말한다. 제네릭 타입은 선언부에`<>`부호가 붙고 그 사이에 타입 파라미터들이 위치한다.
```java
public class 클래스명<A, B, ...> {}
public interface 인터페이스명<A, B, ...> {}
```
타입 파라미터는 변수명과 동일한 규칙에 따라 작성할 수 있지만 대문자 알파벳 한 글자로 표현한다. 외부에서 제네릭 타입을 사용하려면 타입 파라미터에 구체적인 타입을 지정해야 한다. 만약 지정하지 않으면 Object 타입이 암묵적으로 사용된다.

## 3. 제네릭 메소드
제네릭 메소드는 타입 파라미터를 가지고 있는 메소드를 말한다. 타입 파라미터가 메소드 선언부에 정의된다는 점에서 제네릭 타입과 차이가 있다. 제네릭 메소드는 리턴 타입 앞에 <> 기호를 추가하고 타입 파라미터를 정의한 뒤, 리턴 타입과 매개변수 타입에서 사용한다.
```java
public <A, B, ...> 리턴타입 메소드명(매개변수, ...) {}

public <T> Box<T>() boxing(T t) {}
```

## 4. 제한된 타입 파라미터
경우에 따라서는 타입 파라미터를 대체하는 구체적인 타입을 제한할 필요가 있다. 예를 들어 숫자를 연산하는 제네릭 메소드는 대체 타입으로 Number 또는 자식 클래스(Byte, Short, Integer, Long, Double)로 제한할 필요가 있다.

이처럼 모든 타입으로 대체할 수 없고, 특정 타입과 자식 또는 구현에 있는 타입만 대체할 수 있는 타입 파라미터를 제한된 타입 파라미터(bounded type parameter)라고 한다.
```java
public <T extends 상위타입> 리턴타입 메소드(매개변수, ...) {}
```
상위 타입은 클래스뿐만 아니라 인터페이스도 가능하다. 인터페이스라고 해서 implements를 사용 하지는 않는다. 다음은 Number 타입과 자식 클래스(Byte, Short, Integer, Long, Double)에만 대체 가능한 타입 파라미터를 정의한 것이다.

```java
public <T extends Number> boolean compare(T t1, T t2) {
	double v1 = t1.doubleValue() //Number의 doubleValue() 메소드 사용
    double v2 = t2.doubleValue() 
    return (v1 = v2);
}
```

타입 파라미터가 Number 타입으로 제한되면서 Object의 메소드뿐만 아니라 Number가 가지고 있는 메소드도 사용할 수 있다. 위 코드에서 doubleValue() 메소드는 Number 타입에 정의되어 있는 메소드로, double 타입 값을 리턴한다

## 5. 와일드카드 타입 파라미터
제네릭 타입을 매개값이나 리턴 타입으로 사용할 때 타입 파라미터로 ?(와일드카드)를 사용할 수 있다. ?는 범위에 있는 모든 타입으로 대체할 수 있다는 표시이다. 예를 들어 다음과 같은 상속 관계가 있다고 가정해보자.
![](https://velog.velcdn.com/images/co-vol/post/84b9f884-6971-4d51-bf79-fb24c7c2a638/image.png)
타입 파라미터의 대체 타입으로 Student와 자식 클래스인 HighStudent와 MiddleStudent만 가능하도록 매개변수를 다음과 같이 선언할 수 있다.
```java
리턴타입 메소드명(제네릭타입<? extends Student> 변수) {}
```
반대로 Worker와 부모 클래스인 Person만 가능하도록 매개변수를 다음과 같이 선언할 수 있다.
```java
리턴타입 메소드명(제네릭타입<? super Worker> 변수) {}
```
어떤 타입이든 가능하도록 매개변수를 선언할 수도 있다.
```java
리턴타입 메소드명(제네릭타입<?> 변수) {}
```
