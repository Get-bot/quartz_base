---
title: "[TIL-260420] Kafka Consumer로 선착순 쿠폰 발급 Peak Load Shifting"
date: 2026-04-20
tags: ["Spring Boot", "Kotlin", "Kafka", "Spring Kafka", "DLQ", "UUID v7", "멱등성", "Redis"]
categories: ["TIL"]
description: "선착순 쿠폰 발급을 동기→비동기로 전환해 피크 부하를 시간축으로 분산하고, @RetryableTopic exclude 패턴과 UUID v7 pre-gen으로 멱등성 확보"
---

## 잘한 점

### Redis 재고 차감 + Kafka 이벤트 발행으로 DB 쓰기 피크 평평하게

**상황**
- 선착순 쿠폰 flash sale에서 DB write가 피크 bottleneck. Redis 재고 체크는 빠른데 PostgreSQL `INSERT`가 피크에 무너짐.
- 기존 구조는 `CouponIssueService`가 Redis 재고 차감 → DB 저장까지 동기로 묶어 처리. Redis는 한 줄짜리 원자 연산인데 그 뒤에 JPA flush + 커밋이 붙어 있으니 요청이 몰리면 전부 대기.
- "부하 총량을 줄일 순 없으니 시간축으로 펴자"가 이번 설계 방향이었음.

**액션**
- `CouponIssueService`에서 DB 저장을 떼어내고 `CouponIssueProducer`가 Kafka 이벤트만 발행하도록 전환. API는 Redis 차감 + Producer `send().get(3s)`까지만 하고 즉시 return.
- `CouponIssueConsumer`가 별도 스레드에서 DB에 저장. `@RetryableTopic`으로 1s → 2s → 4s exponential backoff 후 DLT.
- `CouponIssueMessage`에 UUID v7을 **Producer가 pre-gen**해서 payload에 박음. Consumer가 retry해도 같은 `id` → DB unique constraint에서 막힘 → 멱등성.
- Kafka 발행 실패 시 Redis 재고 `compensate()` 호출. 재고를 *먼저* 차감했으니 이벤트 유실 = 재고 유실, 이 대칭을 Producer catch 블록에서 맞춤.
- Message key = `eventId.toString()` — 같은 이벤트는 항상 같은 파티션으로. 파티션 3개, 토픽 auto-create.
- `CouponIssueWriter` 삭제. Service → Writer → Repository 층은 Writer가 하는 일이 Repository 위임뿐이라 YAGNI였다.

**칭찬**
- "Kafka 붙여서 비동기화"에서 멈추지 않고 Peak Load Shifting이라는 이름으로 의도를 박아둔 것. 나중에 설계 문서만 봐도 왜 이 구조인지 바로 읽힘.
- 멱등성을 Consumer 로직이 아니라 **메시지 레벨(pre-gen UUID)** 에서 해결한 게 깔끔. Consumer는 `save` 한 줄이다.
- PDCA Match Rate 97% — design과 실제 구현이 거의 안 어긋남. 설계 단계에서 exception exclude, 보상 트랜잭션, 파티션 키까지 정해놓고 들어간 덕.

---

## 개선점

### Spring Kafka 4.x API가 3.x 블로그 예제와 시그니처가 달라서 삽질

**문제**
- `@RetryableTopic` 옵션명, `JacksonJsonSerializer/Deserializer`의 패키지 경로, `KafkaProperties.buildProducerProperties()` 반환 타입 등이 3.x 예제와 달라서 컴파일 에러가 연달아 터짐.
- 특히 `ErrorHandlingDeserializer` 래핑 시그니처가 바뀌어서 레퍼런스 코드 복붙으론 안 붙음.
- 구글링 상위 결과가 대부분 Spring Boot 3.x / Spring Kafka 3.x 기준이라 실제 동작 확인까지 반나절 소요.

**원인**
- Spring Boot 4.0.5가 Spring Kafka 4.x를 끌어오는데, 4.x용 예제가 아직 커뮤니티에 적음.
- `build.gradle.kts`의 실제 버전을 먼저 보지 않고 블로그 코드부터 붙여넣는 습관.
- Jackson 직렬화도 이번에 `JacksonJsonSerializer`로 이름이 바뀐 걸 런타임에야 확인.

**액션플랜**
- 외부 라이브러리 새 기능 쓰기 전에 먼저 **의존성 해석된 실제 버전**(`./gradlew dependencies`) → **공식 레퍼런스** → 블로그 순으로 확인.
- context7 MCP로 라이브러리 문서를 바로 가져오는 걸 PDCA Design 단계 루틴으로 편입.
- `project_kafka_consumer.md` agent memory에 "Spring Kafka 4.x API versioning lessons"를 남겨둠 → 다음 PDCA에서 자동 참조.

---

## 배운 점

### Peak Load Shifting과 "retry에서 exclude하는 예외"

**배움**
- 동기 → 비동기 큐 전환은 부하 총량을 줄이는 게 아니다. 피크를 시간축으로 **펴주는** 것. Consumer 쪽 throughput은 그대로지만 API 서버가 순간적으로 안 무너짐.
- `@RetryableTopic(exclude = [DataIntegrityViolationException::class])`는 "retry해도 영원히 실패할 예외는 retry에서 빼라"는 규칙. 중복 키 충돌은 *실패*가 아니라 *멱등성 증거*라 catch로 흡수하면 끝.
- Producer 단계 UUID pre-gen이 멱등성을 너무 깔끔하게 만듦. Consumer에 "이미 처리했나?" 체크 로직이 한 줄도 안 들어감. DB unique constraint가 모든 걸 막아줌.
- 보상 트랜잭션은 "선행 작업의 효과를 되돌릴 방법이 있는가?"를 설계 시점에 묻게 만듦. 오늘은 Redis 재고 차감이 선행이라 `compensate()`가 필요했음 — 이걸 놓쳤으면 장애 후 재고가 영영 깎인 채로 남을 뻔.

**의미**
- 고동시성 시스템 설계의 시작은 "어디서 병목이 터지는가"를 측정하고 그 지점을 이동시키는 것. 앞으로도 "캐시 하나 더 붙이자"보다 "병목을 다른 층으로 shift할 수 있나?"를 먼저 물어보자.
- 비동기 설계에서 **멱등성 책임 소재**는 Plan 단계에서 못박고 들어가야 함. "Consumer에서 체크", "메시지에 키 박기", "DB 제약" 중 어디에 둘 건지.
- "선행 작업 + 이벤트 발행" 구조에는 항상 **보상 경로**를 한 쌍으로 설계. 한쪽이 없으면 장애 복구 후에도 상태가 안 맞음.
- Writer/Service 같은 층 분리는 실제 필요가 생기기 전까진 YAGNI. 오늘 Writer 삭제하면서 재확인.

---

## 핵심 내용

### 키워드
- `Peak Load Shifting`, `@RetryableTopic`, `DLT (Dead Letter Topic)`, `UUID v7 pre-gen`, `보상 트랜잭션`, `Exclude Exception`, `Spring Kafka 4.x`, `Partition Key`

### 요약
- **Peak Load Shifting**: 동기 처리를 비동기 큐로 옮겨 피크 부하를 시간축으로 평평하게 분산. 총 처리량은 같지만 API 서버가 순간적으로 안 무너짐.
- **UUID v7 pre-gen 멱등성**: Producer가 메시지 ID를 미리 생성해서 payload에 포함 → Consumer retry해도 같은 ID → DB unique constraint가 중복 차단. Consumer 로직 복잡도 0.
- **Retry Exclude 패턴**: retry해도 절대 성공 못 할 예외(`DataIntegrityViolationException` 같은 중복 키 충돌)는 `exclude`로 빼서 DLT 오염 방지. 대신 consume 내부에서 catch해서 `log.info`로 흡수.
- **보상 트랜잭션**: "선행 작업(Redis 차감) + 이벤트 발행(Kafka)"에서 이벤트 발행 실패 시 선행 작업을 되돌려야 상태 정합성이 맞음. Producer catch 블록에서 `compensate()`.
- **Partition Key**: `eventId`를 키로 주면 같은 이벤트의 발급이 항상 같은 파티션 → 파티션 내 순서 보장.

### 코드/명령어

```kotlin
// Producer — Redis 보상 포함
fun publish(message: CouponIssueMessage) {
    try {
        kafkaTemplate.send(COUPON_ISSUE_TOPIC, message.eventId.toString(), message)
            .get(3000, TimeUnit.MILLISECONDS)
    } catch (e: Exception) {
        log.error(e) { "Kafka 발행 실패, Redis 보상" }
        redisStockRepository.compensate(message.eventId, message.userId)
        throw BusinessException(ErrorCode.COUPON_PUBLISH_FAILED)
    }
}
```

```kotlin
// Consumer — retry exclude + 중복 흡수
@RetryableTopic(
    attempts = "4",
    backOff = BackOff(delay = 1000, multiplier = 2.0),
    dltTopicSuffix = ".DLT",
    exclude = [DataIntegrityViolationException::class],
    autoCreateTopics = "true",
)
@KafkaListener(topics = [COUPON_ISSUE_TOPIC], groupId = COUPON_ISSUE_GROUP)
@Transactional
fun consume(message: CouponIssueMessage) {
    try {
        couponIssueRepository.save(CouponIssue(message.id, message.eventId, message.userId))
    } catch (e: DataIntegrityViolationException) {
        log.info { "중복 메시지 무시 — id=${message.id}" }
    }
}
```

```kotlin
// Message — Producer가 id pre-gen
data class CouponIssueMessage(
    val id: UUID,       // UuidCreator.getTimeOrderedEpoch() pre-gen
    val eventId: UUID,  // partition key
    val userId: UUID,
    val issuedAt: Instant,
)
```

### 참고 자료
- Spring Kafka Reference — `@RetryableTopic`, `DltHandler`
- RFC 9562 — UUID v7 (time-ordered)
- `docs/02-design/features/04-kafka-consumer.design.md`, `docs/04-report/features/04-kafka-consumer.report.md`
