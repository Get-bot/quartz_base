## 1. API 도큐먼트
자바 표준 모듈에서 제공하는 라이브러리는 방대하기 때문에 쉽게 찾아서 사용할 수 있도록 도와주는 API 도큐먼트가 있다.
라이브러리가 클래스와 인터페이스의 집합이라면, API 도큐먼트는 이를 사용하기위한 방법을 기술한 것이다.

[자바 API 도큐먼트](https://docs.oracle.com/java/javase/index.html)

<img src="https://velog.velcdn.com/images/co-vol/post/07e7abd6-0046-48a1-9540-fdfbeaaa397a/image.png" width="80%">
자바 버전을 선택후 왼쪽 메뉴에서 [API Document] 를 클릭하면 각 버전에 따른 API 도큐먼트 페이지가 열린다.

### 1. 클래스 선언부 보기
API 도큐먼트에서 클래스가 어떻게 정의되었는지 보려면 (1) 선언부를 보면 된다. 여기서는 클래스가 final인지 abstract 인지를 알 수 있고, 부모 클래스와 구현 인터페이스를 볼 수 있다. 전체 상속 관계를 보려면 (2)상속 계층도를 보면 된다.
<img src="https://velog.velcdn.com/images/co-vol/post/177d40ff-163e-4213-a320-2c059e5ba7e7/image.png" width="80%">
### 2. 구성 멤버 보기
클래스가 가지고 있는 멤버를 보려면 상단 메뉴의 SUMMARY를 활용한다. SUMMARY는 선언된 멤버별로 이동하는 링크를 제공한다. 링크가 있으면 공개된(public, proteted) 멤버가 있다는 뜻이고, 링크가 없다면 공개된 멤버가 없다는 뜻이다.
- NESTED: 중첩 클래스/중첩 인터페이스 목록
- FIELD: 필드 목록은 static 여부와 필드 타입,필드명과 그에대한 간단한 설명이 있다.
- CONSTR: 생성자 목록은 생성자의 매개변수 타입과 간단한 설명이 있다.
- METHOD: 메소드 목록은 메소드 들과 static 여부,리턴 타입, 매개변수 타입 및 개수를 알 수 있다.

## 2. java.base 모듈
java.base는 모든 모듈이 의존하는 기본 모듈로. 모듈 중 유일하게 requires하지 않아도 사용할 수 있다.
### 1. 주요패키지
- java.lang: 자바 언어의 기본 클래스 제공
- java.util: 자료 구조와 관련된 컬렉션 클래스 제공
- java.test: 날짜 및 숫자를 원하는 형태로의 문자열로 만들어 주는 포맷 클래스 제공
- java.time: 날짜 및 시간을 조작하거나 연산하는 클래스 제공
- java.io: 입출력 스트림 클래스 제공
- java.net: 네트워크 통신과 관련된 클래스를 제공
- java.nio: 데이터 저장을 위한 Buffer 및 새로운 입출력 클래스 제공

### 2. java.lang 패키지
java.lang은 자바 언어의 기본적인 클래스를 담고 있는 패키지로, 이 패키지에 있는 클래스와 인터페이스는 import 없이 사용할 수 있다.
- Object: 자바 클래스의 최상위 클래스로 사용
- System: 키보드 데이터입력,모니터(콘솔)출력,프로세스 종료,진행시간Read,시스템 속성Read
- String: 문자열 저장 조작
- StringBuilder: 효율적인 문자열 조작
- java.util.StringTokenizer: 구분자로 연결된 문자열 분리
- Byte, Short, Character, Integer, Folat, Double, Boolean: 문자열 기본타입 변환, 기본 타입의 값 포장
- Math: 수학 계산에 사용
- Class: 클래스의 메타 정보(이름, 구성 멤버)등을 조사할 때 사용

## 3. Object 클래스
클래스를 선언할 때 extends 키워드로 다른 클래스를 상속하지 않으면 암시적으로 java.lang.Object 클래스를 상속한다. 따라서 자바의 모든 클래스는 Object의 자식이거나 자손 클래스이다.
![](https://velog.velcdn.com/images/co-vol/post/060cf433-b2a6-4865-b252-5e3338263235/image.png)
### 1. 주요 메소드
- boolean equals(Object obj): 객체의 번지를 비교하고 결과를 리턴
- int hashCode(): 객체의 해시코드를 리턴
- String toString(): 객체 문자 정보를 리턴

### 2. 객체 동등비교
객체가 비록 달라도 내부의 데이터가 같은지를 비교하는 것 예를 들어 String은 equals() 메소드를 재정의해서 내부 문자열이 같은지를 비교

```java
public boolean equals(Object obj)
```
equals() 메소드의 매개변수 타입이 Object이므로 자동 타입 변환에 의해 모든 객체가 매개값으로 대입될 수 있다.

### 3. 객체 해시코드
객체 해시코드란 객체를 식별하는 정수를 말한다. Object의 hashCode() 메소드는 객체의 메모리 번지를 이용해서 해시코드를 생성하기 때문에 객체마다 다른 정수값을 리턴한다. 두 객체가 동등한지 비교할 때 사용
```java
public int hashCode()
```
![](https://velog.velcdn.com/images/co-vol/post/a12a9df3-9def-40ce-98ab-0a381d752d89/image.png)
자바에서 두 객체가 동등함을 비교할 때 hashCode() 와 equals()를 같이 사용하는 경우가 많다.
### 4. 객체 문자 정보
객체의 문자 정보란 객체를 문자열로 표현한 값을 말한다. 기본적으로 Object의 toString() 메소드는 `클래스명@16진수해시코드`로 구성된 문자열을 리턴한다.
![](https://velog.velcdn.com/images/co-vol/post/895dc23a-49d8-4dfd-8d94-fd9e41b9a3a8/image.png)
객체의 문자 정보가 중요한 경우에는 Object의 toString() 메서드를 재정의해서 정보를 리턴해준다. 예를 들어 Date 클래스는 현재 날짜와 시간을, String클래스는 저장된 문자열을 리턴하도록 toString() 메서드를 재정의 하고있다.
### 5. 레코드 선언

데이터 전달을 위한 DTO(Data Transfer Object)를 작성할 때 반복적으로 사용되는 코드를 줄이기 위해 Java14 부터 레코드가 도입되었다.
```java
public record Person(String name, int age) {
}
```
이렇게 선언된 레코드 소스를 컴파일하면 변수의 타입과 이름을 이용해서 private final필들가 자동 생성되고, 생성자 및 Getter 메소드가 자동으로 추가된다. 그리고 hashCode(), equals(), toString() 메소드를 재정의한 코드가 자동 추가된다.

### 6. Lombok 사용
롬복은 JDK에 포함된 표준 라이브러리는 아니지만 자주 사용되는 자동 코드 생성 라이브러리이다.
롬복은 레코드와 마찬가지로 DTO 클래스를 작성할 때 Getter, Setter, hasCode(), equals(), toString() 메소드를 자동 생성하기 때문에 작성할 코드의 양을 줄여준다.

레코드와의 차이점은 필드가 final이 아니며, Getter는 getXXX(boolean의 경우 isXXX)로, Setter는 setXXX로 생성된다.

**롬복 어노테이션**
- **@Data**: @RequriedArgsConstrutor, @Getter, @Setter, @EqualsAndHashCode, @ToString 어노테이션들이 합쳐진 것과 동일
>**@Data를 지양해야 하는 이유**
> 1.무분별한 Setter 남용
> 2.toString으로 인한 양방향 연관관계시 순환 참조 문제 예를들어 객체가 양방향 연관 관계일 경우 toString() 호출시 무한 순환 참조가 발생한다.
- **@NoArgsConstructor**: 기본(매개변수가 없는)생성자
- **@AllArgsConstructor**: 모든 필드를 초기화시키는 생성자 퐇마
- **@RequiredArgsConstructor**: 기본적으로 매개변수가 없는 생성자 포함, 만약 final 또는 @NonNull이 붙은 필드가 있다면 이 필드만 초기화시키는 생성자 포함
- **@Getter**: Getter메소드 포함
- **@Setter**: Setter메소드 포함
- **@EqualsAndHashCode**: equals(), hashCode() 메소드 포함
- **@ToString**: toString() 메소드 포함
## 4. System 클래스
자바 프로그램은 운영체제상이 아님 JVM 위에서 실행되기 때문에 운영체제의 모든 기능을 자바 코드로 직접 접근하기란 어렵다. System 클래스를 이용하면 운영체제의 일부 기능을 이용할 수 있다.

System 클래스의 static필드와 메소드를 이용하면 프로그램 종료, 키보드 입력, 콘솔(모니터) 출력, 현재 시간 읽기, 시스템 프로퍼티 읽기 등이 가능하다
#### 필드
- **out**: 콘솔(모니터)에 문자 출력
- **err**: 콘솔(모니터)에 에러 내용 출력
- **in**: 키보드 입력
#### 메소드
- **exit(int status)**: 프로세스 종료
- **currentTimeMillis()**: 현재 시간을 밀리초 단위의 long 값으로 리턴
- **nanoTime()**: 현재 시간을 나노초 단위의 long 값으로 리턴
- **getProperty()**: 운영체제와 사용자 정보 제공
- **getenv()**: 운영체제의 환경 변수 정보 제공

### 1. 콘솔출력
out 필드를 이용하면 콘솔에 원하는 문자열을 출력할 수 있다. err필드도 out필드와 동일한데, 차이점은 err는 빨간색으로 출력되는 것이다.
```java
System.out.printIn("consle Message"):
System.err.printIn("Error Message");
```
### 2. 키보드입력
in 필드를 이용해서 read() 메소드를 호출하면 입력된 키의 코드값을 얻을 수 있다.
```java
int keyCode = System.in.read();
```
read()메소드는 호출과 동시에 키 코드를 읽는 것이 아니라, `Enter`키를 누르기 전까지는 대기 하다 `Enter`키 입력시 입력했던 키들을 하나씩 읽기 시작한다. 단, read()메소드는 IOException을 발생할 수 있으므로 예외 처리가 필요하다.
### 3. 프로세스 종료
운영체제는 실행 중인 프로그램을 프로세스로 관리한다. 자바 프로그램을 시작하면 JVM프로세스가 생성되고, 이 프로세스가 main() 메소드를 호출한다. 프로세스를 강제 종료하고 싶다면 System.exit() 메소드를 사용한다
```java
System.exit(int status)
```
exit() 메소드는 int 매개값이 필요한데, 이 값을 종료 상태값이라 한다. 종료 상태값으로 어떤 값이든 할당 가능하나, 관례적으로 정상 종료 0, 비정상 종료 1 or -1 로 할당 해준다.
### 4. 진행시간 읽기
System 클래스의 currentTimeMillis() 메소드와 nanoTime() apthemsms 1970년 1월 1일 0시부터 시작해서 현재까지 진행된 시간을 리턴한다.
- long currentTimeMillis(): 1/1000 초 단위로 진행된 시간을 리턴
- long nanoTime(): 1/10⁹ 초 단위로 진행된 시간을 리턴

위 두 메소드는 프로그램 처리 시간을 측정하는 데 주로 사용된다. 프로그램 시작과 끝에 배치후 그 차이를 구하면 처리 시간이 나온다.
### 5. 시스템 프로퍼티 읽기
System Property란 자바 프로그램이 시작될 때 자동 설정되는 시스템의 속성을 말한다.
운영체제 종류 및 사용자 저오, 자바 버전 등의 기본 사양 정보가 해당된다.
#### 주요속성
- **java.specification.version**: 자바 스펙 버전
- **java.home**: JDK 디렉토리 경로
- **os.name**: 운영체제
- **user.name**: 사용자 이름
- **user.home**: 사용자 홈 디렉토리 경로
- **user.dir**: 현재 디렉토리 경로
## 6. 문자열 클래스
### 주요 클래스
- **String**: 문자열을 저장하고 조작할 떄 사용
- **StringBuilder**: 효율적인 문자열 조작 기능이 필요할 때 사용
- **StringTokenizer**: 구분자로 연결된 문자열을 분리할 때 사용
### 1. String 클래스
String 클래스는 문자열을 저장하고 조작할 때 사용한다. 문자열 리터럴은 자동으로 String 객체로 생성되지만, String 클래스의 생성자로 직접 객체 생성도 가능하다.
### 2. StringBuilder 클래스
String은 내부 문자열을 수정할 수 없다. 따라서 잦은 문자열 변경 작업을 한다면 String 보다는 StringBuilder를 사용하는 것이 좋다.

StringBuilder는 내부 버퍼에 문자열을 저장해두고 그 안에서 추가, 수정, 삭제 작업을 하도록 설계 되어있다.

#### 조작 메소드
- **append(기본값 | 문자열)**: 문자열을 끝에 추가
- **insert(위치, 기본값 | 문자열)**: 문자열을 지정 위치에 추가
- **delete(시작 위치, 끝 위치)**: 문자열 일부 삭제
- **replace(시작 위치, 끝 위치, 문자열)**: 문자열 일부 대체
- **toString()**:문자열 리턴
  toString() 을 제외한 메소드는 StringBuilder를 리턴하기 때문에 메소드 체이닝이 가능하다.

### 3. StringTokenizer
문자열이 구분자(delimiter)로 연결되어 있을 경우, 구분자를 기준으로 문자열을 분리하려면 Stirng의 split() 메소드를 이용하거나 java.util 패키지의 StringTokenizer 클래스를 이용할 수 있다. split은 정규 표현식으로 구분하고, StringTokenizer는 문자로 구분한다.

#### split
```java
String data = "A&B,C,D-E";
String[] name = data.split("[&,-]");
```
#### StringTokenizer
```java
String data = "홍길동/이수홍/박연수";
StringTokenizer st = new StringTokenizer(data, "/");
```
StringTokenizer 객체가 생성되면 아래 메소드를 통해 분리된 문자열을 얻을 수 있다.
- **countTokens()**: 분리할 수 있는 문자열의 총 수
- **hasMoreTokens()**: 남아 있는 문자열이 있는지 여부
- **nextToken()**: 문자열을 하나씩 가져옴
  nextToken()은 분리된 문자열을 하나씩 가져오고, 더 이상 가져올 문자열이 없으면 예외가 발생되기 때문에 hasMoreToken() 메소드로 가져올 문자열이 있는지 먼저 체크하는것이 좋다.

## 7. 포장 클래스
자바는 기본 타입(byte, char, short, int, long, float, double, boolean)의 값을 갖는 객체를 생성할 수 있다. 이런 객체를 포장(Wrapper) 객체라고 한다.

포장 객체를 생성하기 위한 클래스는 java.lang 패키지에 포함되어 있다.

| 기본 타입 | 포장 클래스 |
| :--- | :--- |
| `byte` | `Byte` |
| `char` | `Character` |
| `short` | `Short` |
| `int` | `Integer` |
| `long` | `Long` |
| `float` | `Float` |
| `double` | `Double` |
| `boolean` | `Boolean` |

포장 객체는 포장하고 있는 기본 타입의 값을 변경할 수 없고, 단지 객체로 생성하는 데 목적이 있다.
이런 객체가 필요한 이유는 컬렉션 객체 때문이다. 컬렉션 객체는 기본 타입의 값은 저장할 수 없고, 객체만 저장할 수 있다.

### 1. 박싱과 언박싱
기본 타입의 값을 포장 객체로 만드는 과정을 박싱(boxing)이라고 하고, 포장 객체에서 기본 타입의 값을 얻어내는 과정을 언박싱(unboxing)이라고 한다.

**박싱**은 포장 클래스 변수에 기본 타입이 대입될 때 발생한다.
```java
Integer obj = 100;
```
**언박싱**은 기본 타입 변수에 포장 객체가 대입될 때 그리고 연산 과정에서도 발생한다.
```java
int value = obj;
int value2 = obj + 50; //언박싱 후 연산

```
### 2. 문자열을 기본 타입으로 변환
포장 클래스는 문자열을 기본 타입 값으로 변환할 때도 사용된다. 대부분 포장 클래스에는 `parse+기본타입`명으로 되어있는 정적(static) 메소드가 있다. 이 메소드는 문자열을 해당 기본 타입 값으로 변환한다.

### 3. 포장 값 비교
포장 객체는 내부 값을 비교하기 위해 ==와 !=연산자를 사용할 수 없다. 이 연산은 내부의 값을 비교하는 것이 아니라 포장 객체의 번지를 비교하기 때문이다. 예를 들어 다음 두 Integer 객체는 300 이라는 동일한 값을 갖고 있지만 == 연산의 결과는 false가 나온다.

```java
Integer obj1 = 300;
Integer obj2 = 300;
System.out.printIn(obj1 == obj2);
```

예외로는 포장 객체의 효율적 사용을 위해 다음 범위의 값을 갖는 포장 객체는 공유된다. ==와 !=연산자로 비교 가능하나, 내부 값을 비교하는 것이 아니라 객체 번지를 비교한다!!.

| 타입 | 값의 범위 |
| :--- | :--- |
| `boolean` | `true,false` |
| `char` | `\u0000 ~ \u007f` |
| `byte,short,int` | `-128 ~ 127` |

포장 객체에 정확히 어떤 값이 저장될 지 모르는 상황이라면 ==,!= 연산자의 사용을 지양하는 것이 좋다. 대신 equals() 메소드로 내부 값을 비교할 수 있다.

## 8. 수학 클래스
Math 클래스는 수학 계산에 사용할 수 있는 메소드를 제공한다. Math 클래스가 제공하는 메소드는 모두 정적(static)이므로 Math클래스로 바로 사용이 가능하다.
### 주요 메소드
- **Math.abs()**: 절대값
- **Math.ceil()**: 올림값
- **Math.floor()**: 버림값
- **Math.max()**: 최대값
- **Math.min()**: 최소값
- **Math.random()**: 랜덤값
- **Math.round()**: 반올림값

## 9. 날짜와 시간 클래스
자바는 컴퓨터의 날짜 및 시각을 읽을 수 있도록 java.util 패키지에서 Date와 Calendar 클래스를 제공한다.
- **Date**: 날짜 정보를 전달하기 위해 사용
- **Calendar**: 다양한 시간대별로 날짜와 시간을 얻을 떄 사용
- **LocalDateTime**: 날짜와 시간을 조작할 때 사용

### 1. Date클래스
Date는 날짜를 표현하는 클래스로 객체 간에 날짜 정보를 주고받을 때 사용된다. Date 클래스에는 여러 개의 생성자가 선언되어 있지만 대부분 DepreCated되어 Date()생성자 만 주로 쓰인다.
Date() 생성자는 컴퓨터의 현재 날짜를 읽어 Date 객체로 만든다.
```java
Date currentDate = new Date();
```
현재 날짜를 문자열로 얻고 싶다면 toString()이 사용 가능하나 영문으로 출력되기 때문에
원하는 문자열로 얻고 싶다면 SimpleDateFormat을 사용하면 된다.
```java
SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy.MM.dd HH:mm:ss");
String currentDate = dateFormat.format(new Date());
```

### 2. Calendar 클래스
Calendar 클래스는 달력을 표현하는 추상 클래스이다. 날짜와 시간을 계산하는 방법이 지역과 문화에 따라 다르기 때문에 특정 역법에 따르는 달력은 자식 클래스에서 구현 되도록 되어 있다.
>**역법**
날짜와 시간을 매기는 방법

특별한 역법을 사용하는 경우가 아니라면 직접 하위 클래스를 만들 필요는 없고 Calendar 클래스의 정적 메소드인 getInstance() 메소드를 이용하면 컴퓨터에 설정되어 있는 시간대를 기준으로
Calendar 하위 객체를 얻을 수 있다.
```java
Calendar now = Calendar.getInstance();
```

Claendar가 제공하는 날짜와 시간에 대한 정보를 얻기 위해서는 get() 메소드를 이용한다.
![](https://velog.velcdn.com/images/co-vol/post/b56565a6-4005-4130-baf6-103b94a56c68/image.png)

Calendar 클래스의 오버로딩된 다른 getInstance() 메소드를 이용하면 미국/로스엔젤레스 와 같은 다른 시간대의 Calendar를 얻을 수 있다 TimeZone 객체를 얻어 getInstance()의 매개값으로 넘겨주면 된다.
```java
TimeZone LosAngelesTimeZone = TimeZone.getTimeZone("Americal/Los_Angeles");
Calendar LosAngelesCalendar = Calendar.getInstance(LosAngelesTimeZone);
```

### 3. 날짜와 시간 조작
Date와 Calendar는 날짜와 시간 정보를 얻기에는 충분하지만, 날짜와 시간을 조작할 수는 없다.
이때는 java.time 패키지의 LocalDateTime 클래스가 제공하는 메소드를 이용하면 쉽게 날짜와 시간 조작이 가능하다.
#### 메소드
- **minusYears(long)**: 년 빼기
- **minusMonths(long)**: 월 빼기
- **minusDays(long)**: 일 빼기
- **minusWeeks(long)**: 주 빼기
- **plusYears(long)**: 년 더하기
- **plusMonths(long)**: 월 더하기
- **plusDays(long)**: 주 더하기
- **plusWeeks(long)**: 일 더하기
- **minusHous(long)**: 시간 빼기
- **minusMinutes(long)**: 분 빼기
- **minusSeconds(long)**: 초 빼기
- **minusNanos(long)**: 나노초 빼기
- **plusHours(long)**: 시간 더하기
- **plusMinutes(long)**: 분 더하기
- **plusSeconds(long)**: 초 더하기

LocalDateTime 클래스를 이용해서 현재 컴퓨터의 날짜와 시간 얻기
```java
LocalDateTime = new LocalDateTime.now();
```
### 4. 날짜와 시간비교
LocalDateTime 클래스는 날짜와 시간을 비교할 수 있는 메소드도 제공한다
#### 메소드
- **isAfter(other)**: 이후 날짜인지 | boolean
- **isBefore(other)**: 이전 날짜인지? | boolean
- **isEqual(other)**: 동일 날짜인지? | boolean
- **until(other, unit)**: 주어진 단위(unit)차이를 리턴

비교를 위해 특정 날짜와 시간으로 LocalDateTime객체를 얻는 방법 year 부터 second까지 매가값을 모두 int로 제공한다
```java
LocalDateTime target = LocalDateTime.of(year, month, dayOfmonth, hour, minute, second)
```

## 10. 형식 클래스
형식(Format) 클래스는 숫자 또는 날짜를 원하는 형태의 문자열로 변환해주는 기능을 제공한다.
Format 클래스는 java.text패키지에 포함되어 있는다.
#### 주요 Format 클래스
- **DecimalFormat**: 숫자를 형식화된 문자열로 변환
- **SimpleDateFormat**: 날짜를 형식화된 문자열로 변환

### 1. DecimalFormat
DecimalFormat은 숫자를 형식화된 문자열로 변환하는 기능을 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/4cc53021-2ab1-4ec6-ba63-e1602809b639/image.png)

패턴 정보와 함께 DecimalFormat 객체를 생성하고 format() 메소드로 숫자를 제공하면 패턴에 따른 형식화된 문자열을 얻을 수 있다.
```java
DecimalFormat df = new DecimalFormat("#,###.0");
String result = df.format(1234567.89);

```
### 2. SimpleDateFormat
SimpleDateFormat은 날짜를 형식화된 문자열로 변환하는 기능을 제공한다. 원하는 형식으로 표현하기 위해 다음과 같은 패턴을 사용한다.
![](https://velog.velcdn.com/images/co-vol/post/dc2ad1d8-cd40-40d8-8340-f87fa1c93aed/image.png)
패턴에는 자릿수에 맞게 기호를 반복해서 작성할 수 있다.패턴 정보와 함께 SimpleDateFormat 객체를 생성하고 format() 메소드로 날짜를 제공하면 패턴과 동일한 문자열을 얻을 수 있다.
```java
SimpleDateFormat sdf = new SimpleDateFormat("yyyy년 MM월 dd일");
String strDate = sdf.format(new Date());
```

## 11. 정규 표현식 클래스
문자열이 정해져 있는 형식으로 구성되어 있는지 검증해야 하는 경우가 있다. 자바는 정규 표현식을 이용해 문자열이 올바르게 구성되어 있는지 검증한다.

### 1. 작성방법
정규 표현식은 문자 또는 숫자와 관련된 표현과 반복 기호가 결합된 문자열이다.
![](https://velog.velcdn.com/images/co-vol/post/ca09eb06-45d5-40e5-a212-6407db092d63/image.png)

전화번호를 위한 정규식
```java
(010)-\d{3,4}-\d{4}
```
### 2. Pattern 클래스로 검증
java.util.regex 패키지의 Pattern 클래스는 정규 표현식으로 문자열을 검증하는 matches() 메소드를 제공한다.
```java
boolean result = Pattern.matche("정규식","검증할 문자열");
```

## 12. 리플렉션
자바는 클래스와 인터페이스의 메타 정보를 Class 객체로 관리한다. 여기서 메타 정보란 패키지의 정보, 타입 정보, 멤버(생성자, 필드, 메소드) 정보 등을 말한다. 이러한 메타 정보를 프로그램에서 읽고 수정하는 행위를 리플렉션(reflection) 이라고 한다.
```java
Class clazz = 클래스이름.class; //클래스로부터 얻기
Class clazz = Class.forName("패키지---클래스이름"); //클래스로부터 얻기
Class clazz = 객체참조변수.getClass(); // 객체로 부터 얻기
```
세가지 방법을 사용해도 동일한 Class객체를 얻을 수 있다. 예를들어 String 클래스 객체를 얻으려면 다음과 같이 얻을 수 있다.
```java
Class clazz = String.class;

Class clazz = Class.forName("java.lang.String");

String str = "자바";
Class clazz = str.getClass();
```

### 1. 패키지와 타입 정보 얻기
패키지와 타입(클래스, 인터페이스) 이름 정보는 다음 메소드를 통해 얻을 수 있다.
- **Package getPackage()**: 패키지 정보 읽기
- **String getSimpleName()**: 패키지를 제외한 타입 이름
- **String getName()**: 패키지를 포함한 전체 이름
### 2. 멤버 정보 얻기
타입(클래스, 인터페이스)가 가지고 있는 멤버 정보는 다음 메소드를 통해 얻을 수 있다.
#### 메소드
- **Constructor[] getDeclaredConstructors()**: 생성자 정보 읽기
- **Field[] getDeclaredFields()**: 필드 정보 읽기
- **Method[] getDeclaredMethods()**: 메소드 정보 읽기
### 3. 리소스 경로 얻기
Class 객체는 클래스 파일(~.class)의 경로 정보를 가지고 있기 때문에 이 경로를 기준으로 상대 경로에 있는 다른 리소스 파일의 정보를 얻을 수 있다.
#### 메소드
- **URL getResource(Sring name)**: 리소스 파일의 URL리턴
- **InputStream getResourceAsStream(String name)**: 리소스 파일의 InputStream 리턴

GetResource()는 경로 정보가 담긴 URL 객체를 리턴하고, getResourcesAsStream()은 파일의 내용을 읽을 수 있도록 InputStream 객체를 리턴한다

## 13. 어노테이션
코드에서 @으로 작성되는 요소를 어노테이션(Annotation)이라고 한다. 어노테이션은 클래스 또는 인터페이스를 컴파일하거나 실행할 때 어떻게 처리해야 할 것인지를 알려주는 설정 정보이다.
#### 용도
- **컴파일 시 사용하는 정보 전달**
- **빌드 툴이 코드를 자동으로 생성할 때 사용하는 정보 전달**
- **실행 시 특정 기능을 처리할 때 사용하는 정보 전달**

컴파일 시 사용하는 정보 전달의 대표적인 예는 @Override 어노테이션이다. 컴파일러가 메소드를 재정의 검사를 하도록 설정한다.
어노테이션은 자바 프로그램을 개발할 때 필수 요소가 되었고 웹 개발에 많이 사용되는 Spring Framework 또는 Spring Boot는 다양한 종류의 어노테이션을 사용한다.

### 1. 어노테이션 타입 정의와 적용
어노테이션도 하나의 타입이므로 어노테이션을 사용하기 위해서는 먼저 정의부터 해야 한다. 어노테이션을 정의하는 방법은 인터페이스를 정의하는 것과 유사하다.
```java
public @interface AnnotationName
```
이렇게 정의한 어노테이션은 코드에서 다음과 같이 사용된다
```java
@AnnotationName
```
어노테이션은 속성을 가질 수 있다. 속성은 타입과 이름으로 구성되며, 이름 뒤에 괄호를 붙인다. 속성의 기본값은 default 키워드로 지정할 수 있다. 예를 들어 String 타입 prop1과 int 타입의 prop2속성은 다음과 같이 선언할 수 있다.
```java
public @interface AnnotationName {
	String prop1();
    int prop2() default 1;
}
```
이렇게 정의한 어노테이션은 코드에서 다음과 같이 사용할 수 있다. prop1은 기본값이 없기 때문에 반드시 값을 기술해야 하고, prop2는 기본값이 있기 때문에 생략 가능하다.
```java
@AnnotationName(prop = "값");
@AnnotationName(prop = "값", prop2 = 3);
```
어노테이션은 기본 속성인 value를 다음과 같이 가질 수 있다.
```java
public @interface AnnotationName {
	String value();
    int prop2() default 1;
}
```
value 속성을 가진 어노테이션을 코드에서 사용할 때에는 다음과 같이 값만 기술할 수 있다. 이 값은 value 속성에 자동으로 대입된다.
```java
@AnnotationName("값");
```
하지만 value 속성과 다른 속성의 값을 동시에 주고 싶다면 value 속성 이름을 반드시 언급해야 한다.
```java
@AnnotationName(value = "값", prop2 = 3 );
```
### 2. 어노테이션 적용 대상
자바에서 어노테이션은 설정 정보라고 했다. 그렇다면 어떤 대상에 설정 정보를 적용할 것인지, 즉 클래스에 적용할 것인지, 메소드에 적용할 것인지 명시해야 한다. 적용할 수 있는 대상의 종류는
ElementType 열거 상수로 정의되어 있다.

![](https://velog.velcdn.com/images/co-vol/post/4732ef1a-2ba9-455e-beea-675a1738b857/image.png)
적용 대상을 지정할 때에는 @Target 어노테이션을 사용한다. @Target의 기본 속성인 value는 ElemnetType 배열을 값으로 가진다. 이것은 적용 대상을 복수 개로 지정하기 위해서이다. 에를 들어 다음과 같이 적용 대상을 지정했다고 가정해보자.
```java
@Target({ElementType.TYPE, ElementType.FIELD, ElementType.METHOD})
public @interface AnnotationName{}
```
이 어노테이션은 다음과 같이 클래스, 필드, 메소드에 적용할 수 있고 생성자는 적용할 수 없다.
```java
@AnnotationName
public class ClassName {
	@AnnotationName
    private String fieldName;
    
    public ClassName() {}
    
    @AnnotationName
    public void methodName() {}
}
```
### 3. 어노테이션 유지 정책
어노테이션을 정의할 때 한 가지 더 추가해야 할 내용은 @AnnotationName을 언제까지 유지할 것 인지를 지정하는 것이다. 어노테이션 유지 정책을 RetentionPolicy 열거 상수로 다음과 같이 정의 되어 있다.
![](https://velog.velcdn.com/images/co-vol/post/a43ac0cc-1c8c-41b8-8ddf-4a5e5101d47e/image.png)
유지 정책을 지정할 때에는 @Retention 어노테이션을 사용한다. @Retention의 기본 속성인 value는 RetentionPolicy 열거 상수 값을 가진다. 다음은 실행 시에도 어노테이션 설정 정보를 이용할 수 있도록 유지 정책을 RUNTIME으로 지정한 예이다
```java
@Target( { ElementType.TYPE, ElementType.FIELD, ElementType.METHOD})
@Retention( RetentionPolicy.RUNTIME)
public @interface AnnotationName {}
```

### 4. 어노테이션 설정 정보 이용
어노테이션은 아무런 동작을 가지지 않는 설정 정보일 뿐이다. 이 설정 정보를 이용해서 어떻게 처리할 것인지는 애플리케이션의 몫이다. 애플리케이션은 리플렉션을 이용해서 적용 대상으로부터 어노테이션의 정보를 다음 메소드로 얻어낼 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/c9067fe8-0274-4287-a874-72b28408e7b1/image.png)
