## 1. 스트림이란?
지금까지 컬렉션 및 배열에 저장된 요소를 반복 처리하기 위해서는 for 문을 이용하거나 Iterator(반복자)를 이용했다. 다음은 List 컬렉션에서 요소를 하나씩 처리하는 for문이다.
```java
List<String> list = ...;
for(int i=0; i<list.size(); i++) {
	String item = list.get(i);
}
```
그리고 Set에서 요소를 하나씩 처리하기 위해 Iterator를 다음과 같이 사용했다.
```java
Set<String> set = ...;
Iterator<String> iterator = set.iterator();
while(iterator.hasNext()) {
	String item = iterator.next();
}
```
Java8 부터는 또 다른 방법으로 컬렉션 및 배열의 요소를 반복 처리하기 위해 스트림Stream을 사용할 수 있다. 스트림은 요소들이 하나씩 흘러가면서 처리된다는 의미를 가지고 있다. List 컬렉션에서 요소를 반복 처리하기 위해 스트림을 사용하면 다음과 같다.
```java
Stream<String> stream = list.stream();
stream.forEach( item -> //item처리);
```
List 컬렉션의 stream() 메소드로 Stream 객체를 얻고,  forEach() 메소드로 요소를 어떻게 처리할지를 람다식으로 제공한다.

Stream은 Iterator와 비슷한 반복자이지만, 다음과 같은 차이점이 있다.
- 내부 반복자이므로 처리 속도가 빠르고 병렬 처리에 효율적이다
- 람다식으로 다양한 요소 처리를 정의할 수 있다.
- 중간 처리와 최종 처리를 수행하도록 파이프 라인을 형성할 수 있다.

## 2. 내부 반복자
for문과 Iterator는 컬렉션의 요소를 컬렉션 바깥쪽으로 반복해서 가져와 처리하는데, 이것을 외부 반복자라고 한다. 반면 스트림은 요소 처리 방법을 컬렉션 내부로 주입시켜서 요소를 반복 처리하는데, 이것을 내부 반복자라 한다.
![](https://velog.velcdn.com/images/co-vol/post/5addba2a-2756-4e53-85ce-4ef7481d6a2e/image.png)
외부 반복자일 경우는 컬렉션의 요소를 외부로 가져오는 코드와 처리하는 코드를 모두 개발자 코드가 가지고 있어야 한다. 반면 내부 반복자일 경우는 개발자 코드에서 제공한 데이터 처리 코드 (람다식)를 가지고 컬렉션 내부에서 요소를 반복 처리한다.

내부 반복자는 멀티 코어 CPU를 최대한 활용하기 위해 요소들을 분배시켜 병렬 작업을 할 수 있다. 하나씩 처리하는 순차적 외부 반복자보다는 효율적으로 반복시킬 수 있는 장점이 있다.
![](https://velog.velcdn.com/images/co-vol/post/5ba44ee3-faae-4195-b886-23eae70260ee/image.png)

## 3. 중간 처리와 최종 처리
스트림은 하나 이상 연결될 수 있다. 다음 그림을 보면 컬렉션의 오리지널 스트림 뒤에 필터링 중간 스트림이 연결될 수 있고, 그 뒤에 매핑 중간 스트림이 연결될 수 있다. 이와 같이 스트림이 연결되어 있는 것을 스트림 파이프라인 이라고 한다.
![](https://velog.velcdn.com/images/co-vol/post/c8ae9047-bea5-47d4-bb2a-62f6298cb22f/image.png)
오리지널 스트림과 집계 처리 사이의 중간 스트림들은 최종 처리를 위해 요소를 걸러내거나(필터링), 요소를 변화시키거나(매핑), 정렬하는 작업을 수행한다. 최종 처리는 중간 처리에서 정제된 요소들을 반복하거나, 집계(카운팅, 총합, 평균) 작업을 수행한다.

다음 그림은 Student 객체를 요소로 가지는 컬렉션에서 Student 스트림을 얻고, 중간 처리를 통해 score 스트림으로 변환한 후 최종 집계 처리로 score 평균을 구하는 과정을 나타낸 것이다.
![](https://velog.velcdn.com/images/co-vol/post/ef8c975c-3c9a-4036-aa43-9aac87e4341f/image.png)

```java
//Student 스트림
Stream<Student> studentStream = list.stream();
//score 스트림
IntStream scoreStream = studentStream.mapToInt( student -> student.getScore() );
//평균 계정
double avg = scoreStream.average()getAsDouble();
```
mapToInt() 메소드는 객체를 int 값으로 매핑해서 IntStream으로 변환시킨다. 어떤 객체를 어떤 int 값으로 매핑할 것인지는 람다식으로 제공해야 한다. student -> student.getScore()는 Student 객체를 getScore()의 리턴값으로 매핑한다. IntStream은 최종 처리를 위해 다양한 메소드를 제공하는데, average() 메소드는 요소들의 평균 값을 계산한다.

메소드 체이닝 패턴을 이용하면 앞의 코드를 다음과 같이 더 간결하게 작성할 수 있다.
```java
double avg = list.stream()
	.mapToInt(student -> student.getScore())
    .average()
    .getAsDouble();
```
스트림 파이프라인으로 구성할 때 주의할 점은 파이프라인의 맨 끝에는 반드시 최종 처리 부분이 있어야 한다는 것이다. 최종 처리가 없다면 오리지널 및 중간 처리 스트림은 동작하지 않는다. 즉, 위코드에 average() 이하를 생략하면 stream(), mapToInt()는 동작하지 않는다.
## 4. 리소스로부터 스트림 얻기
java.util.stream 패키지에는 스트림 인터페이스들이 있다. BaseStream 인터페이스를 부모로 한 자식 인터페이스들은 다음과 같은 상속 관계를 이루고 있다.
![](https://velog.velcdn.com/images/co-vol/post/e8d9f230-4c20-419b-a6d6-5c3c10ae866b/image.png)

BaseStream에는 모든 스트림에서 사용할 수 있는 공통 메소드들이 정의되어 있다. Stream은 객체 요소를 처리하는 스트림이고, IntStream, LongStream, DoubleStream은 각각 기본 타입인 int, long, double 요소를 처리하는 스트림이다.

이 스트림 인터페이스들의 구현 객체는 다양한 리소스로부터 얻을 수 있다. 주로 컬렉션과 배열에서 얻지만, 다음과 같은 리소스로부터 스트림 구현 객체를 얻을 수도 있다.
![](https://velog.velcdn.com/images/co-vol/post/d5a2c6e1-3e13-489a-b916-a84dfdba967c/image.png)

### 1. 컬렉션으로부터 스트림 얻기
java.util.Collection 인터페이스는 스트림과 parallelStream() 메소드를 가지고 있기 때문에 자식 인터페이스인 List와 Set 인터페이스를 구현한 모든 컬렉션에서 객체 스트림을 얻을 수 있다.

### 2. 배열로부터 스트림 얻기
java.util.Arrays 클래스를 이용하면 다양한 종류의 배열로부터 스트림을 얻을 수 있다.

### 3. 숫자 범위로부터 스트림 얻기
IntStream 또는 LongStream의 정적 메소드인 range() 와 rangeClosed() 메소드를 이용하면 특정 범위의 정수 스트림을 얻을 수 있다. 첫 번째 매개값은 시작 수이고 두 번째 매개값은 끝 수인데, 끝 수를 포함하지 않으면 range(), 포함하면 rangeClosed()를 사용한다.

### 4. 파일로부터 스트림 얻기
java.nio.file.Files의 lines() 메소드를 이용하면 텍스트 파일의 행 단위 스트림을 얻을 수 있다. 이는 텍스트 파일에서 한 행씩 읽고 처리할 때 유용하게 사용할 수 있다.
## 5. 요소 걸러내기(필터링)
필터링은 요소를 걸러내는 중간 처리 기능이다. 필터링 메소드에는 다음과 같이 distinct()와 filter()가 있다.
![](https://velog.velcdn.com/images/co-vol/post/5bcbbf35-15cf-4027-8e92-7a78cca85951/image.png)
distinct() 메소드는 요소의 중복을 제거한다. 객체 스트림(Stream)일 경우, equals() 메소드의 리턴값이 true이면 동일한 요소로 판단한다. IntStream, LongStream, DoubleStream은 같은 값일 경우 중복을 제거한다.
![](https://velog.velcdn.com/images/co-vol/post/cfcba537-e14d-415e-83ae-6044bde05b55/image.png)
filter() 메소드는 매개값으로 주어진 Predicate가 true를 리턴하는 요소만 필터링한다.
![](https://velog.velcdn.com/images/co-vol/post/ec60a360-b34f-4757-a101-1b905e3c23fe/image.png)
Predicate는 함수형 인터페이스로, 다음과 같은 종류가 있다.
![](https://velog.velcdn.com/images/co-vol/post/d9b85fca-a592-4a30-b485-d4dece2bc543/image.png)
모든 Predicate는 매개값을 조사한 후 boolean을 리턴하는 test() 메소드를 가지고 있다.
![](https://velog.velcdn.com/images/co-vol/post/e54e3656-4291-42f3-ba2b-35cf3410d304/image.png)
`Predicate<T>`을 람다식으로 표현하면 다음과 같다.
```java
T -> {... return true}
T -> true; //return 문만 있을 경우 중괄호와 return 키워드 생략 가능
```
## 6. 요소 변환(매핑)
매핑은 스트림의 요소를 다른 요소로 변화하는 중간 처리 기능이다. 매핑 메소드는 mapXxx(), asDoubleStream(), boxed(), flatMapXxx() 등이 있다.
### 1. 요소를 다른 요소로 변환
mapXxx() 메소드는 요소를 다른 요소로 변환한 새로운 스트림을 리턴한다. 다음 그림처럼 원래 스트림의 A 요소는 C 요소로, B 요소는 D 요소로 변환해서 C, D 요소를 가지는 새로운 스트림이 생성된다
![](https://velog.velcdn.com/images/co-vol/post/6334d3c6-0f0c-4c8d-b224-db164c2d39d3/image.png)
mapXxx() 메소드
![](https://velog.velcdn.com/images/co-vol/post/f4423d22-d3f6-4ed4-a90b-f922f5f596cb/image.png)
매개타입인 Function은 함수형 인터페이스로, 다음과 같은 종류가 있다.
![](https://velog.velcdn.com/images/co-vol/post/d6273c9a-3be4-4cb3-9c1c-bde660c76d64/image.png)
모든 Function은 매개값을 리턴값으로 매핑(변환)하는 applyXxx()메소드를 가지고 있다.
![](https://velog.velcdn.com/images/co-vol/post/2d27a18a-30bb-4e76-a203-2646821f03b9/image.png)
Function<T, R>을 람다식으로 표현하면 다음과 같다.
```java
T -> { ... return R; }
T -> R
```
기본 타입 간의 변환이거나 기본 타입 요소를 래퍼 객체 요소로 변환하려면 다음과 같은 간편화 메소드를 사용할 수도 있다.
![](https://velog.velcdn.com/images/co-vol/post/eb634ac2-2299-49fd-97b1-6b614043148f/image.png)
### 2. 요소를 복수 개의 요소로 변환
flatMapXxx() 메소드는 하나의 요소를 복수 개의 요소들로 변환한 새로운 스트림을 리턴한다. 다음 그림처럼 원래 스트림의 A 요소를 A1,A2 요소로 변환하고 B 요소를 B1, B2로 변환하면 A1,A2,B1,B2를 가지는 새로운 스트림이 생성된다.
![](https://velog.velcdn.com/images/co-vol/post/9aa1d277-0428-459a-bd74-b3efba8740f9/image.png)

flatMap() 메소드의 종류는 다음과 같다.
![](https://velog.velcdn.com/images/co-vol/post/aa083b47-1325-41f8-962f-6112de7d0626/image.png)

## 7. 요소 정렬
정렬은 요소를 오름차순 또는 내림차순으로 정렬하는 중간 처리 기능이다. 요소를 정렬하는 메소드는 다음과 같다.
![](https://velog.velcdn.com/images/co-vol/post/442058e4-a6a4-4310-8025-ee355cbb30f7/image.png)

### 1. Comparable 구현 객체의 정렬
스트림의 요소가 객체일 경우 객체가 Comparable을 구현하고 있어야만 sorted() 메소드를 사용 하여 정렬할 수 있다. 그렇지 않다면 ClassCastException이 발생한다.
![](https://velog.velcdn.com/images/co-vol/post/6a37830d-fe85-41dd-a865-f3a4e4bdb577/image.png)
만약 내림차순으로 정렬하고 싶다면 다음과 같이 Comparator.reverseOrder() 메소드가 리턴하는 Comparator를 매개값으로 제공하면 된다.
```java
Stream<Xxx> reverseOrderedStream = stream.sorted(Comparator.reverseOrder());
```
### 2. Comparator를 이용한 정렬
요소 객체가 Comparable을 구현하고 있지 않다면, 비교자를 제공하면 요소를 정렬시킬 수 있다.
비교자는 Comparator 인터페이스를 구현한 객체를 말하는데 다음과 같이 같단하게 람다식으로 작성 가능하다.
```java
sorted((o1, o2) -> {...})
```
중괄호 안에는 o1이 o2보다 작으면 음수, 같으면0, 크면 양수를 리턴하도록 작성하면 된다. o1과 o2가 정수일 경우에는 Integer.compare(o1,o2)를, 실수일 경우에는 Double.compare(o1, o2)를 호출해서 리턴값을 리턴해도 좋다.

## 8. 요소를 하나씩 처리(루핑)
루핑은 스트림에서 요소를 하나씩 반복해서 가져와 처리하는 것을 말한다. 루핑 메소드에는 peek()와 forEach() 가 있다.
![](https://velog.velcdn.com/images/co-vol/post/3b8df457-45ca-4c8e-955c-f0b1349276bb/image.png)
peek()과 forEach()는 동일하게 요소를 루핑하지만 peek()은 중간 처리 메소드이고, forEach()는 최종 처리 메소드이다. 따라서 peek()은 최종 처리가 뒤에 붙지 않으면 동작하지 않는다.

매개타입인 Consumer는 함수형 인터페이스로, 다음과 같은 종류가 있다.
![](https://velog.velcdn.com/images/co-vol/post/e003be7b-0010-4c69-9d4c-2983c865b553/image.png)
모든 Consumer는 매개값을 처리(소비)하는 accept() 메소드를 가지고 있다.

![](https://velog.velcdn.com/images/co-vol/post/a34301f5-c71f-4f62-8fab-7d0ba58ed0f7/image.png)
`Consumer<? super T>` 를 람다식으로 표현하면 다음과 같다.
```java
T -> { ... }
T -> 실행문;
```

## 9. 요소 조건 만족 여부(매칭)
매칭은 요소들이 특정 조건에 만족하는지 여부를 조사하는 최종 처리 기능이다. 매칭과 관련된 메소드는 다음과 같다.
![](https://velog.velcdn.com/images/co-vol/post/5bff30e5-dbd6-41ab-b67c-257551dfac2b/image.png)
![](https://velog.velcdn.com/images/co-vol/post/4e6a6e26-567f-478b-bb17-34428ca4aabb/image.png)
allMatch(), anyMatch(), noneMatch() 메소드는 매개값으로 주어진 Predicate가 리턴하는 값에 따라 true 또는 false를 리턴한다.  예를 들어 allMatch()는 모든 요소의 Predicate가 true를 리턴해야만 true를 리턴한다.

## 10. 요소 기본 집계
집계는 최종 처리 기능으로 요소들이 처리해서 카운팅, 합계, 평균값, 최대값, 최소값등과 같이 하나의 값으로 산출하는 것을 말한다. 즉, 대량의 데이터를 가공해서 하나의 값으로 축소하는 리덕션이라고 볼 수 있다.

### 1. 스트림이 제공하는 기본 집계
스트림은 카운팅, 최대, 최소, 평균, 합계 등을 처리하는 다음과 같은 최종 처리 메소드를 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/0ea84ffe-bafd-41e8-a977-7b0b863c1968/image.png)
집계 메소드가 리턴하는 OptionalXXX는 Optional, OptionalDouble, OptionalInt, OptionalLong 클래스를 말한다. 이들은 최종값을 저장하는 객체로 get(), getAsDouble(), getAsInt(), getAsLong() 을 호출하면 최종값을 얻을 수 있다.

### 2. Optional 클래스
Optional, OptionalDouble, OptionalInt, OptionalLong 클래스는 단순히 집계값만 저장하는 것이 아니라, 집계값이 존재하지 않는 경우 디폴트 값을 설정하거나 집계값을 처리하는 Consumer를 등록할 수 있다. 다음은 Optional 클래스가 제공하는 메소드이다.
![](https://velog.velcdn.com/images/co-vol/post/1d96b7a8-129d-40bd-8679-e2befb84eaf5/image.png)
컬렉션의 요소는 동적으로 추가되는 경우가 많다. 만약 컬렉션에 요소가 존재하지 않으면 집계 값을 산출할 수 없으므로 NoSuchElementException 예외가 발생한다. 하지만 앞의 표에 언급되어 있는 메소드를 이용하면 예외 발생을 막을 수 있다.

예를 들어 평균을 구하는 average를 최종 처리에서 사용하는 경우, 다음과 같이 3가지 방법으로 요소 가 없는 경우를 대비할 수 있다.
1. isPresent()메소드가 true를 리턴한 때만 집계값을 얻는다.
```java
OptionalDouble optionalAvg = stream.average();
if(optionalAvg.isPresent()) {
	//값 얻기
} else {
	//값이 없을때 경우 처리
}
```
2. orElse() 메소드로 집계값이 없을 경우를 대비해서 디폴트 값을 정한다.
```java
OptionalDouble optionalAvg = stream.average().orElse(0.0);
```
3. ifPresent()메소드로 집계값이 있을 경우에만 동작하는 Consumer 람다식을 제공한다.
```java
stream
	.average()
    .ifPresent(a -> //동작);
```
## 11. 요소 커스텀 집계
스트림은 기본 집계 메소드인 sum(), average(), count(), max(), min()을 제공하지만, 다양한 집계 결과물을 만들 수 있도록 reduce() 메소드도 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/6376ceb8-944e-4164-886d-a087af1a418b/image.png)
매개값인 BinaryOperator는 함수형 인터페이스이다. BinaryOperator는 두 개의 매개값을 받아 하나의 값을 리턴하는 apply() 메소드를 가지고 있기 때문에 다음과 같이 람다식을 작성할 수 있다.
```java
(a, b) -> { ... return 값
(a, b) -> 값
```
reduce()는 스트림에 요속가 없을 경우 예외가 발생하지만, identity 매개값이 주어지면 이 값을 디폴트 값으로 리턴한다. 다음 중 왼쪽 코드는 스트림에 요소가 없을 경우 NoSuchElementException을 발생 시키지만, 오른쪽 코드는 디퐅트 값(identity)인 0을 리턴한다.
![](https://velog.velcdn.com/images/co-vol/post/33a54462-4dad-4b5c-a71d-4a44d10fd73f/image.png)

## 12. 요소 수집
스트림은 요소들이 필터링 또는 매핑한 후 요소들이 수집하는 최종 처리 메소드인 collect() 를 제공 한다. 이 메소드를 이용하면 필요한 요소만 컬렉션에 담을 수 있고, 요소들을 그룹핑한 후에 집계도 할 수 있다.

### 1. 필터링한 요소 수집
Stream의 collect(Collector<T, A, R> coollector) 메소드는 필터링 또는 매핑된 요소들을 새로운 컬렉션에 수집하고, 이 컬렉션을 리턴한다. 매개값인 Collector는 어떤 요소를 어떤 컬렉션에 수집할 것인지를 결정한다.
![](https://velog.velcdn.com/images/co-vol/post/b34b91b2-6bdd-4efd-a161-21f70e19b49a/image.png)
타입 파라미터의 T는 요소, A는 누적기, R은 요소갖 저장될 컬렉션이다. 풀어서 해석하면 T 요소를 A 누적기가 R에 저장한다는 의미이다. Collector의 구현 객체는 다음과 같이 Collectors 클래스의 정적 메소드로 얻을 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/550af67b-a18d-445d-8fac-8ec6c7e10627/image.png)

리턴값인 Collector를 보면 A(누적기)가 ?로 되어 있는데, 이것은 Collector가 List, Set, Map 컬렉션에 요소를 저장하는 방법을 알고 있어 별도의 누적기가 필요 없기 때문이다.

다음은 Student 스트림에서 남학생만 필터링해서 별도의 List로 생성하는 코드이다.
```java
List<Student> maleList = totlaList.stream()
	.filter(s -> s.getSex().equals("남"))
    .collect(Collectors.toList());
```
다음은 Student 스트림에서 이름을 키로, 점수를 값으로 갖는 Map 컬렉션을 생성하는 코드이다.
```java
Map<String, Integer> map = totalList.stream()
	.collect(
    	Collectors.toMap(
        	s -> s.getName(),
            s -> s.getScore()
        )
    )
```
Java16 부터는 좀 더 편리하게 요소 스트림에서 List 컬렉션을 얻을 수 있다. 스트림에서 바로 toList() 메소드를 사용하면 된다.
```java
List<Student> maleList = totalList.stream()
	.filter( s -> s.getSex().equals("남") )
    .toList();
```

### 2. 요소 그룹핑
collect() 메소드는 단순히 요소를 수집하는 기능 이외에 컬렉션의 요소들을 그룹핑해서 Map 객체를 생성하는 기능도 제공한다. Collectors.groupingBy() 메소드에서 얻은 Collector를 collect() 메소드를 호출할 때 제공하면 된다.
![](https://velog.velcdn.com/images/co-vol/post/1383487f-c202-4e4e-a596-56558cac18ae/image.png)
groupingBy()는 Function을 이용해서 T를 K로 매핑하고, K를 키로 해 `List<T>`를 값으로 갖는 Map 컬렉션을 생성한다.![](https://velog.velcdn.com/images/co-vol/post/01f614dd-5190-47cd-b88e-2b2b150a70fe/image.png)
다음은 "남", "여" 를 키로 설정하고 `List<Student>`를 값으로 갖는 Map을 생성하는 코드이다.
```java
Map<String, List<Student>> map = totalList.stream()
	.collect(
    	Collectors.groupingBy(s -> s.getSex()) // 그룹핑 키 리턴
    )
```
Collectors.groupingBy() 메소드는 그룹핑 후 매핑 및 집계(평균, 카운팅, 연결, 최대, 최소, 합계)를 수행할 수 있도록 두 번째 매개값인 Collector를 가질 수 있다. 다음은 두 번째 매개값으로 사용될 Collector를 얻을 수 있는 Collectors의 정적 메소드이다.
![](https://velog.velcdn.com/images/co-vol/post/c430a07f-9edc-4376-9cff-0b516ed67ad9/image.png)
다음은 학생들을 성별로 그룹핑하고 각각의 평균 점수를 구해서 Map으로 얻는 코드이다
```java
Map<String, Double> map = totalList.stream()
	.collect(
    	Collectors.groupingBy(
        	s -> s.getSex(),
            Collectors.averagingDouble(s -> getScore())
        )
    )
```
## 13. 요소 병렬 처리
요소 병렬 처리란 멀티 코어 CPU 환경에서 전체 요소를 분할해서 각각의 코어가 병렬 적으로 처리하는 것을 말한다. 요소 병렬 처리의 목적은 작업 처리 시간을 줄이는 것에 있다. 자바는 요소 병렬 처리를 위해 병렬 스트림을 제공한다.

### 1. 동시성과 병렬성
멀티 스레드는 동시성 또는 병렬성으로 실행되기 때문에 이들 용어에 대해 정확히 이해하는 것이 좋다. 동시성은 멀티 작업을 위해 멀티 스레드가 하나의 코어에서 번갈아 가며 실행 하는 것을 말하고, 병렬성은 멀티 작업을 위해 멀티 코어를 각각 이용해서 병렬로 실행하는 것을 말한다.
![](https://velog.velcdn.com/images/co-vol/post/079765cd-f608-40f6-be00-90651fff7a72/image.png)
동시성은 한 시점에 하나의 작업만 실행한다. 번갈아 작업을 실행하는 것이 워낙 빠르다보니 동시에 처리되는 것처럼 보일 뿐이다. 병렬성은 한 시점에 여러 개의 작업을 병렬로 실행하기 때문에 동시성 보다는 좋은 성능을 낸다.

병렬성은 데이터 병렬성과 작업 병렬성으로 구분할 수 있다.
**데이터 병렬성**
데이터 병렬성은 전체 데이터를 분할해서 서브 데이터셋으로 만들고 이 서브 데이터셋들을 병렬 처리해서 작업을 빨리 끝내는 것을 말한다. 자바 병렬 스트림은 데이터 병렬성을 구현한 것이다.
**작업 병렬성**
작업 병렬성은 서로 다른 작업을 병렬 처리하는 것을 말한다. 작업 병렬성의 대표적인 예는 서버 프로그램이다. 서버는 각각 클라이언트에서 요청한 내용을 개별 스레드에서 병렬로 처리한다.

### 2. 포크조인 프레임워크
자바 병렬 스트림은 요소들을 병렬 처리하기 위해 포크조인 프레임워크를 사용한다.포크조인 프레임워크는 포크 단계에서 전체 요소들을 서브 요소셋으로 분할하고, 각각의 서브 요소셋을 멀티 코어에서 병렬로 처리한다. 조인 단계에서는 서브 결과를 결합해서 최종 결과를 만들어낸다.

예를 들어 쿼드 코어 CPU에서 병렬 스트림으로 요소들을 처리할 경우 먼저 포크 단계에서 스트림의 전체 요소들을 4개의 서브 요소셋으로 분할한다. 그리고 각각의 서브 요소셋을 개별 코어에서 처리하고, 조인 단계에서는 3번의 결합 과정을 거쳐 최종 결과를 산출한다.
![](https://velog.velcdn.com/images/co-vol/post/802c2c0b-1dc3-4224-a891-36798e4d7fef/image.png)
병렬 처리 스트림은 포크 단계에서 요소를 순서대로 분할하지 않는다. 이해하기 쉽도록 위 그림에서 는 앞에서부터 차례대로 4등분 했지만, 내부적으로 요소들을 나누는 알고리즘이 있기 때문에 개발자는 신경 쓸 필요가 없다.

포크조인 프레임워크는 병렬 처리를 위해 스레드풀을 사용한다. 각각의 코어에서 서브 요소셋을 처리하는 것은 작업 스레드가 해야 하므로 스레드 관리가 필요하다. 포크조인 프레임워크는 ExecutorService의 구현 객체인 ForkJoinPool을 사용해서 작업 스레드를 관리한다.
![](https://velog.velcdn.com/images/co-vol/post/26c6c01b-45ea-4bb3-a55e-83c1d2624a25/image.png)
### 3. 병렬 스트림 사용
자바 병렬 스트림을 이용할 경우에는 백그라운드에서 포크조인 프레임워크가  사용되기 때문에 개발자는 매우 쉽게 병렬 처리를 할 수 있다. 병렬 스트림은 두 가지 메소드로 얻을 수 있다.
![업로드중..](blob:https://velog.io/b0be7ed8-7e76-4ad9-b7db-65595fd15f38)
parallelStream() 메소드는 컬렉션(List, Set)으로부터 병렬 스트림을 바로 리턴한다. parallel() 메소드는 기존 스트림을 병렬 처리 스트림으로 변환한다.


### 4. 병렬 처리 성능
스트림 병렬 처리가 스트림 순차 처리보다 항상 실행 성능이 좋다고 판단해서는 안 된다. 그 전에 먼저 병렬 처리에 영향을 미치는 3가지 요인을 잘 살펴보아야 한다.
**요소의 수와 요소당 처리 시간**
컬렉션에 전체 요소의 수가 적고 요소당 처리 시간이 짧으면 일반 스트림이 병렬 스트림보다 빠를 수 있다. 병렬 처리는 포크 및 조인 단계가 있고, 스레드 풀을 생성하는 추가적인 비용이 발생하기 때문이다.

**스트림 소스의 종류**
ArrayList와 배열은 인덱스로 요소를 관리하기 때문에 포크 단계에서 요소를 쉽게 분리할 수 있어 병렬 처리 시간이 절약된다. 반면에 HashSet, TreeSet은 요소 분리가 쉽지 않고, LinkedList 역시 링크를 따라가야 하므로 요소 분리가 쉽지 않다. 따라서 이 소스들은 상대적으로 병렬 처리가 늦다.

**코어의 수**
CPU 코어(Core)의 수가 많으면 많을수록 병렬 스트림의 성능은 좋아진다. 하지만 코어의 수가 적을 경우에는 일반 스트림이 더 빠를 수 있다. 병렬 스트림은 스레드 수가 증가하여 동시성이 많이 일어나므로 오히려 느려진다.