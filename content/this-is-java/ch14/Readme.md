## 1. 멀티 스레드 개념
운영체제는 실행 중인 프로그램을 프로세스 로 관리한다 멀티 태스킹은 두 가지 이상의 작업을 동시에 처리하는 것을 말하는데, 이때 운영체제는 멀티 프로세스를 생성해서 처리한다. 하지만 멀티 태스킹이 꼭 멀티 프로세스를 뜻하지는 않는다. 하나의 프로세스 내에서 멀티 태스킹을 할 수 있도록 만들어진 프로그램들도 있다. 예를 들어 메신저는 채팅 작업을 하면서 동시에 파일 전송 작업을 수행하기도 한다.

하나의 프로세스가 두 가지 이상의 작업을 처리할 수 있는 이유는 멀티 스레드가 있기 때문이다. 스레드는 코드의 실행 흐름을 말하는데, 프로세스 내에 스레드가 두 개라면 두 개의 코드 실행 흐름이 생긴다는 의미이다.

멀티 프로세스가 단위의 멀티 태스킹 이라면 멀티 스레드는 프로그램 내부에서 멀티 태스킹이라고 볼 수 있다.
**멀티 프로세스와 멀티 스레드의 차이점**
![](https://velog.velcdn.com/images/co-vol/post/8263f116-f489-4042-a408-5c629170af27/image.png)
멀티 프로세스들은 서로 독립적이므로 하나의 프로세스에서 오류가 발생해도 다른 프로세스에 영향을 미치지 않는다. 하지만 멀티 스레드는 프로세스 내부에서 생성되기 때문에 하나의 스레드가 예외를 발생시키면 프로세스가 종료되므로 다른 스레드에게 영향을 미친다.

예를 들어 워드와 엑셀을 동시에 사용하는 도중에 워드에 오류가 생격 먹통이 되더라도 엑셀은 여전히 사용 가능하다. 그러나 멀티 스레드로 동작하는 메신저의 경우, 파일을 전송하는 스레드에서 예외가 발생하면 메신저 프로세스 자체가 종료되기 때문에 채팅 스레드도 같이 종료된다. 그렇게 때문에 멀티 스레드를 사용할 경우에는 예외 처리에 만전을 가해야 한다.

멀티 스레드는 데이터를 분할해서 병렬로 처리하는 곳에서 사용하기도 하고, 안드로이드 앱에서 네트워크 통신을 하기 위해 사용하기도 한다. 또한 다수의 클라이언트 요청을 처리하는 서버를 개발할 때에도 사용된다.

## 2.메인 스레드
모든 자바 프로그램은 메인 스레드가  main() 메소드를 실행하면서 시작된다. 메인 스레드는 main() 메소드의 첫 코드부터 순차적으로 실행하고, main() 메소드의 마지막 코드를 실행하거나 return  문을 만나면 실행을 종료한다.
![](https://velog.velcdn.com/images/co-vol/post/ec6956d0-31a5-4be8-b3b4-d7cb4c904868/image.png)

메인 스레드는 필요에 따라 추가 작업 스레드들을 만들어서 실행시킬 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/8c8f5e94-25a3-46db-9caa-b29fa3cebc48/image.png)

멀티 스레드에서 메인 스레드가 작업 스레드1을 생성하고 곧이어 작업 스레드가2를 생성하고 실행 시키는것을 볼 수있다.

싱글 스레드에서는 메인 스레드가 종료되면 프로세스도 종료된다. 하지만 멀티 스레드에서는 실행중인 스레드가 하나라도 있다면 프로세스는 종료되지 않는다. 메인 스레드가 작업 스레드보다 먼저 종료되더라도 작업 스레드가 계속 실행 중이라면 프로세스는 종료되지 않는다.

## 3. 작업 스레드 생성과 실행
멀티 스레드로 실행하는 프로그램을 개발하려면 먼저 몇 개의 작업을 병렬로 실행할지 결정하고 각 작업별로 스레드를 생성해야 한다.
![](https://velog.velcdn.com/images/co-vol/post/0a430309-095b-492d-98dc-430ee423f2d9/image.png)
자바 프로그램은 메인 스레드가 반드시 존재하기 떄문에 메인 작업 이외에 추가적인 작업 수만큼 스레드를 생성하면 된다. 자바는 작업 스레드도 객체로 관리하므로 클래스가 필요하다. Thread클래스로 직접 객체를 생성해도 되지만, 하위 클래스를 만들어 생성할 수도 있다.

### 1. Thread 클래스로 직접 생성
java.lang 패키지에 있는 Thread 클래스로부터 작업 스레드를 객체 직접 생성하려면 다음과 같이 Runnable 구현 객체를 매개값으로 갖는 생성자를 호출하면 된다.
```java
Thread thread = new Thread(Runnable target);
```
Runnable은 스레드가 작업을 실행할 때 사용하는 인터페이스이다. Runnable에는 run() 메소드가 정의되어 있는데, 구현 클래스는 run()을 재정의해서 스레드가 실행할 코들르 가지고 있어야 한다.
```java
class Task implements Runnable {
	@Override
    public void run() {
    	//스레드가 실행할 코드
    }
}
```

Runnable 구현 클래스는 작업 내용을 정의한 것으로, 스레드에게 전달해야 한다. Runnable 구현 객체를 생선한 후 Thread 생성자 매개값으로 Runnable 객체를 다음과 같이 전달하면 된다.
```java
Runnable task = new Task();

Thread thread = new Thread(task);
```
명시적인 Runnable 구현 클래스를 작성하지 않고 Thread 생성자를 호출할 때 Runnable 익명 구형 객체를 매개값으로 사용할 수 있다. 오히려 이 방법이 더 많이 사용된다.
```java
Thread thread = new Thread(new Runnable() {
    @Override
    public void run() {
        // 스레드가 실행할 코드 
    }
}
);
```
작업 스레드 객체가 생성되었다고 해서 바로 작업 스레드가 실행되지는 않는다. 작업 스레드를 실행 하려면 스레드 객체의 start() 메소드를 다음과 같이 호출해야 한다.
```java
thread.start();
```

start() 메소드가 호출되면, 작업 스레드는 매개값으로 받은 Runnable의 run() 메소드를 실행하면서 작업을 처리한다.
**작업스레드 생성 실행 순서**
![](https://velog.velcdn.com/images/co-vol/post/3bc1b979-1dae-4da9-a694-22649587ba02/image.png)
메인 스레드는 동시에 두 가지 작업을 처리할 수 없다.

### 2. Thread 자식 클래스로 생성
작업 스레드 객체를 생성하는 또 다른 방법은 Thread의 자식 객체로 만드는 것이다. Thread 클래스를 상속한 다음 run() 메소드를 재정의해서 스레드가 실행할 코드를 작성하고 객체를 생성하면 된다.
```java
public class WorkerThread extends Thread {
	 @Override
     public void run() {
     	//스레드가 실행할 코드
     }
     
}

//스레드 객체 생성
Thread thread = new WorkerThread();

thread.start();
```
작업 스레드를 실행하는 방법은 동일하게 start() 메소드를 호출하면 작업 스레드는 재정의된 run() 메소드를 실행한다.
![](https://velog.velcdn.com/images/co-vol/post/38c4714c-9117-47db-a044-88bdf539e501/image.png)
명시적인 자식 클래스를 정의하지 않고, 다음과 같이 Thread 익명 자식 객체를 사용할 수도 있다. 오히려 이 방법이 더 많이 사용된다.
```java
Thread thread = new Thread() {
	@Override
    public void run() {
     //스레드가 실행할 코드
    }
};

thread.start();
```

## 4. 스레드 이름
스레드는 자신의 이름을 가지고 있다. 메인 스레드는  `main`이라는 이름을 가지고 있고, 작업 스레드는 자동적으로 `Thread-n`이라는 일므을 가진다. 작업 스레드의 이름을 Thread-n 대신 다른 이름으로 설정하고 싶다면 Thread 클래스의 setName() 메소드를 사용하면 된다.
```java
thread.setName("스레드 이름");
```
스레드 이름은 디버깅할 때 어떤 스레드가 작업을 하는지 조사할 목적으로 주로 사용된다. 현재 코드를 어떤 스레드가 실행하고 있는지 확인하려면 정적 메소드인 currentThread()로 스레드 객체의 참조를 얻은 다음 getName() 메소드로 이름을 출력해보면 된다.
```java
Thread thread = Thread.currentThread();
System.out.println(thread.getName());
```

## 5. 스레드 상태
스레드 객체를 생성(NEW)하고, start() 메소드를 호출하면 곧바로 스레드가 실행되는 것이 아니라 실행 대기 상태(RUNNABLE)가 된다. 실행 대기 상태란 실행을 기다리고 있는 상태를 말한다. 실행 대기하는 스레드는 CPU 스케쥴링에 따라 CPU를 점유하고 run() 메소드를 실행한다. 이때를 실행(RUNNING) 상태라고 한다. 실행 스레드는 run() 메소드를 모두 실행하기 전에 스케줄링에 의해 다시 실행 대기 상태로 돌아갈 수 있다. 그리고 다른 스레드가 실행 상태가 된다.

이렇게 스레드는 실행 대기 상태와 실행 상태를 번갈아 가면서 자신의 run() 메소드를 조금씩 실행한다. 실행 상태에서 run() 메소드가 종료되면 더 이상 실행할 코드가 없기 때문에 스레드의 실행은 멈추게된다. 이 상태를 종료 상태(TERMINATED)라고 한다.
![](https://velog.velcdn.com/images/co-vol/post/74854362-ee12-4ca8-85cf-af3fde65ef78/image.png)
실행 상태에서 일시 정지 상태로 가기도 하는데, 일시 정지 상태는 스레드가 실행할 수 없는 상태를 말한다. 스레드가 다시 실행 상태로 가기 위해서는 일시 정지 상태에서 실행 대기 상태로 가야만 한다.
![](https://velog.velcdn.com/images/co-vol/post/40e617dd-4b97-4ce3-afa4-256c7d2d564a/image.png)
![](https://velog.velcdn.com/images/co-vol/post/2d2fb6d7-a8ee-40f4-829f-6018036c519f/image.png)
wait() 과 notify(), notifyAll()은 Object 클래스의 메소드이고 그 외는 Thread 클래스의 메소드이다.

### 1. 주어진 시간 동안 일시 정지
실행 중인 스레드를 일정 시간 멈추게 하고 싶다면 Thread 클래스의 정적 메소드인 sleep() 을 이용하면 된다. 매개값에는 얼마 동안 일시 정지 상태로 있을 것인지 밀리세컨드(1/1000) 단위로 시간을 주면 된다.
```java
try {
	Thread.sleep(1000);
} catch(InterruptedException e) {
	// interrupt() 메소드가 호출되면 실행
}
```
일시 정지 상태에서는 InterruptedException이 발생할 수 있기 때문에 sleep()은 예외 처리가 필수이다.

### 2. 다른 스레드의 종료를 기다림
스레드는 다른 스레드와 독립적으로 실행하지만 다른 스레드가 종료될 때까지 기다렸다가 실행을 해야 하는 경우도 있다. 예를 들어 계산 스레드의 작업이 종료된 후 그 결과값을 받아 처리하는 경우가 있다.
이를 위해 스레드는 join() 메소드를 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/5be2c1e1-eac2-4b04-8d01-afdaf44ebf31/image.png)
ThreadA가 ThreadB의 join() 메소드를 호출하면 ThreadA는 ThreadB가 종료할 때까지 일시 정지 상태가 된다. ThreadB의 run() 메소드가 종료되고 나서야 비로소 ThreadA는 일시 정지에서 풀려 다음 코드를 실행한다.

### 3. 다른 스레드에게 실행 양보
스레드가 처리하는 작업은 반복적인 실행을 위해 for 문이나 while문을 포함하는 경우가 많은데, 가끔 반복문이 무의미한 반복을 하는 경우가 있다.
```java
public void run() {
	while(true) {
    	if(work) {
        	System.out.printlin("ThreadA 작업내용");
        }
    }
}
```
work의 값이 false 일 시에는 무의미한 반복이 일어난다.
이때는 다른 스레드에게 실행을 양보하고 자신은 실행 대기 상태로 가는 것이 프로그램 성능에 도움이 된다. 이런 기능을 위해 Thread는 yield()메소드를 제공한다. yield()를 호출한 스레드는 실행 대기 상태로 돌아가고, 다른 스레드가 실행 상태가 된다.
![](https://velog.velcdn.com/images/co-vol/post/ba341ebd-bf9f-412d-976b-65b3aefc80aa/image.png)
```java
public void run() {
	while(true) {
    	if(work) {
        	System.out.printlin("ThreadA 작업내용");
        } else {
        	Thread.yield();
        }
    }
}
```
무의미한 반복을 하지 않고 다른 스레드에게 실행을 양보해준다.
## 6. 스레드 동기화
멀티 스레드는 하나의 객체를 공유해서 작업할 수도 있다. 이 경우, 다른 스레드에 의해 객체 내부 데이터가 쉽게 변경될 수 있기 때문에 의도했던 것과는 다른 결과가 나올 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/31398dd2-2938-485f-824a-2f15bf593bfe/image.png)
User1Thread는 Calculator 객체의 memory 필드에 100을 먼저 저장하고 2초간 일시 정지 상태가 된다. 그동안 User2Thread가 memory 필드값을 50으로 변경한다. 2초가 지나 User1Thread가 다시 실행 상태가 되어 memory 필드의 값을 출력하면 User2Thread가 저장한 50이 출력된다.

그런데 이렇게 하면 User1Thread에 저장된 데이터가 날아가버린다. 스레드가 사용 중인 객체를 다른 스레드가 변경할 수 없도록 하려면 스레드 작업이 끝날 때까지 객체에 잠금을 걸면 된다. 이를 위해 자바는 동기화 메소드와 블록을 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/e80882ee-307e-47d7-9413-09333fac42d2/image.png)
객체 내부에 동기화 메소드와 동기화 블록이 여러 개가 있다면 스레드가 이들 중 하나를 실행할 때 다른 스레드는 해당 메소드는 물론이고 다른 동기화 메소드 및 블록도 실행할 수 없다. 하지만 일반 메소드는 실행이 가능하다.
### 1. 동기화 메소드 및 블록 선언
동기화 메소드를 선언하는 방법은 synchronized 키워드를 붙이면 된다. synchronized 키워드는 인스턴스와 정적 메소드 어디든 붙일 수 있다.
```java
public synchronized void method() {
	// 단 하나의 스레드만 실행하는 영역
}
```
스레드가 동기화 메소드를 실행하는 즉시 객체는 잠금이 일어나고, 메소드 실행이 끝나면 잠금이 풀린다. 메소드 전체가 아닌 일부 영역을 실행할 때만 객체 잠금을 걸고 싶다면 동기화 블록을 만들면 된다.
```java
public void method() {
	//여러 스레드가 실행할 수 있는 영역
    
    synchronized(공유객체) {
    	// 단 하나의 스레드만 실행하는 영역!
    }
    //여러 스레드가 실행할 수 있는 영역
}
```

### 2. wait()과 notify()를 이용한 스레드 제어
경우에 따라서는 두 개의 스레드를 교대로 번갈아 가며 실행할 때도 있다. 정확한 교대 작업이 필요할 경우, 자신의 작업이 끝나면 상대방 스레드를 일시 정지 상태에서 풀어주고 자신은 일시 정지 상태로 만들면 된다.

이 방법의 핵심은 공유 객체에 있다. 공유 객체는 두 스레드가 작업할 내용을 각각 동기화 메소드로 정해 놓는다. 한 스레드가 작업을 완료하면 notify() 메소드를 호출해서 일시 정지 상태에 있는 다른 스레드를 실행 대기 상태로 만들고, 자신은 두 번 작업을 하지 않도록 wait() 메소드를 호출하여 일시 정지 상태로 만든다.

![](https://velog.velcdn.com/images/co-vol/post/b829fd59-2785-4974-9fd6-00f7e38c6960/image.png)

notify() 는 wait()에 의해 일시 정지된 스레드 중 한 개를 실행 대기 상태로 만들고, notifyAll() 은 wait() 에 의해 일시 정지된 모든 스레드를 실행 대기 상태로 만든다. 주의할 점은 이 두 메소드는 동기화 메소드 또는 동기화 블록 내에서만 사용할 수 있다는 것이다.

## 7. 스레드 안전 종료
스레드는 자신의 run() 메소드가 모두 실행되면 자동적으로 종료되지만, 경우에 따라서는 실행 중인 스레드를 즉시 종료할 필요가 있다. 예를 들어 동영상을 끝까지 보지 않고 사용자가 멈춤을 요구하는 경우이다.
스레드를 강제 종료시키기 위해 Thread는 stop() 메소드를 제공하고 있으나 이 메소드는 deprecated되었다. 스레드를 갑자기 종료하게 되면 사용 중이던 리소스들이 불안전한 상태로 남겨지기 때문이다. 여기에서 리소스란 파일, 네트워크 연결 등을 말한다.

스레드를 안전하게 종료하는 방법은 사용하던 리소스들을 정리하고 run() 메소드를 빨리 종료하는 것이다.
주로 조건 이용 방법과 interrupt() 메소드 이용 방법을 사용한다.

### 1. 조건이용
스레드가 while 문으로 반복 실행할 경우, 조건을 이용해서 run() 메소드의 종료를 유도할 수 있다.
```java
public class XXXThread extends Thread {
	private boolean stop;
    
    private void run() {
    	while( !stop ) {
        	//스레드가 반복 실행하는 코드
        }
        //스레드가 사용한 리소스 정리
    }
}
```
### 2. interrupt() 메소드 이용
interupt() 메소드는 스레드가 일시 정지 상태에 있을 때 InterruptedException 예외를 발생시키는 역할을 한다. 이것을 이용한면 예외 처리를 통해 run() 메소드를 정상 종료시킬 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/5cecfa2e-1e87-4200-93ae-d912a100188f/image.png)
XThread를 생성해서 start() 메소드를 실행한 후에 XThread의 interrupt() 메소드를 실행하면 XThread가 일시 정지 상태가 될 때 InterruptedException이 발생하여 예외 처리 블록으로 이동한다. 이것은 결국 while문을 빠져나와 자원을 정리하고 스레드가 종료되는 효과를 가져온다.

스레드가 실행 대기/실행 상태일 때에는 interrupt() 메소드가 호출되어도 InterruptedException이이 발생하지 않는다. 그러나 스레드가 어떤 이유로 일시 정지 상태가 되면, InterruptedException이 예외가 발생한다. 그래서 짧은 시간이나마 일시 정지를 시켜 주어야 한다.

일시 정지를 만들지 않고도 interrupt() 메소드 호출 여부를 알 수 있는 방법이 있다. Thread의 interrupted()와 isInterrupted() 메소드는 interrupt() 메소드 호출 여부를 리턴한다. interrupted() 메소드는 정적 메소드이고, isInterrupted() 는 인스턴스 메소드이다
```java
boolean status = Thread.interrupted();
boolean status = objThread.isInterrupted();
```
## 8. 데몬 스레드
데몬 스레드는 주 스레드의 작업을 돕는 보조적인 역할을 수행하는 스레드이다. 주 스레드가 종료되면 데몬 스레드도 따라서 자동으로 종료된다.

데몬 스레드를 적용한 예로는 워드프로세서의 자동 저장, 미디어플레이어의 동영상 및 음악 재생,갑비지 컬렉터 등이 있는데, 여기서 주 스레드(워드프로세스, 미디어플레이어, JVM)가 종료되면 데몬 스레드도 같이 종료된다.

스레드를 데몬으로 만들기 위해서는 주 스레드가 데몬이 될 스레드의 setDeamon(true)를 호출하면 된다.
```java
public static void main(String[] args) {
	AutoSaveThread thread = new AutoSaveThread();
    thread.setDeamon(true);
    thread.start;
}
```
메인 스레드가 주 스레드가 되고 AutoSaveThread를 데몬 스레드로 실행 시킨다.
## 9. 스레드풀
병렬 작업 처리가 많아지면 스레드의 개수가 폭증하여 CPU가 바빠지고 메모리 사용량이 늘어난다. 이에 따라 애플리케이션의 성능 또한 급격히 저하된다. 이렇게 병렬 작업 증가로 인한 스레드의 폭증을 막으려면 스레드풀을 사용하는 것이 좋다.

스레드풀은 작업 처리에 사용되는 스레드를 제한된 개수만큼 정해놓고 작업 큐에 들어오는 작업들을 스레드가 하나씩 맡아 처리하는 방식이다. 작업 처리가 끝난 스레드는 다시 작업 큐에서 새로운 작업을 가져와 처리한다. 이렇게 하면 작업량이 증가해도 스레드의 개수가 늘어나지 않아 애플리케이션의 성능이 급격히 저하되지 않는다.
![](https://velog.velcdn.com/images/co-vol/post/0b454fa2-e372-4d10-8ece-d15df214b442/image.png)

### 1. 스레드풀 생성
자바는 스레드풀을 생성하고 사용할 수 있도록 java.util.concurrent 패키지에서 ExecutorService인터페이스와 Executors 클래스를 제공하고 있다. Executors의 다음 두 정적 메소드를 이용하면 간단하게 스레드풀인 ExecutorService 구현 객체를 만들 수 있다.
![](https://velog.velcdn.com/images/co-vol/post/7b92d34f-bbf7-4e05-8ed6-ff1615b94201/image.png)
초기 수는 스레드풀이 생성될 때 기본적으로 생성되는 스레드 수를 말하고, 코어 수는 스레드가 증가된 후 사용되지 않는 스레드를 제거할 때 최소한 풀에서 유지하는 스레드 수를 말한다. 그리고 최대 수는 증가되는 스레드의 한도 수이다.

```java
ExecutorService executorService = Executors.newCachedThreadPool();
ExecutorService executorService2 = Executors.newFixedThreadPool(5);
```
executorService의 초기 스레드 개수는 0개이고 작업 개수가 많아지면 스레드를 생성해서 작업한다. 60초 이상 스레드가 사용되지 않으면 스레드를 풀에서 제거한다.
executorService2의 초기 스레드 개수는 0개이고, 작업 개수가 많아지면 최대 5개 까지 스레드를 생성시켜 작업을 처리한다. 이 스레드풀의 특징은 생선된 스레드를 제거하지 않는다는 것이다.

위 두 메소드를 사용하지 않고 직접 ThreadPoolExecutor로 스레드풀을 생성할 수도 있다.
```java
ExecutorService threadPool = new ThreadPoolExecutor(
	3, // 코어 스레드 개수
    100, // 최대 스레드 개수
    120L, // 놀고 있는 시간
    TimeUnit.SECONDS // 놀고 있는 시간 단위
    new SynchronousQueue<Runnable>() // 작업 큐
)
```
### 2. 스레드풀 종료
스레드풀의 스레드는 기본적으로 데몬 스레드가 아니기 때문에 main스레드가 종료되더라도 작업을 처리하기 위해 계속 실행 상태로 남아 있다. 스레드풀의 모든 스레드를 종료하려면 ExecutorService의 다음 두 메소드 중 하나를 실행해야 한다.
![](https://velog.velcdn.com/images/co-vol/post/dd648944-5e40-4455-8c4d-41153652d224/image.png)
남아있는 작업을 마무리하고 스레드풀을 종료할 때에는 shutdown()을 호출하고, 강제로 종료할 때에는 shutdownNow() 를 호출하면 된다.

### 3. 작업 생성과 처리 요청
하나의 작업은 Runnable 또는 Callable 구현 객체로 표현한다. Runnable과 Callable의 차이점은 작업 처리 완료후 리턴값이 있느냐 없느냐이다.
![](https://velog.velcdn.com/images/co-vol/post/4e6b3ae9-3ca4-4ddb-83dd-c2c0b8d39266/image.png)
Runnable의 run() 메소드는 리턴값이 없고, Callable의 call() 메소드는 리턴값이 있다. call()의 리턴 타입은 Callable<T>에서 지정한 T 타입 파라미터와 동일한 타입이어야 한다.

작업 처리 요청이란 ExecutorService의 작업 큐에 Runnable 또는 Callable 객체를 넣는 행위를 말한다.작업 처리 요청을 위해 ExecutorService는 두 가지 메소드를 제공한다.
![](https://velog.velcdn.com/images/co-vol/post/a4bf2957-7c7b-4562-8f94-253b10eef1df/image.png)
Runnable 또는 Callable 객체가 ExecutorService의 작업 큐에 들어가면 ExecutorService는 처리할 스레드가 있는지 보고, 없다면 스레드를 새로 생성시킨다. 스레드는 작업 큐에서 Runnable또는 Callable 객체를 꺼내와 run() 또는 call() 메소드를 실행하면서 작업을 처리한다.