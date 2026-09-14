---
title: "[TIL-260429] AES-GCM 컬럼 암호화 + @RequireRole AOP RBAC + 마지막 ADMIN 회수 차단"
date: 2026-04-29
tags: ["AES-GCM", "AOP", "RBAC", "Spring Security", "Springdoc", "Kotlin"]
categories: ["TIL"]
description: "RegisteredApp.secret을 AES-GCM application-level 암호화, @RequireRole AOP로 권한 체크 횡단 분리, 회원 역할 ADMIN API에 멱등·자가 회수 차단·마지막 ADMIN 보호 3종 가드"
---

## 잘한 점

### RegisteredApp.secret 을 AES-GCM application-level 암호화

**상황**
- `RegisteredApp` 의 `secret` 컬럼은 PG·외부 시스템 호출에 쓰이는 민감값
- DB 덤프가 유출되거나 백업이 잘못 노출되면 그대로 평문이 새는 클래스
- DB 자체 TDE만 믿기엔 운영 환경에서 dump가 평문으로 빠져나갈 경로가 있음

**액션**
- `global/service/AesGcmEncryptionService` 추가 — AES-GCM (12-byte IV, 16-byte tag) 표준
- 키는 환경변수 `AES_KEY` (32 byte base64) 로 주입
- prod 프로파일에서 `AES_KEY` 미설정 시 **부팅 실패** — fallback 절대 안 둠
- Repository slice 테스트용으로 `NoOpEncryptionService` 별도 빈

**칭찬**
- 처음엔 dev/test 편의로 fallback 키를 둘 뻔했는데 "prod에서 사고 나는 가장 빠른 길" 이라 강제로 fail-fast 박은 결정

---

### `@RequireRole` AOP — 권한 체크 횡단 관심사 분리 + Springdoc 자동 문서화

**상황**
- ADMIN 전용 엔드포인트가 도메인마다 늘어나는 중
- 매 컨트롤러에 권한 체크를 박으면 누락이 생기고, Spring Security `@PreAuthorize` 식 SpEL은 IDE 정적 분석이 안 되어 리팩토링 폭탄

**액션**
- `@RequireRole(Role.ADMIN)` 어노테이션 + `RequireRoleAspect` 로 SecurityContext 검증
- `RequireRoleOperationCustomizer` 가 Springdoc OpenAPI 응답에 401/403을 자동 추가 — Swagger 문서가 권한 체크와 자동 동기화

**칭찬**
- AOP는 잘못 쓰면 디버깅 헬게이트인데, 권한 체크라는 **정말 횡단인 케이스** 에만 적용한 절제

---

### 회원 역할(Role) 관리 ADMIN API — 3종 가드

**상황**
- `MemberRoleAdminController` 로 부여/회수/조회 API 만들면서 도메인 규칙 검토
- 시스템에 ADMIN이 0명이 되거나, 자기 자신의 ADMIN을 실수로 회수하면 곧장 운영 사고

**액션**
- **부여 멱등**: 이미 부여된 역할 재요청 시 no-op (PK 충돌 회피, idempotent 호출 허용)
- **자가 회수 차단**: principal.id == targetMemberId && role == ADMIN 이면 거부
- **마지막 ADMIN 회수 차단**: 회수 직전 ADMIN 카운트 = 1 이면 거부
- 모든 변경에 `AuthAuditEvent` 발행 → 감사 로그 적재

---

## 개선점

### Repository slice 테스트가 AES 의존성 때문에 부팅 실패

**문제**
- `@DataJpaTest` 슬라이스에서 `AesGcmEncryptionService` 빈을 못 찾아 부팅 실패
- prod엔 fail-fast가 정답인데 테스트엔 그게 함정이 됨

**원인**
- 암호화 컴버터가 Entity 매핑 단계에 끼어들어서 슬라이스 테스트도 AES 빈을 요구

**액션플랜**
- `support/NoOpEncryptionService` + `TestPersistenceConfig` 로 슬라이스용 대체 빈 등록
- prod fail-fast는 유지, 테스트 환경만 우회

---

### "마지막 ADMIN 회수 차단" 같은 규칙은 DB 제약으론 못 풀음

**문제**
- 처음엔 "체크 제약(CHECK constraint)이나 트리거로 막을 수 있나?" 잠깐 고민
- 다중 행 카운트 조건은 DB 레벨에서 깔끔하게 안 됨 (트리거 가능하지만 분산 환경엔 race)

**원인**
- 도메인 규칙을 자꾸 "가장 아래 레이어에서 막고 싶다" 는 본능

**액션플랜**
- 도메인 규칙 = Service/Aggregate 레이어에서 트랜잭션 + 비관락(또는 SELECT FOR UPDATE)으로 검증
- DB 제약은 "NOT NULL, FK, UNIQUE" 같은 단순 불변식만 — 비즈니스 규칙은 위로

---

## 배운 점

### prod fail-fast는 가장 싼 안전장치

**배움**
- `AES_KEY` 미설정 시 부팅 실패 → 환경변수 누락이 "빈 키로 암호화" 같은 사일런트 사고로 못 이어짐
- fallback이 있으면 사고가 "한참 뒤에 데이터 다 깨진 채" 발견됨

**의미**
- 운영 환경 필수 설정은 무조건 부팅 시 검증, 누락이면 즉시 죽이기

---

### 멱등성은 클라이언트한테 주는 선물

**배움**
- 부여 API를 멱등하게 만들면 클라이언트가 재시도·중복 호출 걱정을 안 해도 됨
- 멱등 안 하면 "이미 있다" 에러를 클라이언트가 무시할지 처리할지 매번 고민

**의미**
- 모든 "상태 부여" API는 기본적으로 멱등하게 — 진짜 "중복 거부" 가 비즈니스 의미일 때만 예외

---

## 핵심 내용

### 키워드
- `AES-GCM`, `AesGcmEncryptionService`, `@RequireRole`, `RequireRoleAspect`, `RequireRoleOperationCustomizer`, `AuthAuditEvent`, `멱등`, `fail-fast`

### 요약
- **AES-GCM**: 12-byte IV (랜덤) + 16-byte tag. key는 32 byte base64. application-level 컬럼 암호화.
- **@RequireRole**: 메서드/클래스 레벨, AOP에서 SecurityContext 검증. Springdoc Customizer가 401/403을 OpenAPI 응답에 자동 추가.
- **3종 가드**: (1) 부여 멱등 (2) 자가 ADMIN 회수 차단 (3) 마지막 ADMIN 회수 차단.
- **prod fail-fast**: `AES_KEY` 미설정 → 부팅 실패. fallback 금지.

### 코드/명령어
```kotlin
// @RequireRole AOP
@Aspect
@Component
class RequireRoleAspect {
  @Around("@annotation(requireRole) || @within(requireRole)")
  fun check(pjp: ProceedingJoinPoint, requireRole: RequireRole): Any? {
    val auth = SecurityContextHolder.getContext().authentication
        ?: throw BusinessException(AUTH_UNAUTHENTICATED)
    if (requireRole.value !in auth.authorities.map { Role.from(it.authority) }) {
      throw BusinessException(AUTH_FORBIDDEN)
    }
    return pjp.proceed()
  }
}
```

```kotlin
// 마지막 ADMIN 회수 차단
fun revoke(targetId: UUID, role: Role) {
  if (principal.id == targetId && role == Role.ADMIN) {
    throw BusinessException(AUTH_CANNOT_REVOKE_SELF)
  }
  if (role == Role.ADMIN && memberRoleRepository.countByRole(Role.ADMIN) <= 1) {
    throw BusinessException(AUTH_LAST_ADMIN_PROTECTED)
  }
  // ...
}
```

### 참고 자료
- `src/main/kotlin/com/bubaum/buws/global/service/AesGcmEncryptionService.kt`
- `src/main/kotlin/com/bubaum/buws/auth/aop/RequireRoleAspect.kt`
- 커밋: `27b2962` (RegisteredApp + AES-GCM + RBAC AOP), `faf84a3` (Role 관리 ADMIN API)
