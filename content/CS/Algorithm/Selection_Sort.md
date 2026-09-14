# 선택정렬(Selection Sort)

### 개요

- Selection Sort는 Bubble Sort와 유사한 알고리즘이다.
- **해당 순서에 원소를 넣을 위치는 이미 정해져 있고, 어떤 원소를 넣을지 선택하는 알고리즘이다.**
- Selection Sort는 **배열에서 해당 자리를 선택하고 그 자리에 오는 값을 찾는 것**이다.

### 프로세스(오름차순)

1. 주어진 배열 중에 최소값을 찾는다.
2. 그 값을 맨 앞에 위치한 값과 교체한다.(pass)
3. 맨 처음 위치를 뺀 나머지 배열을 같은 방법으로 교체한다.

### Java Code

```java
void selectionSort(int[] arr) {
    int indexMin, temp;
    for (int i = 0; i < arr.length-1; i++) {        // 1.
        indexMin = i;
        for (int j = i + 1; j < arr.length; j++) {  // 2.
            if (arr[j] < arr[indexMin]) {           // 3.
                indexMin = j;
            }
        }
        // 4. swap(arr[indexMin], arr[i])
        temp = arr[indexMin];
        arr[indexMin] = arr[i];
        arr[i] = temp;
  }
  System.out.println(Arrays.toString(arr));
}
```

1. 우선, 위치를 선택해준다.
2. i + 1 번째 원소부터 선택한 위치(index)의 값과 비교를 시작한다.
3. 오름차순이므로 현재 선택한 자리에 있느 값보다 순회하고 있는 값이 작다면, 위치(index)를 갱신해준다.
4. 2번 반복문이 끝난 뒤에는 indexMin에 1번에서 선택한 위치에 들어가야하는 값의 위치를 갖고 있으므로 서로 교환 해준다.

### Selection Sort 과

![selection-sort-001.gif](./img/selection-sort-001.gif)

### 시간복잡도

첫번째 회전에서의 비교횟수 : 1 ~ ( n - 1) ⇒ n -1

두번째 회전에서의 비교횟수 : 2 ~ ( n - 1) ⇒ n -2

…….

(n-1) + (n-2) + .... + 2 + 1 => n(n-1)/2

- 최선,평균,최악 모두 시간복잡도는 O(n^2)를 갖는다.

### 공간복잡도

주어진 배열 안에서 교환 하므로 O(n)이다.

### 장점

- 알고리즘이 단순
- Bubble Sort에 비해 실제로 교환하는 횟수는 적기 때문에 많은 교환이 일어나야 하는 자료상태에서 비교적 효율적이다.
- 정렬하고자 하는 배열 내부에서 교환하는 방식으로, 다른 메모리 공간을 필요로 하지않는다 ⇒ 제자리 정렬

### 단점

- 시간복잡도가 O(n^2)로 비효율적이다.
- 불안정 정렬(Unstable Sort)이다.