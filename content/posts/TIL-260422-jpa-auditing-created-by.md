---
title: "[TIL-260422] Spring JPA Auditing @CreatedBy 자동 주입 메커니즘"
date: 2026-04-22
tags: ["Spring Boot", "JPA", "Kotlin", "Auditing", "Spring Security", "Spring Data"]
categories: ["TIL"]
description: "@CreatedBy가 AuditorAware와 SecurityContextHolder를 거쳐 자동 주입되는 파이프라인 전체와 필드명이 아닌 어노테이션이 트리거라는 핵심 이해"
---

## 잘한 점

### Spring JPA Auditing 메커니즘 정확한 이해

**상황**
- `@CreatedBy` 어노테이션이 왜 `UserRoleAssignment.assignedBy` 필드에만 자동 주입되는지 의문이 생김
- 필드명(createdBy vs assignedBy)에 따라 동작 차이가 있을 거라 막연히 의심하고 있었음
- AuditorAware가 정확히 어느 시점에 호출되는지도 불명확

**액션**
- BUWS-22 커밋(`feat: AuthAuditLogger JSON 감사 + AuditorAware (@CreatedBy)`)의 변경 파일을 따라가며 추적
- `CurrentAuditorAware.kt` / `JpaConfig.kt` / `UserRoleAssignment.kt` / `BaseCreatedTimeEntity.kt` 소스 확인
- Spring Data JPA의 `AuditingEntityListener` 동작 원리를 코드 단위로 따라감

**칭찬**
- 아 이래서 그런 거구나. 어노테이션이 붙어있으면 **필드명이 뭐든 상관없고, 타입만 맞으면 자동 주입**이라는 걸 체감으로 이해함
- `assignedBy`라는 이름은 비즈니스 컨텍스트(누가 역할을 부여했는가)를 반영한 의도일 뿐 JPA 메커니즘과는 무관했음
- SecurityContextHolder → CustomUserDetails → userId 추출까지 전체 파이프라인을 한눈에 꿰게 됨

---

## 개선점

### 오늘은 특별히 없음

파고드는 과정이 흐름대로 이어져서 리팩토링할 것은 없었다.

---

## 배운 점

### @CreatedBy 자동 주입의 트리거는 "어노테이션 존재"

**배움**
- `@CreatedBy`는 어노테이션 선언 자체가 주입 조건. 필드명은 아무 상관 없다
- 지금 프로젝트는 `BaseCreatedTimeEntity`에는 `@CreatedBy`가 없고 `UserRoleAssignment.assignedBy`에만 붙어있어서, 자동 주입되는 필드가 그 하나뿐이었던 것
- 다른 엔티티에 필요하면 그 엔티티에 직접 `@CreatedBy` 필드 추가하면 끝

**의미**
- 필드명은 도메인 의미에 맞춰 자유롭게 선택 가능 (`createdBy`, `assignedBy`, `modifiedBy` 등)
- `AuditorAware<T>` 제네릭 타입과 필드 타입만 맞추면 타입 안전성 보장
- BaseEntity에 `@CreatedBy`를 공통으로 둘지, 필요한 엔티티에만 선언할지는 감사 정책 따라 결정하면 된다는 감이 잡힘

---

## 핵심 내용

### 키워드
- `@EnableJpaAuditing`, `AuditingEntityListener`, `@CreatedBy`, `AuditorAware`, `SecurityContextHolder`, `@PrePersist`, `CustomUserDetails`

### 요약
- `@CreatedBy` 필드는 엔티티 저장 시점(`@PrePersist`)에 `AuditorAware.getCurrentAuditor()` 호출 결과로 자동 주입된다. 필드명은 무관, `AuditorAware<T>`의 제네릭과 필드 타입만 일치하면 됨.
- `getCurrentAuditor()`가 `Optional.empty()`를 반환하면 해당 필드는 NULL로 저장 (비인증 요청 등).
- 프로젝트 전역 설정은 `@EnableJpaAuditing(auditorAwareRef = "auditorAware")` 한 줄. 엔티티는 `@EntityListeners(AuditingEntityListener::class)`로 Listener 등록.

### 파이프라인 그림

```
[HTTP Request]
      ↓
[Spring Security Filter]
      ↓  SecurityContextHolder.setContext(Authentication)
[@Service.assignRole(...)]
      ↓  repository.save(UserRoleAssignment(...))
[JPA persist()]
      ↓  @PrePersist 훅 트리거
[AuditingEntityListener]
      ↓  엔티티 스캔: @CreatedBy 필드 탐색
[@CreatedBy assignedBy 발견]
      ↓  AuditorAware<UUID>.getCurrentAuditor() 호출
[CurrentAuditorAware]
      ↓  SecurityContextHolder.getContext().authentication.principal
      ↓  CustomUserDetails.userId (UUID)
[Optional.of(UUID) 반환]
      ↓
[assignedBy 필드에 주입]
      ↓
[INSERT INTO user_role_assignments(..., assigned_by) VALUES (..., ?)]
```

### 코드/명령어

```kotlin
// 1️⃣ JpaConfig — @EnableJpaAuditing + AuditorAware 빈 이름 지정
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorAware")
class JpaConfig { /* ... */ }

// 2️⃣ CurrentAuditorAware — SecurityContext에서 UUID 추출
@Component("auditorAware")
class CurrentAuditorAware : AuditorAware<UUID> {
    override fun getCurrentAuditor(): Optional<UUID> {
        val auth = SecurityContextHolder.getContext().authentication
            ?: return Optional.empty()
        if (!auth.isAuthenticated || auth.principal !is CustomUserDetails) {
            return Optional.empty()
        }
        return Optional.of((auth.principal as CustomUserDetails).userId)
    }
}

// 3️⃣ UserRoleAssignment — @CreatedBy 필드 선언 (필드명은 자유)
@Entity
@Table(name = "user_role_assignments")
class UserRoleAssignment(/* ... */) : BaseCreatedTimeEntity() {
    @CreatedBy
    @Column(name = "assigned_by", updatable = false)
    @JdbcTypeCode(SqlTypes.UUID)
    var assignedBy: UUID? = null
        protected set
}

// 4️⃣ BaseCreatedTimeEntity — EntityListener 등록 (상속 엔티티 전역 적용)
@MappedSuperclass
@EntityListeners(AuditingEntityListener::class)
abstract class BaseCreatedTimeEntity {
    @CreatedDate
    @Column(updatable = false)
    var createdAt: Instant? = null
        protected set
}
```

### 참고 자료
- Spring Data JPA Auditing: https://docs.spring.io/spring-data/jpa/reference/auditing.html
- 프로젝트 커밋: BUWS-22 `feat: AuthAuditLogger JSON 감사 + AuditorAware (@CreatedBy)`
- 프로젝트 코드: `global/config/CurrentAuditorAware.kt`, `auth/authorization/UserRoleAssignment.kt`
