## 1. 컬렉션 프레임워크
자바는 널리 알려저 있는 자료구조를 바탕으로 객체들을 효율적으로 추가, 삭제, 검색할수 있도록 관련된 인터페이스와 클래스들을 java.util 패키지에 포함시켜 놓았다. 이들을 총칭해서 컬렉션 프레임워크 라고 부른다.

컬렉션 프레임워크는 몇 가지 인터페이스를 통해서 다양한 컬렉션 클래스를 이용할 수 있도록 설계 되어 있다.주요 인터페이스로는 List, Set, Map이 있는데, 이 인터페이스로 사용 가능한 컬렉션 객체의 종류는 다음과 같다.

![](https://velog.velcdn.com/images/co-vol/post/625858dc-644b-4d24-b5cb-fc9c37a22ee0/image.png)

List와 Set은 객체를 추가, 삭제, 검색하는 방법에 있어서 공통점이 있기 때문에 공통된 메소드만 따로 모아 Collection 인터페이스로 정의해 두고 이것을 상속한다. Map은 키와 값을 하나의 쌍으로 묶어서 관리하는 구조로 되어 있어 List 및 Set과는 사용 방법이 다르다.
![](https://velog.velcdn.com/images/co-vol/post/b430cc61-0819-46e8-b0b9-390596245a6c/image.png)

## 2. List 컬렉션
List 컬렉션은 객체를 인덱스로 관리하기 때문에 객체를 저장하면 인덱스가 부여되고 인덱스로 객체를 검색, 삭제할 수 있는 기능을 제공한다.

List 컬렉션에는 ArrayList, Vector, LinkedList 등이 있는데, List 컬렉션에서 공통적으로 사용가능한 List 인터페이스 메소드는 다음과 같다. 인덱스로 객체들이 관리되기 떄문에 인덱스를 매개값으로 갖는 메소드들이 많다.

![](https://velog.velcdn.com/images/co-vol/post/02b86ef2-aaff-49ac-ba6b-ba30c92a6e05/image.png)

### 1. ArrayList
ArrayList는 List 컬렉션에서 가장 많이 사용되는 컬렉션이다. ArrayList에 객체를 추가하면 내부 배열에 객체가 저장된다. 일반 배열과의 차이점은 ArrayList는 제한 없이 객체를 추가할 수 있다는 것이다.
![](https://velog.velcdn.com/images/co-vol/post/9c8aded9-a824-423b-bbfa-df70a36bc48f/image.png)
List 컬렉션은 객체 자체를 저장하는 것이 아니라 객체의 번지를 저장한다. 또한 동일한 객체를 중복 저장할 수 있는데, 이 경우에는 동일한 번지가 저장된다. null 또한 저장이 가능하다.
```java
List<E> list = new ArrayList<E>(); // E에 지정된 타입의 객체만 저장
List<E> list = new ArrayList<>(); // E에 지정된 타입의 객체만 저장
List list = new ArrayList(); // 모든 타입의 객체를 저장
```
타입 파라미터 E에는 ArrayList에 저장하고 싶은 객체 타입을 지정하면 된다. List에 지정한 객체 타입과 동일하다면 ArrayList<>와 같이 객체 타입을 생략할 수도 있다. 객체 타입을 모두 생략하면 모든 종류의 객체를 저장할 수 있다.

ArrayList 컬렉션에 객체를 추가하면 인덱스 0번부터 차례대로 저장된다. 특정 인덱스의 객체를 제거하면 바로 뒤 인덱스부터 마지막 인덱스까지 모두 앞으로 1씩 당겨진다. 마찬가지로 특정 인덱스에 객체를 삽입하면 해당 인덱스부터 마지막 인덱스까지 모두 1씩 밀려난다.
![](https://velog.velcdn.com/images/co-vol/post/9966ae62-2f35-41e4-9ea0-c1b778dee056/image.png)
따라서 빈번한 객체 삭제와 삽입이 일어나는 곳에서는 ArrayList를 사용하는 것은 바람직하지 않다.
대신 이런 경우라면 LinkedList를 사용하는 것이 좋다.

### 2. Vector
Vector는 ArrayList와 동일한 내부 구조를 가지고 있다. 차이점은 Vector는 동기화된 메소드로 구성되어 있기 때문에 멀티 스레드가 동시에 Vector() 메소드를 실행할 수 없다는 것이다.
![](https://velog.velcdn.com/images/co-vol/post/51037824-8d9f-40b6-aa6f-04795a64d176/image.png)
```java
List<E> list = new Vector<E>(); // E에 지정된 타입의 객체만 저장
List<E> list = new Vector<>(); // E에 지정된 타입의 객체만 저장
List list = new Vector(); // 모든 타입의 객체 저장
```
타입 파라미터 E에는 Vector에 저장하고 싶은 객체 타입을 지정하면 된다. List에 지정한 객체 타입과 동일하다면 Vector<>와 같이 객체 타입을 생략할 수도 있다. 객체 타입을 모두 생략하면 모든 종류의 객체를 저장할 수 있다.

### 3. LinkedList
LinkedList는 ArrayList와 사용 방법은 동일하지만 내부 구조는 완전히 다르다. ArrayList는 내부 배열에 객체를 저장하지만, LinkedList는 인접 객체를 체인처럼 연결해서 관리한다.
![](https://velog.velcdn.com/images/co-vol/post/79b833ff-f6f9-481d-9da9-d69f2d0991f8/image.png)
LinkedList는 특정 위치에서 객체를 삽입하거나 삭제하면 바로 앞뒤 링크만 변경하면 되므로 빈번한 객체 삭제와 삽입이 일어나는 곳에서는 ArrayList보다 좋은 성능을 발휘한다.
![](https://velog.velcdn.com/images/co-vol/post/66bb3229-84d2-4b6a-b4e6-a895de14e568/image.png)
```java
List<E> list = new LinkedList<E>(); // E에 지정된 타입의 객체만 저장
List<E> list = new LinkedList<>(); // E에 지정된 타입의 객체만 저장
List list = new LinkedList(); // 모든 타입의 객체 저장
```

## 3.  Set 컬렉션
List 컬렉션은 저장 순서를 유지하지만, Set 컬렉션은 저장 순서가 유지되지 않는다. 또한 객체를 중복해서 저장할 수 없고, 하나의 null만 저장할 수 있다. Set 컬렉션은 수학의 집합에 비유될 수 있다.
집합은 순서와 상관없고 중복이 허용되지 않기 때문이다.

Set 컬렉션은 또한 구슬 주머니와도 같다. 동일한 구슬을 두 개 넣을 수 없으며, 들어갈(저장할) 때 와 나올(찾을) 때의 순서가 다를 수도 있기 떄문이다.
![](https://velog.velcdn.com/images/co-vol/post/9fe3b476-4d85-416b-88aa-d3eaccf07a5c/image.png)
Set 컬렉션에는 HashSet, LinkedHashSet, TreeSet 등이 있는데, Set 컬렉션에 공통적으로 사용 가는 Set 인터페이스의 메소드는 다음과 같다. 인덱스로 관리하지 않기 때문에 인덱스를 매개값으로 갖는 메소드가 없다.
![](https://velog.velcdn.com/images/co-vol/post/593d5199-7274-4ffe-be41-4c7847862a3a/image.png)
### 1. HashSet
Set 컬렉션 중에서 가장 많이 사용되는 것이 HashSet이다.
```java
Set<E> set = new HashSetM<E>(); // E에 지정된 타입의 객체만 저장 가능
Set<E> set = new HashSetM<>(); // E에 지정된 타입의 객체만 저장 가능
Set set = new HashSetM(); // 모든 타입의 객체 저장 가능
```
HashSet은 동일한 객체는 중복 저장하지 않는다. 여기서 동일한 객체란 동등 객체를 말한다. HashSet은 다른 객체라도 hashCode() 메소드의 리턴값이 같고, equals() 메소드가 true를 리턴하면 동일한 객체라고 판단하고 중복 저장하지 않는다.

![](https://velog.velcdn.com/images/co-vol/post/7e40f79a-89a3-4fd4-a7a0-527c290d442a/image.png)
문자열을 HashSet에 저장할 경우, 같은 문자열을 같는 String 객체는 동등한 객체로 간주한다. 같은 문자열이면 hashCoed()의 리턴값이 같고 equals() 의 리턴값이 true가 나오기 때문이다.

Set 컬렉션은 인덱스로 객체를 검색해서 가져오는 메소드가 없다. 대신 객체를 한 개씩 반복해서 가져와야 하는데, 여기에는 두 가지 방법이 있다.
```java
Set<E> set = new Set<>();
for(E e : set) {
	...
}

Iterator<E> iterator = set.iterator();
```
iterator는 Set 컬렉션의 객체를 가져오거나 제거하기 위해 메소드를 제공한다.

![](https://velog.velcdn.com/images/co-vol/post/23a16b5b-8a39-437c-be08-384728930e4b/image.png)
```java
while(iterator.hasNext()) {
	E e = iterator.next();
}
```
hasNext() 메소드로 가져올 객체가 있는지 먼저 확인하고, true를 리턴할 때만 next() 메소드로 객체를 가져온다. 만약 next()로 가져온 객체를 컬렉션에서 제거하고 싶다면 remove() 메소드를 사용한다.

## 4. Map 컬렉션
Map 컬렉션은 키(Key)와 값(Value)로 구성된 엔트리(Entry)객체를 저장한다. 여기서 키와 값은 모두 객체이다. 키는 중복 저장할 수 없지만 값은 중복 저장할 수 있다. 기존에 저장된 키와 동일한 키로 값을 저장하면 기존의 값은 없어지고 새로운 값으로 대체된다.
![](https://velog.velcdn.com/images/co-vol/post/59c5e15f-6b5c-483c-b57c-6fc9b349e337/image.png)
Map 컬렉션에는 HashMap, Hashtable, LinkedHashMap, Properties, TreeMap 등이 있다.
Map 컬렉션에서 공통적으로 사용 가능한 Map 인터페이스 메소드는 다음과 같다. 키로 객체들을 관리하기 때문에 키를 매개값으로 갖는 메소드가 많다.
![](https://velog.velcdn.com/images/co-vol/post/830d8424-bb1a-4009-9afa-7269fa8275f1/image.png)
K는 키 타입 V는 값 타입을 말한다.

### 1. HashMap
HashMap은 키로 사용할 객체가 hashCoed()의 메소드의 리턴값이 같고 equals() 메소드가 true를 리턴할 경우,동일 키로 보고 중복 저장을 허용하지 않는다.
![](https://velog.velcdn.com/images/co-vol/post/bb8d2bc8-8282-45b5-8b53-5f0984e25042/image.png)

다음은 HashMap 컬렉션을 생성하는 방법이다. K와 V는 각각 키와 값의 타입을 지정할 수 있는 타입 파라미터이다.
```java
Map<K, B>map = new HashMap<K, V>();
```
키는 String 타입, 값은 Integer 타입으로 갖는 HashMap은 다음과 같이 생성할 수 있다. Map에 지정된 키와 값의 타입이 HashMap과 동일할 경우, HashMap<>을 사용할 수 있다.
```java
Map<String, Integer> map = new HashMap<String, Interger>();
Map<String, Integer> map = new HashMap<>();
```
모든 타입의 키와 객체를 저장할 수 있도록 HashMap을 다음과 같이 생성할 수 있지만, 이런 경우는 거의 없다.
```java
Map map = new HashMap();
```

### 2. HashTable
HashTable은 HashMap과 동일한 내부 구조를 가지고 있다. 차이점은 HashTable은 동기화된(synchronized) 메소드로 구성되어 있기 때문에 멀티 스레드가 동시에 Hashtable의 메소드들을 실행할 수 없다는 것이다. 따라서 멀티 스레드 환경에서도 안전하게 객체를 추가, 삭제할 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/d49d81e8-91c8-4f05-926a-488ee8cb0a34/image.png)

다음은 키 타입으로 String을, 값 타입으로 Integer를 같는 Hashtable을 생성한다.
```java
Map<String, Integer> map = new Hashtable<String, Integer>();
Map<String, Integer> map = new Hashtable<>();
Map map = new Hashtable();
```

### 3. Properties
Properties는 Hashtable의 자식 클래스이기 때문에 Hashtable의 특징을 그대로 가지고 있다. Properties는 키과 값을 String 타입으로 제한한 컬렉션이다. Properties는 주로 확장자가 .properties인 프로퍼티 파일을 읽을 때 사용한다.

프로퍼티 파일은 다음과 같이 키와 값이 = 기호로 연결되어 있는 텍스트 파일이다. 일반 텍스트 파일과는 다르게 `ISO 8859-1` 문자셋으로 저장되며, 한글일 경우에는 `\u+유니코드`로 표현되어 저장된다.

database.properties
```properties
driver = oracle.jdbc.OracleDirver
url = jdbc:oracle:thin:@localhost:1521:orcl
usernmae = someUser
password = someass
admin = \uc774\uac74\u0020\uc774\uc2a4\ud130\uc5d0\uadf8\uc57c\u007e\u0020\ub09c\u0020\uc0ac\uc2e4\u0020\uc0ac\ub791\ud558\ub294\u0020\uc0ac\ub78c\uc774\u0020\uc788\uc5b4\u002e
```
Properties을 사용하면 위와 같은 프로퍼티 파일의 태용을 코드에서 쉽게 읽을 수 있다. 먼저 Properties 객체를 생성하고, load() 메소드로 프로퍼티 파일의 내용을 메모리로 로드한다.
```java
Properties properties = new Properties();
properties.load(Xxx.class.getResourceAsStream("database.properties"));
```
일반적으로 프로퍼티 파일은 클래스 파일(~.class)들과 함께 저장된다. 따라서 클래스 파일을 기준으로 상대 경로를 이용해서 읽는 것이 편리하다. Class 객체의 getResourceAsStream() 메소드는 주어진 상대 경로의 리소스 파일을 읽는 InputStream을 리턴한다.

## 5. 검색 기능을 강화시킨 컬렉션
컬렉션 프레임워크는 검색 기능을 강화시킨 TreeSet과 TreeMap을 제공한다. 이름에서 알 수 있듯이 TreeSet은 Set 컬렉션이고, TreeMap은 Map컬렉션이다.

### 1. TreeSet
TreeSet은 이진 트리를 기반으로 한 Set컬렉션이다. 이진 트리는 여러 개의 노드가 트리형태로 연결된 구조로, 루트 노드 라고 불리는 하나의 노드에서 시작해 각 노드에 최대 2개의 노드를 연결할 수 있는 구조를 가지고 있다.
![](https://velog.velcdn.com/images/co-vol/post/e8954ba1-da99-4208-9e14-88e35d76f541/image.png)
TreeSet에 객체를 저장하면 다음과 같이 자동으로 정렬된다. 부모 노드의 객체와 비교해서 낮은 것은 왼쪽 자식 노드에, 높은 것은 오른쪽 자식 노드에 저장한다.
![](https://velog.velcdn.com/images/co-vol/post/cd7a09e5-c929-491d-8ac7-b85de72ac605/image.png)
```java
TreeSet<E> treeSet = new TreeSet<E>();
TreeSet<E> treeSet = new TreeSet<>();
```
Set 타입 변수에 대입해도 되지만 TreeSet 타입으로 대입한 이유는 검색 관련 메소드가 TreeSet에 만 정의되어 있기 때문이다.
<img src="https://velog.velcdn.com/images/co-vol/post/1a4c7834-32e8-4331-8b3e-7214d5b9bb9e/image.png" style="margin-bottom:0px"/>
<img src="https://velog.velcdn.com/images/co-vol/post/fecc27d1-a253-42bc-af7f-39dbf9667015/image.png" style="margin-top:0px; position:relative; top:-31px;"/>

### 2. TreeMap
TreeMap은 이진 트리를 기반으로 한 Map 컬렉션이다. TreeSet과의 차이점은 키와 값이 저장된 Entry를 저장한다는 점이다.TreeMap에 엔트리를 저장하면 키를 기준으로 자동 정렬되는데, 부모 키 값과 비교해서 낮은 것은 왼쪽, 높은 것은 오른쪽 자식 노드에 Entry 객체를 저장한다.

![](https://velog.velcdn.com/images/co-vol/post/d538aa1f-d363-4ec0-bdaf-22af402269b4/image.png)
```java
TreeMap<K, V> treeMap = new TreeMap<K, V>();
TreeMap<K, V> treeMap = new TreeMap<>();
```
Map 타입 변수에 대입해도 되지만 TreeMap 타입으로 대입한 이유는 검색 관련 메소드가 TreeMap에만 정의되어 있기 때문이다.
![](https://velog.velcdn.com/images/co-vol/post/8e5d8485-c276-4d94-a6c7-8690600f3fc1/image.png)

### 3. Comparable 과 Comparator
TreeSet에 저장되는 객체와 TreeMap에 저장되는 키 객체는 저장과 동시에 오름차순으로 정렬되는데, 어떤 객체든 정렬될 수 있는 것은 아니고 객체가 Comparable 인터페이스를 구현하고 있어야 가능하다. Integer, Double, String 타입은 모두 Comparable을 구현하고 있기 때문에 상관 없지만, 사용자 정의 객체를 저장할 때에는 반드시 Comparable을 구형하고 있어야 한다.

Comparable 인터페이스에는 compareTo() 메소드가 정의되어 있다. 따라서 사용자 정의 클래스에서 이 메소드를 재정의해서 비교 결과를 정수 값으로 리턴해야 한다.
![](https://velog.velcdn.com/images/co-vol/post/4efc98e4-8501-44b2-bb92-95fb5674197e/image.png)
비교 기능이 있는 Comparable 구현 객체를 TreeSet에 저장하거나 TreeMap의 키로 저장하는 것이 원칙이지만, 비교 기능이 없는 Comparable 비구현 객체를 저장하고 싶다면 TreeSet과 TreeMap을 생성할 때 비교자를 제공하면 된다.
```java
TreeSet<E> treeSet = new TreeSet<>( new ComparatorImpl() );
TreeMap<K, V> treeMap = new TreeMap<>( new ComparatorImpl() );

```
비교자는 Comparator 인터페이스를 구현한 객체를 말하는데, Comparator 인터페이스는 compare() 메소드가 정의되어 있다. 비교자는 이 메소드를 재정의해서 비교 결과를 정수 값으로 리턴해준다.![](https://velog.velcdn.com/images/co-vol/post/bc607bc7-25f3-4dc0-8e87-539cf48f25d1/image.png)

## 6. LIFO와 FIFO 컬렉션
후입선출(LIFO)은 나중에 넣은 객체가 먼저 빠져나가고, 선입선출(FIFO)은 먼저 넣은 객체가 먼저 빠져나가는 구조를 말한다. 컬렉션 프레임워크는 LIFO 자료구조를 제공하는 스택 클래스와 FIFO 자료구조를 제공하는 큐 인터페이스를 제공하고 있다.
![](https://velog.velcdn.com/images/co-vol/post/753b3231-be9b-4bfe-95ff-eb649919e76e/image.png)
스택을 응용한 대표적인 예가 JVM 스택 메모리이다. 스택 메모리에 저장된 변수는 나중에 저장된 것부터 제거된다. 큐를 응용한 대표적인 예는 스레드풀의 작업 큐이다. 작업 큐는 먼저 들어온 작업부터 처리한다.

### 1. Stack
Stack 클래스는 LIFO 자료구조를 구현한 클래스이다.
```java
Stack<E> stack = new Stack<E>();
Stack<E> stack = new Stack<>();
```
![](https://velog.velcdn.com/images/co-vol/post/f5cd504c-4963-4be5-b8a3-8515c67e911d/image.png)

### 2. Queue
Queue 인터페이스는 FIFO 자료구조에서 사용되는 메소드를 정의하고 있다.
![](https://velog.velcdn.com/images/co-vol/post/6cafd26a-f87e-4be3-93a4-5b3d988e7c7d/image.png)
Queue 인터페이스를 구현한 대표적인 클래스는 LinkedList이다. 그렇기 때문에 LinkedList 객체를 Queue 인터페이스 변수에 대입할 수 있다.
```java
Queue<E> queue = new LinkedList<E>();
Queue<E> queue = new LinkedList<>();
```

## 7. 동기화된 컬렉션
컬렉션 프레임워크의 대부분의 클래스들은 싱글 스레드 환경에서 사용할 수 있도록 설계되었다. 그렇기 때문에 여러 스레드가 동시에 컬렉션에 접근한다면 의도하지 않게 요소가 변경될 수 있는 불안전한 상태가 된다.

Vector와 Hashtable은 동기화된 메소드로 구성되어 있기 때문에 멀티 스레드 환경에서 안전하게 요소를 처리할 수 있지만, ArrayList와 HashSet, HashMap은 동기화된 메소드로 구성되어 있지 않아 멀티 스레드 환경에서 안전하지 않다.

경우에 따라서는 ArrayList, HashSet, HashMap을 멀티 스레드 환경에서 사용하고 싶을 때가 있을 것이다. 이런 경우를 대비해서 컬렉션 프레인워크는 비동기화된 메소드를 동기화된 메소드로 래핑하는 Collections의 synchronizedXXX() 메소드를 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/06370418-67b0-41f9-a9e3-995c2d3fed04/image.png)
이 메소드들은 매개값으로 비동기화된 컬렉션을 대입하면 동기화된 컬렉션을 리턴한다.
![](https://velog.velcdn.com/images/co-vol/post/388c094f-f757-4b49-9b9a-046d04444842/image.png)
ArrayList를 Collections.synchronizedList() 메소드를 통해 동기화된 List로 변환한다.
## 8. 수정할 수 없는 컬렉션
수정할 수 없는 컬렉션이란 요소를 추가, 삭제할 수 없는 컬렉션을 말한다. 컬렉션 생성 시 저장된 요소를 변경하고 싶지 않을 때 유용하다. 여러 가지 방법으로 만들 수 있는데, 먼저 첫번째 방법으로는 List, Set, Map 인터페이스의 정적 메소드인 of()로 생성할 수 있다.
```java
List<E> immutableList = List.of(E... elements);
Set<E> immutableSet = Set.of(E... elements);
Map<K, V> imuutableMap = Map.of(K k1, V v1, K k2, V v2, ...);
```
두 번째 방법은 List, Set, Map 인터페이스의 정적 메소드인 copyOf()를 이용해 기존 컬렉션을 복사하여 수정할 수 없는 컬렉션을 만드는 것이다.
```java
List<E> immutableList = List.copyOf(Collection<E> coll);
Set<E> immutableSet = Set.copyOf(Collection<E> coll);
Map<K, V> imuutableMap = Map.copyOf(Map<K, V> map);
```
세 번째 방법은 배열로부터 수정할 수 없는 List 컬렉션을 만들 수 있다.
```java
String[] arr = {"A", "B", "C"};
List<String> immutableList = Arrays.asList(arr);
```
