# 8. 컬렉션 API 개선

# 컬렉션 팩토리

자바 9에서는 작은 컬렉션 객체를 쉽게 만들 수 있는 몇 가지 방법을 제공한다.

### UnsupportedOperationException

내부적으로 고정된 크기의 변환할 수 있는 배열에 새 요소를 추가하거나 요소를 삭제 할 경우 발생한다.

## 리스트 팩토리

List.of 팩토리 메서드를 이용해서 간단하게 리스트를 만들 수 있다.

```java
List<String> friends = List.of("Raphael", "Olivia", "Thibaut");
```

- 변경할 수 없는 리스트가 만들어 졌기 때문에  아이템을 수정,삭제 시 UnsupportedOperationException 예외가 발생한다.
- 이런 제약으로 컬렉션이 의도치 않게 변하는 것을 방지한다.
- null 요소는 금지하므로 의도치 않은 버그를 방지하고 조금 더 간결한 내부 구현을 달성했다.
- 데이터 처리 형식을 설정하거나 데이터를 변환할 필요가 없다면 사용하기 간편한 팩토리 메서드 사용을 추천한다.

## 집합 팩토리

Set.of 팩토리 메서드 이용

```java
Set<String> friends = Set.of("Raphael", "Olivia", "Thibaut");
```

- 중복된 요소를 제공해 집합을 만들려고 하면 어떤 요소가 중복되어 있다는 설명과 IllegalArgumentException이 발생한다.

## 맵 팩토리

Map.of 팩토리 메서드에 키와 값을 번갈아 제공하는 방법으로 맵을 만들 수 있다.

```java
Map<String, Integer> ageOfFriends = Map.of("Raphael", 30, "Olivia", 25, "Thibaut", 26);
```

- 열 개 이하의 키와 값 쌍을 가진 작은 맵을 만들 때는 이 메소드가 유용하다.
- 그 이상의 맵에서는 Map.Entry<K, V> 객체를 인수로 받으며 가변 인수로 구현된 Map.ofEntries 팩토리 메서드를 이용하는 것이 좋다.

```java
Map<String, Integer> ageOfFriends = 
	Map.ofEntry(
		entry("Raphael", 30),
		entry("Olivia", 25),
		entry("Thibaut", 26)
	);
```

# 리스트와 집합 처리

자바8 에서 List와 set에 추가된 메서드

- removeIf: 프레디케이트를 만족하는 요소를 제거
- replaceAll: 리스트에서 이용할 수 있는 기능으로 UnaryOperator 함수를 이용해서 요소를 바꿈
- sort: List 인터페이스에서 제공하는 기능으로 리스트를 정렬

## removeIf 메서드

```java
//숫자로 시작되는 참조 코드를 가진 트랙잭션을 삭제하는 코드
for (Transaction transaction: transactions) {
	if(Character.isDigit(transactin.getReferenceCode().charAt(0))) {
		transactions.remove(transaction);
	}
}

//내부적으로 for-each 루프는 Iterator 객체를 사용하므로 다음과 같이 해석된다
for (Iterator<Transaction> iterator = transactions.iterator(); iterator.hasNext(); ) {
	  Transaction transaction = iterator.next();
	  if(Character.isDigit(transaction.getTrader().getName().charAt(0))){
	    transactions.remove(transaction);
			// 반복하면서 별도의 두 객체를 통해 컬렉션을 바꾸고 있는 문제
	  }
}
```

- 위 코드는 ConcurrentModificationException을 일으 킨다.
- 두 개의 개별 객체가 컬렉션을 관리
    - Iterator 객체, next(), hasNext() 를 이용해 소스를 질의
    - Collection 객체 자체, remove()를 호출해 요소를 삭제
- 결과적으로 반복자의 상태는 컬렉션의 상태와 서로 동기화되지 않는다.

```java
// Iteractor 객체를 명시적으로 사용하고 그 객체의remove() 메서드를 호출해서 문제 해결
for (Iterator<Transaction> iterator = transactions.iterator(); iterator.hasNext(); ) {
  Transaction transaction = iterator.next();
  if (Character.isDigit(transaction.getTrader().getName().charAt(0))) {
    iterator.remove();
  }
}

//자바 8의 removeIf 메서드 사용
transactions.removeIf(transaction -> Character.isDigit(transaction.getTrader().getName().charAt(0)));
```

- removeIf
    - 단순한 코드, 버그 예방, 삭제할 요소를 가리키는 프레디케이트를 인수로 받는다.

## replaceAll 메서드

List 인터페이스의 replaceAll 메서드를 이용해 리스트의 각 요소를 새로운 요소로 바꿀 수 있다.

```java
//새로운 문자열 컬렉션을 생성한다.
referenceCodes.stream()
        .map(code -> Character.toUpperCase(code.charAt(0)) + code.substring(1))
				.collect(toList())
        .forEach(System.out::println);

//ListIterator 객체를 이용해 기존 컬렉션 변경
for (ListIterator<String> iterator = referenceCodes.listIterator(); iterator.hasNext(); ) {
    String code = iterator.next();
    iterator.set(Character.toUpperCase(code.charAt(0)) + code.substring(1));
  }

//자바 8의 replaceAll 메서드
referenceCodes.replaceAll(code -> Character.toUpperCase(code.charAt(0)) + code.substring(1));
```

# 맵 처리

## forEach 메서드

```java
// Map.Entry<K, V>의 반복자를 이용해 맵의 항목 집합 반복
for (Map.Entry<String, Integer> entry : ageOfFriends.entrySet()) {
  String friend = entry.getKey();
  Integer age = entry.getValue();
  System.out.println(friend + " is " + age + " years old");
}

//forEach 반복 (자바 8부터 Map 인터페이스는 BiConsumer를 인수로 받는 forEach지원)
ageOfFriends.forEach((friend, age) -> System.out.println(friend + " is " + age + " years old"));
```

## 정렬 메서드

맵의 항목을 값 또는 키를 기준으로 정렬할 수 있다.

```java
Map<String, String> favouriteMovies = Map.ofEntries(
    entry("Raphael", "Star Wars"),
    entry("Cristina", "Matrix"),
    entry("Olivia", "James Bond")
);

//Entry.comparingByKey 키로 정렬
favouriteMovies.entrySet().stream()
    .sorted(Map.Entry.comparingByKey())
    .forEachOrdered(System.out::println);

//Entry.comparingByValue 값으로 정렬
favouriteMovies.entrySet().stream()
    .sorted(Map.Entry.comparingByValue())
    .forEachOrdered(System.out::println);
```

## getOrDefault 메서드

getOrDefault 메서드를 이용하면 null으로 발생하는 문제를 쉽게 해결 가능하다. 첫 번째 인수로 키를, 두 번째 인수로 기본값을 받으며 맵에 키가 존재하지 않으면 두 번째 인수로 받은 기본값을 반환한다.

```java
Map<String, String> favoriteMovies_GetOrDefault = Map.ofEntries(
    entry("Raphael", "Star Wars"),
    entry("Olivia", "James Bond")
);

System.out.println(favoriteMovies_GetOrDefault.getOrDefault("Olivia", "Matrix"));
System.out.println(favoriteMovies_GetOrDefault.getOrDefault("Thibaut", "Matrix"));
```

### 계산 패턴

- computeIfAbsent: 제공된 키에 해당하는 값이 없으면, 키를 이용해 새 값을 계산하고 맵에 추가한다.
- computeIfPresent: 제공된 키가 존재하면 새 값을 계산하고 맵에 추가한다.
- compute: 제공된 키로 새 값을 계산하고 맵에 저장한다.

### 삭제 패턴

키가 특정한 값과 연관되었을 때만 항목을 제거하는 오버로드 버전 메서드 제공

```java
favouriteMovies.remove(key, value);
```

### 교체 패턴

- replaceAll: BifFunction을 적용한 결과로 각 항목의 값을 교체.
- Replace: 키가 존재하면 맵의 값을 바꾼다.

### 합침

- putAll: 지정된 소스 맵의 모든 매핑을 대상 맵으로 복사, 대상 맵의 기존 키를 소스의 값으로 덮어쓸 가능성이 있다.
- merge: 중복된 키를 어떻게 합칠지 결정하는 BiFunction을 인수로 받아 중복 처리

# 개선된 ConcurrentHashMap

ConcurrentHashMap은 내부 자료구의 특정 부분만 잠궈 동시 추가, 갱신 작업을 허용한다. 동기화된 Hashtable 버전에 비해 연산 성능이 월등하다.

## 리듀스와 검색

- forEach: 각 쌍에 주어진 액션 실행
- reduce: 모든 쌍을 제공된 리듀스 함수를 이용해 결과 합침
- search: 널이 아닌 값을 반환할 때까지 각 쌍에 함수를 적용
- 키에 함수 받기, 값, Map.Entry, (키, 값)인수를 이용한 네 가지 연산 형태를 지원한다.
    - 키,값으로 연산
    - 키로 연산
    - 값으로 연산
    - Map.Entry 객체로 연산
- 이들 연산은 ConcurrentHashMap의 상태를 잠그지 않고 연산을 수행한다.
- 이들 연산에 제공한 함수는 계산이 진행되는 동안 바뀔 수 있는 객체, 값, 순서 등에 의존하면 안된다.

## 계수

ConcurrentHashMap 클래스는 맵의 매핑 개수를 반환하는 mappingCount 메서드를 제공한다.

- 기존의 size 대신 int를 반환하는 mappingCount를 사용하자

## 집합뷰

ConcurrentHashMap 클래스는 ConcurrentHashMap을 집합 뷰로 반환하는 KeySet메서드를 제공한다.

- 맵을 바꾸면 집합도 바뀌고 반대로 집합을 바꾸면 맵도 영향을 받는다.

# 마무리

- 자바 9는 적은 원소를 포함하며 바꿀 수 없는 리스트, 집합, 맵을 쉽게 만들 수 있도록 컬렉션 팩토리를 지원한다.
- 이들 컬렉션 팩토리가 반환한 객체는 만들어진 다음 바꿀 수 없다.
- List 인터페이스는 removeIf, replaceAll, sort 세 가지 디폴트 메서드를 지원한다.
- Set 인터페이스는 removeIf 메서드를 지원한다.
- Map 인터페이스는 자주 사용하는 패턴과 버그를 방지할 수 있도록 다양한 디폴트 메서드를 지원 한다.
- ConcurrentHashMap은 Map에서 상속받은 새 디폴트 메서드를 지원함과 동시에 스레드 안전성도 제공한다.