---
title: "Spring Boot + jOOQ에서 ThreadLocal 기반 멀티테넌시 접근 제어 구현하기"
date: 2026-01-13
tags: ["spring-boot", "jooq", "threadlocal", "multi-tenancy", "authorization", "security"]
description: "수십 개 테이블이 결제앱 ID를 참조하는 환경에서 파라미터 전파 대신 Filter + ThreadLocal + jOOQ Condition으로 쿼리 레벨 데이터 격리. 장단점과 비동기 전파 한계 포함."
source: https://velog.io/@co-vol/Spring-Boot-jOOQ%EC%97%90%EC%84%9C-ThreadLocal-%EA%B8%B0%EB%B0%98-%EB%A9%80%ED%8B%B0%ED%85%8C%EB%84%8C%EC%8B%9C-%EC%A0%91%EA%B7%BC-%EC%A0%9C%EC%96%B4-%EA%B5%AC%ED%98%84%ED%95%98%EA%B8%B0
---

>이 글에서는 Filter, ThreadLocal, 그리고 jOOQ Condition을 조합하여, 기존 쿼리의 수정 없이 우아하게 데이터 격리를 구현한 경험을 공유합니다.

## 문제 상황
최근 이상거래 모니터링 시스템을 개발하며 **'데이터 격리'** 문제에 직면했습니다. 시스템 내에 다수의 **결제 앱(PayApp)**이 공존하는 환경이라, 관리자 권한에 따라 담당 앱 데이터만 엄격하게 **격리하여** 보여주는 구조가 필요했습니다.

> 결국 멀티테넌시(Multi-tenancy) 문제구나.

처음에는 단순하게 생각했습니다. API 엔드포인트마다 권한 검증 로직을 넣으면 되지 않을까? 하지만 이 시스템에는 결제 앱 ID를 참조하는 테이블이 수십 개에 달했습니다. 감지 조건, 감지 로그, 알림 설정, 수신자 관리 등 모든 도메인이 결제 앱과 연결되어 있었습니다.

> 모든 Repository 메서드에 memberId를 파라미터로 넘기고, 매번 권한 체크를 하라고?

이는 지나치게 비효율적이었습니다. 기존 코드를 전부 수정해야 할 뿐만 아니라, **실수로 누락될 경우 데이터 유출이라는 치명적인 보안 사고**로 이어질 수 있기 때문입니다. 저는 더 안전하고 우아한 방법이 필요했습니다.

## 설계 고민

### AOP vs Filter

처음 떠오른 방법은 AOP였습니다. @PreAuthorize나 커스텀 어노테이션으로 메서드 레벨에서 권한을 체크하는 방식입니다.

```java
// AOP 방식 (고려했지만 선택하지 않음)
@AuthorizePayApp
public PayAppInfo getPayAppInfo(UUID payAppId) {
    // ...
}
```

하지만 목록 조회 API에서 문제가 발생했습니다. 결과를 가져온 후 애플리케이션 레벨에서 필터링하면 페이지네이션(Pagination)이 깨집니다. 즉, **쿼리 레벨에서 조건을 걸어야 했습니다.**

> Filter에서 컨텍스트를 설정하고, Repository에서 조건을 읽어오면 되지 않을까?

Filter는 모든 요청의 진입점입니다. 여기서 사용자 정보를 기반으로 접근 가능한 앱 목록을 조회하고, 어딘가에 저장해두면 Repository 계층에서 꺼내 쓸 수 있을 것입니다.

### 파라미터 전파 vs ThreadLocal

그렇다면 "어딘가"는 어디일까요? 두 가지 선택지가 있었습니다.

**방법 1: 파라미터 전파**
```java
// Controller → Service → Repository로 계속 넘겨야 함
public List<DetectCond> getList(UUID memberId, Set<UUID> accessibleAppIds) {
    return repository.findAll(memberId, accessibleAppIds);
}
```

이 방법을 시도해 보려 했으나, ~~5분 만에 포기...~~ 구현을 시작하자마자 한계를 직감했습니다. 모든 메서드 시그니처를 변경해야 했고, 파라미터가 누락되어도 컴파일 에러가 발생하지 않아 전체 데이터가 노출될 위험이 컸습니다.

**방법 2: ThreadLocal**
```java
// 어디서든 현재 요청의 컨텍스트에 접근
Set<UUID> appIds = AppAccessContext.getAccessibleAppIds();
```

ThreadLocal은 스레드별로 독립된 저장소를 제공합니다. HTTP 요청은 하나의 스레드에서 처리되므로, 요청 시작 시 설정하고 끝날 때 정리하면 완벽한 '요청 스코프' 저장소가 됩니다.

> 이거다. 기존 코드를 거의 건드리지 않고 접근 제어를 적용할 수 있겠다.

## 구현

### 전체 구조
![](https://velog.velcdn.com/images/co-vol/post/81e6cf16-19e4-46f1-84c3-479fccc92ef9/image.png)

### Step 1: ThreadLocal 컨텍스트

먼저 요청 스코프의 접근 정보를 저장할 컨텍스트를 만들었습니다.

```java
public class AppAccessContext {

    private static final ThreadLocal<AppAccessInfo> CONTEXT = new ThreadLocal<>();

    // Filter에서 호출
    public static void set(UUID memberId, Set<UUID> accessibleAppIds, boolean isSuperAdmin) {
        CONTEXT.set(new AppAccessInfo(memberId, accessibleAppIds, isSuperAdmin));
    }

    // Repository에서 호출
    public static Set<UUID> getAccessibleAppIds() {
        AppAccessInfo info = CONTEXT.get();
        return info != null ? info.accessibleAppIds() : null;
    }

    // 슈퍼관리자 여부 확인
    public static boolean isSuperAdmin() {
        AppAccessInfo info = CONTEXT.get();
        return info != null && info.isSuperAdmin();
    }

    // 필터링이 필요한지 확인
    public static boolean requiresFiltering() {
        AppAccessInfo info = CONTEXT.get();
        if (info == null) {
            return false; // 컨텍스트 없음 (public API 등)
        }
        return !info.isSuperAdmin() && info.accessibleAppIds() != null;
    }

    // Filter의 finally에서 반드시 호출
    public static void clear() {
        CONTEXT.remove();
    }

    private record AppAccessInfo(
            UUID memberId,
            Set<UUID> accessibleAppIds,
            boolean isSuperAdmin
    ) {
        AppAccessInfo {
            // 불변성 보장
            accessibleAppIds = accessibleAppIds != null
                    ? Collections.unmodifiableSet(accessibleAppIds)
                    : Collections.emptySet();
        }
    }
}
```

핵심은 `requiresFiltering()` 메서드입니다. 슈퍼관리자이거나 컨텍스트가 설정되지 않은 경우(외부 API 등)에는 필터링 로직을 건너뛰게 설계했습니다.

### Step 2: Filter 구현

Spring Security의 필터 체인에 위치할 커스텀 필터입니다.

```java
@Component
@RequiredArgsConstructor
public class AppAccessFilter extends OncePerRequestFilter {

    private final MemberPayAppAccessRepository memberPayAppAccessRepository;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        try {
            setupAppAccessContext();
            filterChain.doFilter(request, response);
        } finally {
            // 반드시 정리해야 함 - 스레드 풀 재사용 시 오염 방지
            AppAccessContext.clear();
        }
    }

    private void setupAppAccessContext() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated()) {
            return; // 인증되지 않은 요청
        }

        if (!(authentication.getPrincipal() instanceof PrincipalDetails principal)) {
            return;
        }

        UUID memberId = UUID.fromString(principal.id());
        List<String> roles = principal.getRole(principal.role());
        boolean isSuperAdmin = roles.contains(MemberRole.SUPER_ADMIN.getValue());

        if (isSuperAdmin) {
            // 슈퍼관리자는 DB 조회 없이 바로 설정
            AppAccessContext.set(memberId, null, true);
        } else {
            // 일반 관리자는 할당된 앱 목록 조회
            Set<UUID> accessibleAppIds = memberPayAppAccessRepository
                    .findPayAppIdsByMemberId(memberId);
            AppAccessContext.set(memberId, accessibleAppIds, false);
        }
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        // 외부 API 경로는 필터 제외
        String path = request.getRequestURI();
        return path.startsWith("/api/v1/external/")
                || path.startsWith("/api/v1/payment/result/");
    }
}
```

> `finally` 블록에서 `clear()`를 호출하는 것이 매우 중요합니다.

Tomcat과 같은 WAS는 스레드 풀을 사용합니다. 이전 요청에서 설정된 `ThreadLocal` 값이 다음 요청에 남아있을 경우, **다른 사용자의 데이터가 노출되는 치명적인 보안 사고**가 발생할 수 있습니다.

### Step 3: Repository 구현

멤버-앱 접근 권한을 관리하는 Repository입니다.

```java
@Repository
@RequiredArgsConstructor
public class MemberPayAppAccessRepository extends MemberPayAppAccessDao {

    private final DSLContext dslContext;

    // 멤버가 접근 가능한 앱 ID 목록 조회
    public Set<UUID> findPayAppIdsByMemberId(UUID memberId) {
        return new HashSet<>(
                dslContext
                        .select(MEMBER_PAY_APP_ACCESS.PAY_APP_ID)
                        .from(MEMBER_PAY_APP_ACCESS)
                        .where(MEMBER_PAY_APP_ACCESS.MEMBER_ID.eq(memberId))
                        .fetchInto(UUID.class)
        );
    }

    // 권한 부여
    public void grantAccess(UUID memberId, UUID payAppId, LocalDateTime createdAt) {
        dslContext
                .insertInto(MEMBER_PAY_APP_ACCESS)
                .set(MEMBER_PAY_APP_ACCESS.MEMBER_ID, memberId)
                .set(MEMBER_PAY_APP_ACCESS.PAY_APP_ID, payAppId)
                .set(MEMBER_PAY_APP_ACCESS.REG_DATE, createdAt)
                .onDuplicateKeyIgnore() // 중복 무시
                .execute();
    }

    // 권한 회수
    public void revokeAccess(UUID memberId, UUID payAppId) {
        dslContext
                .deleteFrom(MEMBER_PAY_APP_ACCESS)
                .where(MEMBER_PAY_APP_ACCESS.MEMBER_ID.eq(memberId))
                .and(MEMBER_PAY_APP_ACCESS.PAY_APP_ID.eq(payAppId))
                .execute();
    }
}
```

### Step 4: jOOQ 조건 유틸리티

가장 중요한 부분입니다. 동적 쿼리의 복잡성을 캡슐화하여, 기존 쿼리에 접근 제어 조건을 손쉽게 끼워 넣을 유틸리티 클래스입니다.

```java
@NoArgsConstructor(access = AccessLevel.PRIVATE)
public final class PayAppAccess {

    /**
     * PAY_APP_ID 필드를 가진 테이블 조회 시 사용
     * 예: .where(PayAppAccess.restrictByAppId(TABLE.PAY_APP_ID))
     */
    public static Condition restrictByAppId(Field<UUID> payAppIdField) {
        if (!AppAccessContext.requiresFiltering()) {
            // 슈퍼관리자 또는 컨텍스트 미설정
            return DSL.trueCondition();
        }

        Set<UUID> accessibleAppIds = AppAccessContext.getAccessibleAppIds();

        if (accessibleAppIds == null || accessibleAppIds.isEmpty()) {
            // 접근 가능한 앱이 없으면 결과도 없음
            return DSL.falseCondition();
        }

        return payAppIdField.in(accessibleAppIds);
    }

    /**
     * 단일 리소스 접근 검증 (상세 조회, 수정, 삭제 시)
     */
    public static void validateAccess(UUID payAppId) {
        if (!AppAccessContext.hasAccessTo(payAppId)) {
            throw new CustomException(ErrorCode.FORBIDDEN, "접근 권한이 없는 결제 앱입니다.");
        }
    }
}
```

초기에는 `boolean`을 반환하도록 설계했으나, 사용하는 곳마다 `if`문을 작성해야 하는 불편함이 있었습니다.

```java
// 처음 시도 (불편함)
if (PayAppAccess.hasAccess(payAppId)) {
    conditions.add(TABLE.PAY_APP_ID.in(accessibleAppIds));
}
```

> jOOQ의 `Condition` 객체를 직접 반환하면 훨씬 깔끔해지지 않을까?

`restrictByAppId` 메서드는 상황에 따라 `trueCondition()`, `falseCondition()`, 또는 `in` 조건을 반환합니다. 덕분에 비즈니스 로직에서는 복잡한 분기 처리 없이 이 메서드 하나만 호출하면 됩니다.

## 적용 예시

기존 쿼리에 **단 한 줄**만 추가하면 데이터 격리가 적용됩니다.

```java
// 기존 코드
public List<DetectCondDto> getList(DetectCondListReqDto reqDto) {
    return dslContext
            .select(/* ... */)
            .from(APP_WITHDRAW_DETECT_COND)
            .where(APP_WITHDRAW_DETECT_COND.DEL_YN.eq("N"))
            .and(/* 기존 검색 조건 */)
            .fetchInto(DetectCondDto.class);
}

// 접근 제어 적용 후
public List<DetectCondDto> getList(DetectCondListReqDto reqDto) {
    return dslContext
            .select(/* ... */)
            .from(APP_WITHDRAW_DETECT_COND)
            .where(APP_WITHDRAW_DETECT_COND.DEL_YN.eq("N"))
            .and(PayAppAccess.restrictByAppId(APP_WITHDRAW_DETECT_COND.PAY_APP_ID)) // 이 한 줄 추가
            .and(/* 기존 검색 조건 */)
            .fetchInto(DetectCondDto.class);
}
```

단일 리소스 접근 시에는 검증 메서드를 사용한다.

```java
public DetectCondDto getById(UUID id) {
    DetectCondDto dto = repository.findById(id);

    // 접근 권한 검증
    PayAppAccess.validateAccess(dto.payAppId());

    return dto;
}
```

## 장단점 분석

### 장점

- **기존 코드 수정 최소화**: 쿼리에 한 줄만 추가하면 됨
- **일관성**: Filter에서 한 번 설정하면 모든 곳에서 동일한 컨텍스트 사용
- **성능**: 슈퍼관리자는 DB 조회 없이 바로 통과
- **테스트 용이**: 테스트 시 `AppAccessContext.set()`으로 컨텍스트 주입 가능

### 단점

- **ThreadLocal 관리 필수**: `clear()` 누락 시 메모리 누수 또는 보안 사고
- **비동기 처리 주의**: `@Async` 메서드에서는 컨텍스트가 전파되지 않음
- **IDE 지원 부족**: 호출 관계가 명시적이지 않아 추적이 어려울 수 있음

### 개선 방향

1. **비동기 지원**: `TaskDecorator`를 구현하여 비동기 스레드에도 컨텍스트 전파
2. **캐싱**: 동일 요청 내 반복 조회 시 캐시 활용
3. **감사 로그**: 접근 시도 기록으로 보안 모니터링 강화

## 마무리

멀티테넌시 접근 제어를 구현하면서 중요한 점을 배웠습니다.

> 모든 메서드에 파라미터를 추가하는 건 확장 가능한 해결책이 아니다.

ThreadLocal은 '요청 스코프'라는 개념을 깔끔하게 추상화해 줍니다. 또한, **jOOQ의 Condition은 조립이 가능(Composable)합니다.** `trueCondition()` 과 `falseCondition()`을 활용하면 조건부 로직을 아주 우아하게 처리할 수 있습니다.

> jOOQ의 Condition은 합성이 자유롭다.

이 패턴은 멀티테넌시뿐만 아니라, **논리적 삭제(Soft Delete)**나 **활성 상태 필터링** 등 "전역적인 데이터 필터링이 필요한 상황"에서 범용적으로 활용할 수 있을 것입니다.

---

원문: [velog · 2026-01-13](https://velog.io/@co-vol/Spring-Boot-jOOQ%EC%97%90%EC%84%9C-ThreadLocal-%EA%B8%B0%EB%B0%98-%EB%A9%80%ED%8B%B0%ED%85%8C%EB%84%8C%EC%8B%9C-%EC%A0%91%EA%B7%BC-%EC%A0%9C%EC%96%B4-%EA%B5%AC%ED%98%84%ED%95%98%EA%B8%B0)
