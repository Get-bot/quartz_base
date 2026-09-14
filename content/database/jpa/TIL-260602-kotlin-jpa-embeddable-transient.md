---
title: "[TIL-260602] Kotlin JPA @Embeddable 파생 필드 함정 — @Transient와 no-arg init"
date: 2026-06-02
tags: ["kotlin", "jpa", "hibernate", "embeddable", "kotlin-noarg", "troubleshooting"]
categories: ["TIL"]
description: "@Embeddable VO의 파생 필드는 @Transient 필수. 게다가 kotlin-noarg는 no-arg 재로드 시 init 블록을 안 돌려서, init eager 계산은 null로 남아 NPE. value 기반 computed property로 해결."
---

## 잘한 점

### 회귀 테스트로 NPE 먼저 재현하고 고침

**상황**
- IP allowlist용 `IpCidr` VO에서 버그가 있었음
- 로컬 bootRun이 `entityManagerFactory` 빈 생성 실패로 안 떴는데, 통합 테스트는 멀쩡히 통과 → 처음엔 마이그레이션-엔티티 불일치인 줄 알았음

**액션**
- 추측으로 고치지 않고 `AllowedIpRepositoryTest`(Testcontainers)에 DB 재로드 후 `contains()` 부르는 회귀 테스트부터 추가해서 NPE를 재현
- 재현 확인하고 나서 `value` 기반 computed property로 수정

**칭찬**
- "테스트 통과하는데 왜 로컬만 죽지?"에서 멈추지 않고 환경별 `ddl-auto` 차이까지 파고든 거
- 버그 재현 → 수정 순서를 지킨 거

---

## 개선점

### "테스트는 통과 but 운영은 죽음" — create-drop이 가린 매핑 버그

**문제**
- `IpCidr`(`@Embeddable`)의 파생 필드 `networkAddress`/`prefixLength`가 영속 매핑에서 안 빠져 있었음
- 통합 테스트가 다 통과해서 한참 못 알아챘다

**원인**
- `application-test.yaml`이 `ddl-auto: create-drop` + `flyway.enabled: false` → Hibernate가 엔티티 기준으로 테이블을 만들어서 `network_address` 컬럼이 자동 생성됨 → 불일치가 안 생김
- 로컬/dev/prod는 `ddl-auto: validate` + Flyway → Flyway 테이블엔 그 컬럼이 없어서 validate 실패
- 테스트 환경만 믿었더니 매핑 버그를 못 잡았다

**액션플랜**
- `@Embeddable`/Entity 새로 만들 때 파생 필드엔 무조건 `@Transient` 명시
- 매핑 의심되면 validate + Flyway 조합으로도 한 번 돌려서 검증

---

## 배운 점

### kotlin-noarg는 init 블록을 안 돌린다

**배움**
- `@Transient`를 붙여도 끝이 아니었음. `init {}`에서 eager 계산하던 게 두 번째 함정이었다
- `kotlin("plugin.jpa")`가 적용하는 `kotlin-noarg`는 `invokeInitializers=false`(기본)라, Hibernate가 no-arg 생성자로 재로드할 때 `init {}`을 안 돌린다
- 그래서 `value`는 reflection으로 채워지는데 `networkAddress`(non-null `ByteArray`)는 미할당 → `contains()`에서 NPE
- 멀티 인스턴스라 다른 인스턴스나 캐시 만료 후 DB 재로드 때 터지는 구조였음. 진짜 위험한 종류

**의미**
- Kotlin VO + JPA에서 파생값은 절대 `init`에서 eager로 만들지 말자
- 파생값은 `value` 하나에서 계산되는 computed property(custom getter)로 두면 재로드든 뭐든 항상 일관된다

---

## 핵심 내용

### 키워드
- `@Embeddable`, `@Transient`, `kotlin-noarg`, `invokeInitializers`, `ddl-auto validate vs create-drop`, computed property

### 요약
- JPA `@Embeddable`/`@Entity`는 `@Transient` 없는 모든 필드를 컬럼으로 간주한다. 파생 필드엔 `@Transient` 필수.
- `kotlin("plugin.jpa")` = `kotlin-noarg`(`invokeInitializers=false`). no-arg 생성자 재로드 시 `init {}` 미실행 → init에서 eager 계산한 파생값은 null로 남는다.
- 해결: init eager 계산 대신 `value` 기반 computed property(custom getter). 재로드해도 getter가 항상 계산하니 안전.
- 환경 분기 함정: test는 `create-drop`이라 엔티티 기준으로 테이블을 만들어 매핑 버그가 가려진다. 로컬/dev/prod는 `validate`+Flyway라 노출된다.

### 코드/명령어
```kotlin
// ✅ value 기반 computed property — no-arg 재로드(init 미실행)에도 항상 계산됨
@Embeddable
class IpCidr(value: String) {
    @Column(name = "value", nullable = false, length = 64)
    var value: String = normalize(value)
        protected set

    private val prefixLength: Int
        get() = value.substringAfter('/').toInt()

    private val networkAddress: ByteArray
        get() = InetAddress.getByName(value.substringBefore('/')).address
}
```
