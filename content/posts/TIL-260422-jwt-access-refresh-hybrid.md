---
title: "[TIL-260422] JWT Access+Refresh 하이브리드 — Stateless와 Stateful의 결합"
date: 2026-04-22
tags: ["JWT", "Spring Security", "Valkey", "Redis", "Authentication", "Token Rotation", "OAuth"]
categories: ["TIL"]
description: "순수 Session과 순수 JWT의 약점을 서로 보완하는 하이브리드 인증. Device Family Rotation, Kill-Switch, Replay Detection까지 왜 이런 구조가 필요한가"
---

## 잘한 점

### Stateless와 Stateful의 약점을 서로 보완하는 하이브리드 설계

**상황**
- 출금 API 서버는 금융 수준 보안 + 모바일 트래픽 수평 확장을 동시에 요구
- 순수 Session은 매 요청 Valkey 조회 → 고트래픽 시 병목
- 순수 JWT는 토큰 탈취 시 TTL 끝까지 차단 불가 → 금융 서비스에서 수용 불가

**액션**
- Access 토큰: Stateless JWT (TTL 15분, 서명 검증만) — 매 요청 스토어 조회 없음, 수평 확장 쉬움
- Refresh 토큰: Stateful (TTL 7일, Valkey 저장) — 탈취 의심 시 즉시 Kill-Switch 가능
- Device-scoped Token Family Rotation + Multi-device LRU + 3초 grace window를 Lua 스크립트로 원자 보장
- 쿠키: HttpOnly + Secure + SameSite=Strict → XSS/CSRF 3중 방어

**칭찬**
- "빠른 검증"과 "즉시 차단"을 한 시스템에서 같이 얻는 구조가 마음에 듦
- 단순히 "둘 다 쓴다"가 아니라 각 토큰의 책임을 나눠 Plan(정책) / Design(구현) 문서를 분리한 점
- rotation을 Lua로 원자화해서 race condition을 언어 단이 아니라 스토어 단에서 차단한 판단

---

## 개선점

### Replay 탐지가 정당한 사용자까지 kill 할 수 있는 risk

**문제**
- 공격자가 탈취한 Refresh 토큰으로 정당한 사용자보다 **먼저** refresh를 치면, 정당한 사용자도 나중에 같은 토큰으로 시도할 때 REPLAY로 걸림
- 정당한 사용자는 아무 잘못 없이 device family 전체가 revoke → 강제 재로그인 (UX 저하)
- 3초 grace window는 네트워크 지연은 커버하지만 공격자 선점은 못 막음

**원인**
- Replay 탐지는 "누가 진짜 주인인가"를 판단 안 하고 "토큰 일치 여부"만 본다
- 탈취 사실 자체는 서버가 인지 불가 → 가장 안전한 선택이 "둘 다 일단 차단"

**액션플랜**
- 클라이언트 exponential backoff로 refresh 재시도 최소화
- REPLAY 탐지 로그에 IP/UA/timestamp 남겨 사후 포렌식 경로 마련 (AuditLog에 설계됨)
- 프론트에 "비정상 활동 감지, 다시 로그인해주세요" 공지 UI → 사용자 납득 가능하게
- 장기적으로 2FA 붙여 REPLAY 시 전체 kill 대신 2차 인증으로 격상

### Valkey 단일 의존의 가용성 리스크

**문제**
- 인증 흐름이 Valkey 가용성에 묶임. Valkey 다운 = refresh 전부 실패 = 전원 재로그인
- 로컬/Dev는 단일 컨테이너라 가용성 고려 없음

**원인**
- Stateful Refresh의 대가 — 상태를 어디엔가 두면 거기가 SPOF
- Access를 Stateless로 만든 설계 의도와의 trade-off

**액션플랜**
- Prod는 ElastiCache for Valkey Cluster / Sentinel 필수 (설계 문서 명시)
- Valkey degraded 시 Access 유효 기간 내엔 서비스 유지, 만료 후 재로그인 유도

---

## 배운 점

### "Stateless vs Stateful"은 선택이 아니라 결합의 문제

**배움**
- 둘 중 하나 고르는 게 아니라 **책임을 분리해서 같이 쓰는 게** 금융/중보안 서비스의 패턴이라는 걸 설계 쓰면서 체감
- Access의 책임 = "매 요청 빠른 본인 확인" → Stateless가 답
- Refresh의 책임 = "세션 연장 + 탈취 대응" → Stateful 필수
- TTL도 책임에 맞춰 결정 — 짧은 Access는 탈취 피해 최소화, 긴 Refresh는 UX 유지

**의미**
- 앞으로 인증 설계 볼 때 "Stateless만 쓰냐 / Session만 쓰냐" 논쟁은 공허하다
- 중요한 건 **각 토큰의 책임**과 그에 맞는 저장 전략
- 비슷한 패턴은 다른 도메인에도 적용 가능 (조회는 Stateless 캐시, 수정은 Stateful 분산락 등)

### Access TTL 15분의 sweet spot

**배움**
- 15분이 적당한 이유: 탈취 시 최악 피해 15분 (SPA 자동 갱신으로 UX 영향 없음) + refresh 빈도 낮아 서버 부하 적음
- 1분으로 줄이면 refresh 트래픽 15배 증가, 1시간으로 늘리면 탈취 피해 4배 증가

**의미**
- 숫자 하나하나가 "왜 이 값인가" 근거가 있어야 한다. 기본값 복붙하면 trade-off가 안 보임
- 다음 서비스 TTL 결정 시 "탈취 피해 허용 시간" + "refresh 트래픽 감당 가능량" 두 축으로

---

## 핵심 내용

### 키워드
- `JWT`, `Stateless`, `Stateful Refresh`, `Valkey`, `Device-scoped Family Rotation`, `Kill-Switch`, `HttpOnly Cookie`, `Replay Detection`

### 요약
- **Access (Stateless, 15분)**: 매 요청 서명만 검증 → p95 5ms 이하, 수평 확장 용이
- **Refresh (Stateful, 7일, Valkey)**: 발급 이력 추적 → 탈취 의심 시 family 전체 revoke 가능
- **Device Family Rotation**: 리프레시마다 jti 갱신, 이전 jti는 3초 grace 후 만료. 만료 jti 재사용 시 REPLAY → 기기 family kill
- **Multi-device LRU**: 사용자당 기기 3개 상한, 초과 시 가장 오래된 기기 자동 로그아웃
- **쿠키 전략**: Refresh만 HttpOnly+Secure+SameSite=Strict (XSS/CSRF 방어), Access는 Bearer 헤더

### 트레이드오프 비교

| 방식 | 검증 비용 | 즉시 무효화 | 수평 확장 | 탈취 대응 |
|------|---------|-----------|---------|---------|
| Pure Session | 높음 (매 요청 스토어) | ✓ | 스토어가 SPOF | 즉시 |
| Pure JWT | 낮음 (서명만) | ✗ | 쉬움 | TTL 만료까지 불가 |
| Hybrid (이 프로젝트) | 낮음 (Access만) | Refresh 차단 시점 | 쉬움 | Refresh family kill |

### 탈취 시나리오 → Kill-Switch

```
[공격자] 탈취한 old_jti로 refresh 시도
      ↓
[서버] RefreshTokenStore.rotate() Lua 원자 실행
      ↓  old_jti ≠ current && old_jti ≠ prev (grace 3초 만료)
[REPLAY 탐지]
      ↓
[Kill-Switch] 해당 device family 전체 revoke (Valkey ZSET 제거)
      ↓
정당한 사용자도 재로그인 필요 (감사 로그 + 프론트 공지)
```

### 코드/명령어

**TTL 설정** (`application.yaml`)
```yaml
jwt:
  access-token-validity: PT15M       # 15분
  refresh-token-validity: P7D        # 7일

cookie:
  refresh-name: buws_refresh
  max-age-seconds: 604800            # 7일 (refresh TTL과 일치)

refresh:
  grace-seconds: 3                   # Rotation grace (current→prev TTL)
```

**Refresh 검증 분기** (`AuthService.refresh`)
```kotlin
val claims = try {
    jwtProvider.parseRefreshClaims(refreshToken)
} catch (e: ExpiredJwtException) {
    throw BusinessException(ErrorCode.AUTH_REFRESH_EXPIRED)    // A401-3: 자동 재로그인 가능
} catch (e: JwtException) {
    throw BusinessException(ErrorCode.AUTH_REFRESH_INVALID)    // A401-2: 로그인 페이지
}

when (val outcome = refreshTokenStore.rotate(userId, deviceId, oldJti, newJti, now)) {
    is RotateOutcome.Success -> { /* 새 토큰 발급 */ }
    is RotateOutcome.Replay -> {
        auditLogger.log(AuthAuditEvent.RefreshReplay(userId, deviceId))
        throw BusinessException(ErrorCode.AUTH_REFRESH_REPLAY) // A401-5: 즉시 로그아웃
    }
    is RotateOutcome.Unknown -> throw BusinessException(ErrorCode.AUTH_REFRESH_INVALID)
}
```

### 에러 코드 매핑

| 코드 | HTTP | 의미 | 클라이언트 동작 |
|------|------|------|---------------|
| A401-1 AUTH_REFRESH_MISSING | 401 | 쿠키 없음 | 로그인 페이지 |
| A401-2 AUTH_REFRESH_INVALID | 401 | 서명/형식 오류 | 로그인 페이지 |
| A401-3 AUTH_REFRESH_EXPIRED | 401 | TTL 만료 | 자동 재로그인 시도 |
| A401-5 AUTH_REFRESH_REPLAY | 401 | 재사용 탐지 | 즉시 로그아웃 + 보안 공지 |

### 참고 자료
- `docs/archive/2026-04/auth-rbac/design.md` — Device Family Rotation 상세 설계
- `src/main/kotlin/com/bubaum/buws/auth/service/AuthService.kt` — login/refresh/logout 구현
- `src/main/kotlin/com/bubaum/buws/auth/token/RefreshTokenStore.kt` — Lua 원자 rotation
- 커밋 BUWS-19 ~ BUWS-20 — Device-scoped Rotation, HttpOnly Cookie 구현
