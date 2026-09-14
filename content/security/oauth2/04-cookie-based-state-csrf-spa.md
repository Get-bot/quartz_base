---
title: "Spring OAuth2 쿠키 기반 인증 - CSRF 보호와 SPA 호환성 달성하기"
date: 2026-01-13
tags: ["spring-boot", "spring-security", "oauth2", "social-login", "csrf", "cookie", "spa"]
description: "세션 대신 쿠키로 OAuth2 인증 상태를 유지하며 SPA와 통신. HttpCookieOAuth2AuthorizationRequestRepository, SameSite 선택, 보안 체크리스트. 시리즈 4편."
source: https://velog.io/@co-vol/Spring-OAuth2-%EC%BF%A0%ED%82%A4-%EA%B8%B0%EB%B0%98-%EC%9D%B8%EC%A6%9D-CSRF-%EB%B3%B4%ED%98%B8%EC%99%80-SPA-%ED%98%B8%ED%99%98%EC%84%B1-%EB%8B%AC%EC%84%B1%ED%95%98%EA%B8%B0
---

> SPA(Single Page Application)와 OAuth2를 연동할 때 발생하는 상태 관리 문제를 쿠키 기반으로 해결합니다. CSRF 공격을 방어하면서 프론트엔드와 안전하게 통신하는 방법을 다룹니다.

## 들어가며

[[03-user-info-factory-pattern|이전 글]]에서 Factory Pattern으로 Provider별 응답을 통합했습니다. 이번에는 OAuth2 인증 과정에서 **상태를 어떻게 관리**하는지 다룹니다.

### 문제: OAuth2 인증 상태 관리

OAuth2 인증은 여러 단계의 리다이렉트를 거칩니다:

```json
[프론트엔드] → [백엔드] → [카카오] → [백엔드] → [프론트엔드]
    (1)         (2)        (3)        (4)          (5)
```

문제는 (2)와 (4) 사이에 **상태를 어디에 저장할 것인가**입니다:

1. **AuthorizationRequest**: CSRF 방어용 `state` 파라미터 검증에 필요
2. **redirect_uri**: 인증 성공 후 프론트엔드의 어느 페이지로 돌려보낼지

### 세션 vs 쿠키

| 방식 | 장점 | 단점 |
| --- | --- | --- |
| **세션** | 서버에서 안전하게 관리 | 스케일아웃 시 세션 공유 필요 |
| **쿠키** | Stateless, 스케일아웃 용이 | 쿠키 보안 설정 필수 |

SPA + 마이크로서비스 환경에서는 **쿠키 기반**이 더 적합합니다.

---

## 1. HttpCookieOAuth2AuthorizationRequestRepository 구현

Spring Security의 `AuthorizationRequestRepository` 인터페이스를 구현하여 쿠키 기반 저장소를 만듭니다.

### 전체 구조

```java
package com.example.oauth2.repository;

import com.example.oauth2.client.core.dto.OAuth2AuthorizationRequestDto;
import com.example.oauth2.global.properties.Oauth2Properties;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseCookie;
import org.springframework.security.oauth2.client.web.AuthorizationRequestRepository;
import org.springframework.security.oauth2.core.endpoint.OAuth2AuthorizationRequest;
import org.springframework.stereotype.Component;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.Optional;

@Component
@RequiredArgsConstructor
@Slf4j
public class HttpCookieOAuth2AuthorizationRequestRepository
        implements AuthorizationRequestRepository<OAuth2AuthorizationRequest> {

    private final Oauth2Properties oauth2Properties;
    private final ObjectMapper objectMapper;

    // ==================== Repository Interface ====================

    /**
     * 쿠키에서 AuthorizationRequest를 로드합니다.
     */
    @Override
    public OAuth2AuthorizationRequest loadAuthorizationRequest(HttpServletRequest request) {
        return getCookieValue(request, oauth2Properties.cookie().authName())
                .map(this::deserialize)
                .orElse(null);
    }

    /**
     * AuthorizationRequest를 쿠키에 저장합니다.
     */
    @Override
    public void saveAuthorizationRequest(
            OAuth2AuthorizationRequest authorizationRequest,
            HttpServletRequest request,
            HttpServletResponse response
    ) {
        if (authorizationRequest == null) {
            deleteCookie(response, oauth2Properties.cookie().authName());
            return;
        }

        String serialized = serialize(authorizationRequest);
        if (serialized != null) {
            // 1. redirect_uri 쿠키 저장 (프론트엔드가 보낸 콜백 URL)
            String loginRedirectUri = request.getParameter(
                    oauth2Properties.cookie().redirectUriName()
            );
            if (loginRedirectUri != null && !loginRedirectUri.isBlank()) {
                addCookie(response, oauth2Properties.cookie().redirectUriName(),
                        loginRedirectUri);
            }

            // 2. AuthorizationRequest 쿠키 저장
            addCookie(response, oauth2Properties.cookie().authName(), serialized);
        }
    }

    /**
     * 쿠키에서 AuthorizationRequest를 제거하고 반환합니다.
     */
    @Override
    public OAuth2AuthorizationRequest removeAuthorizationRequest(
            HttpServletRequest request,
            HttpServletResponse response
    ) {
        OAuth2AuthorizationRequest authorizationRequest = loadAuthorizationRequest(request);
        deleteCookie(response, oauth2Properties.cookie().authName());
        return authorizationRequest;
    }

    // ==================== 추가 메서드 ====================

    /**
     * 프론트엔드 리다이렉트 URI를 쿠키에서 가져오고 삭제합니다.
     */
    public String getRedirectUriFromCookie(
            HttpServletRequest request,
            HttpServletResponse response
    ) {
        String loginRedirectUri = getCookieValue(
                request, oauth2Properties.cookie().redirectUriName()
        ).orElse("/");

        deleteCookie(response, oauth2Properties.cookie().redirectUriName());
        return loginRedirectUri;
    }

    /**
     * 모든 OAuth2 관련 쿠키를 삭제합니다.
     */
    public void clearAllCookies(HttpServletResponse response) {
        deleteCookie(response, oauth2Properties.cookie().authName());
        deleteCookie(response, oauth2Properties.cookie().redirectUriName());
    }

    // ==================== Cookie Operations ====================

    private Optional<String> getCookieValue(HttpServletRequest request, String cookieName) {
        if (request.getCookies() == null) {
            return Optional.empty();
        }
        return Arrays.stream(request.getCookies())
                .filter(cookie -> cookieName.equals(cookie.getName()))
                .map(Cookie::getValue)
                .findFirst();
    }

    private void addCookie(HttpServletResponse response, String name, String value) {
        ResponseCookie cookie = buildCookie(name, value,
                oauth2Properties.cookie().maxAgeSeconds());
        response.addHeader("Set-Cookie", cookie.toString());
    }

    private void deleteCookie(HttpServletResponse response, String name) {
        ResponseCookie cookie = buildCookie(name, "", 0);
        response.addHeader("Set-Cookie", cookie.toString());
    }

    private ResponseCookie buildCookie(String name, String value, int maxAge) {
        ResponseCookie.ResponseCookieBuilder builder = ResponseCookie.from(name, value)
                .path("/")
                .httpOnly(true)
                .secure(oauth2Properties.cookie().secure())
                .maxAge(maxAge)
                .sameSite("Lax");

        String domain = oauth2Properties.getCookieDomain();
        if (domain != null && !domain.isBlank()) {
            builder.domain(domain);
        }

        return builder.build();
    }

    // ==================== Serialization ====================

    private String serialize(OAuth2AuthorizationRequest request) {
        try {
            OAuth2AuthorizationRequestDto dto = OAuth2AuthorizationRequestDto.from(request);
            String json = objectMapper.writeValueAsString(dto);
            return Base64.getUrlEncoder().encodeToString(
                    json.getBytes(StandardCharsets.UTF_8)
            );
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize OAuth2AuthorizationRequest", e);
            return null;
        }
    }

    private OAuth2AuthorizationRequest deserialize(String serialized) {
        try {
            String json = new String(
                    Base64.getUrlDecoder().decode(serialized),
                    StandardCharsets.UTF_8
            );
            OAuth2AuthorizationRequestDto dto = objectMapper.readValue(
                    json, OAuth2AuthorizationRequestDto.class
            );
            return dto.toOAuth2AuthorizationRequest();
        } catch (Exception e) {
            log.error("Failed to deserialize OAuth2AuthorizationRequest", e);
            return null;
        }
    }
}
```

---

## 2. OAuth2AuthorizationRequestDto: 직렬화용 DTO

`OAuth2AuthorizationRequest`는 직렬화가 어렵습니다. 직렬화 가능한 DTO로 변환합니다.

```java
package com.example.oauth2.client.core.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.security.oauth2.core.endpoint.OAuth2AuthorizationRequest;
import java.util.Map;
import java.util.Set;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OAuth2AuthorizationRequestDto {

    private String authorizationUri;
    private String clientId;
    private String redirectUri;
    private String state;
    private Set<String> scopes;
    private Map<String, Object> additionalParameters;
    private String authorizationRequestUri;
    private Map<String, Object> attributes;
    private String responseType;

    /**
     * OAuth2AuthorizationRequest → DTO 변환
     */
    public static OAuth2AuthorizationRequestDto from(OAuth2AuthorizationRequest request) {
        return OAuth2AuthorizationRequestDto.builder()
                .authorizationUri(request.getAuthorizationUri())
                .clientId(request.getClientId())
                .redirectUri(request.getRedirectUri())
                .state(request.getState())
                .scopes(request.getScopes())
                .additionalParameters(request.getAdditionalParameters())
                .authorizationRequestUri(request.getAuthorizationRequestUri())
                .attributes(request.getAttributes())
                .responseType(request.getResponseType().getValue())
                .build();
    }

    /**
     * DTO → OAuth2AuthorizationRequest 변환
     */
    public OAuth2AuthorizationRequest toOAuth2AuthorizationRequest() {
        return OAuth2AuthorizationRequest.authorizationCode()
                .authorizationUri(this.authorizationUri)
                .clientId(this.clientId)
                .redirectUri(this.redirectUri)
                .state(this.state)
                .scopes(this.scopes)
                .additionalParameters(this.additionalParameters)
                .authorizationRequestUri(this.authorizationRequestUri)
                .attributes(attrs -> attrs.putAll(this.attributes))
                .build();
    }
}
```

---

## 3. 보안 쿠키 설정

### 쿠키 보안 옵션

```java
ResponseCookie cookie = ResponseCookie.from(name, value)
        .path("/")              // 모든 경로에서 접근 가능
        .httpOnly(true)         // JavaScript 접근 차단 (XSS 방어)
        .secure(true)           // HTTPS에서만 전송
        .maxAge(180)            // 3분 (인증 과정 동안만 유효)
        .sameSite("Lax")        // Cross-Site 요청 제한 (CSRF 방어)
        .build();
```

### 각 옵션 설명

| 옵션 | 값 | 목적 |
| --- | --- | --- |
| `httpOnly` | `true` | JavaScript에서 쿠키 접근 차단 → XSS 공격으로 쿠키 탈취 방지 |
| `secure` | `true` | HTTPS에서만 쿠키 전송 → 네트워크 스니핑 방지 |
| `sameSite` | `Lax` | 일반 링크에서만 쿠키 전송 → CSRF 공격 방지 |
| `maxAge` | `180` | 3분 후 자동 만료 → 인증 완료 후 자동 정리 |
| `path` | `/` | 모든 경로에서 쿠키 접근 가능 |

### SameSite 옵션 비교

| **SameSite 옵션** | **특징 및 동작 방식** |
| --- | --- |
| **Strict** | • 같은 사이트 요청에서만 쿠키 전송
• OAuth2 리다이렉트에서 쿠키 전송 안 됨 ❌ |
| **Lax** | • 일반 링크 클릭 시 쿠키 전송 (GET 요청)
• OAuth2 리다이렉트에서 쿠키 전송 됨 ✅
• POST Form 제출 시 쿠키 전송 안 됨 (CSRF 방어) |
| **None** | • 모든 요청에서 쿠키 전송
• CSRF 공격에 취약 ⚠️
• `Secure=true` 필수 |

OAuth2 인증에서는 **Lax**가 최적입니다:

- 카카오에서 리다이렉트로 돌아올 때 쿠키가 전송됨 (GET 요청)
- CSRF 공격(POST Form 제출)은 차단됨

---

## 4. Properties 설정

### Oauth2Properties 클래스

```java
package com.example.global.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.security.oauth2")
public record Oauth2Properties(
        String authorizedRedirectUri,  // 인증 성공 후 프론트엔드 콜백 URL
        CookieProperties cookie
) {

    public record CookieProperties(
            String authName,          // AuthorizationRequest 쿠키 이름
            String redirectUriName,   // redirect_uri 쿠키 이름
            int maxAgeSeconds,        // 쿠키 만료 시간 (초)
            boolean secure            // HTTPS 전용 여부
    ) {

    }

    /**
     * 쿠키 도메인 추출 (예: "example.com")
     */
    public String getCookieDomain() {
        try {
            java.net.URI uri = new java.net.URI(authorizedRedirectUri);
            String host = uri.getHost();

            // localhost는 도메인 설정 불필요
            if (host.equals("localhost") || host.equals("127.0.0.1")) {
                return null;
            }

            // 서브도메인 공유를 위해 메인 도메인 반환
            // api.example.com → example.com
            String[] parts = host.split("\\\\.");
            if (parts.length >= 2) {
                return parts[parts.length - 2] + "." + parts[parts.length - 1];
            }
            return host;
        } catch (Exception e) {
            return null;
        }
    }
}
```

### application.yml 설정

```yaml
app:
  security:
    oauth2:
      # 인증 성공 후 프론트엔드 콜백 URL
      authorized-redirect-uri: https://example.com/oauth2/callback

      cookie:
        auth-name: oauth2_auth_request         # AuthorizationRequest 쿠키 이름
        redirect-uri-name: oauth2_redirect_uri # redirect_uri 쿠키 이름
        max-age-seconds: 180                   # 3분
        secure: true                           # HTTPS 환경 (Prod)

# ==========================================
# 개발 환경 (Local)
# ==========================================
---
spring:
  config:
    activate:
      on-profile: local

app:
  security:
    oauth2:
      authorized-redirect-uri: http://localhost:3000/oauth2/callback
      cookie:
        secure: false  # 로컬 HTTP 환경
```

---

## 5. 프론트엔드 연동

### 로그인 요청

프론트엔드에서 소셜 로그인 버튼 클릭 시:

```jsx
// React 예시
const handleKakaoLogin = () => {
    // 현재 페이지 URL을 redirect_uri로 전달
    const currentPath = window.location.pathname;
    const loginUrl = `${API_BASE_URL}/oauth2/authorization/kakao?redirect_uri=${encodeURIComponent(currentPath)}`;

    window.location.href = loginUrl;
};
```

### 콜백 처리

인증 성공 후 프론트엔드 콜백 페이지:

```jsx
// /oauth2/callback 페이지
import {useEffect} from 'react';
import {useSearchParams, useNavigate} from 'react-router-dom';

function OAuth2Callback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        const error = searchParams.get('error');
        const redirectUri = searchParams.get('redirect_uri');

        if (error) {
            // 에러 처리
            const message = searchParams.get('message');
            alert(`로그인 실패: ${message}`);
            navigate('/login');
            return;
        }

        // 성공 시 원래 페이지로 이동
        // (Refresh Token은 HttpOnly 쿠키로 자동 설정됨)
        navigate(redirectUri || '/');
    }, [searchParams, navigate]);

    return <div>로그인 처리 중...</div>;
}
```

### 인증 플로우 다이어그램
![](https://velog.velcdn.com/images/co-vol/post/ce3a7cca-b741-4069-8475-c02da0ae7ebc/image.png)

---

## 마치며

쿠키 기반 인증 상태 관리를 구현하여 다음을 달성했습니다:

1. **Stateless 아키텍처**: 서버 세션 없이 상태 관리
2. **CSRF 방어**: `SameSite=Lax` + `state` 파라미터 검증
3. **XSS 방어**: `HttpOnly` 쿠키로 JavaScript 접근 차단
4. **SPA 호환**: 프론트엔드 redirect_uri 유지

### 보안 체크리스트

| 항목 | 설정 | 목적 |
| --- | --- | --- |
| `HttpOnly` | `true` | XSS 공격 방어 |
| `Secure` | `true` (운영) | HTTPS 강제 |
| `SameSite` | `Lax` | CSRF 공격 방어 |
| `maxAge` | `180초` | 불필요한 쿠키 자동 정리 |
| `state` 검증 | Spring Security 자동 | CSRF 공격 방어 |

---

원문: [velog · 2026-01-13](https://velog.io/@co-vol/Spring-OAuth2-%EC%BF%A0%ED%82%A4-%EA%B8%B0%EB%B0%98-%EC%9D%B8%EC%A6%9D-CSRF-%EB%B3%B4%ED%98%B8%EC%99%80-SPA-%ED%98%B8%ED%99%98%EC%84%B1-%EB%8B%AC%EC%84%B1%ED%95%98%EA%B8%B0)
