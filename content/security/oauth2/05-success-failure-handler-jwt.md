---
title: "Spring OAuth2 Success/Failure Handler - JWT 발급과 에러 처리 전략"
date: 2026-01-14
tags: ["spring-boot", "spring-security", "oauth2", "social-login", "jwt", "error-handling"]
description: "인증 성공 시 자체 JWT 발급과 Refresh 쿠키, 실패 시 프론트가 처리할 수 있는 에러 분류 전략. 시리즈 5편(완결)."
source: https://velog.io/@co-vol/Spring-OAuth2-SuccessFailure-Handler-JWT-%EB%B0%9C%EA%B8%89%EA%B3%BC-%EC%97%90%EB%9F%AC-%EC%B2%98%EB%A6%AC-%EC%A0%84%EB%9E%B5
---

> OAuth2 인증 성공 후 자체 JWT를 발급하고, 실패 시 프론트엔드 친화적인 에러 응답을 반환합니다. 사용자 경험을 해치지 않으면서 보안을 유지하는 핸들러 설계를 다룹니다.

## 들어가며

[[04-cookie-based-state-csrf-spa|이전 글]]에서 쿠키 기반 인증 상태 관리를 구현했습니다. 이번에는 OAuth2 인증의 **마지막 단계**인 핸들러를 다룹니다.

### 핸들러의 역할

![](https://velog.velcdn.com/images/co-vol/post/d245404a-8015-46b8-b414-ba0ca619986a/image.png)

---

## 1. OAuth2AuthenticationSuccessHandler 구현

### 전체 구조

```java
package com.example.oauth2.handler;

import com.example.global.exception.CustomException;
import com.example.global.exception.ErrorCode;
import com.example.global.properties.Oauth2Properties;
import com.example.global.util.RefreshTokenCookieUtils;
import com.example.member.dto.Oauth2LoginResultDto;
import com.example.member.service.MemberOAuth2LinkService;
import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.userinfo.CustomOAuth2User;
import com.example.oauth2.client.core.userinfo.CustomOidcUser;
import com.example.oauth2.repository.HttpCookieOAuth2AuthorizationRequestRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

@Component
@RequiredArgsConstructor
@Slf4j
public class OAuth2AuthenticationSuccessHandler
        extends SimpleUrlAuthenticationSuccessHandler {

    private final HttpCookieOAuth2AuthorizationRequestRepository cookieRepository;
    private final MemberOAuth2LinkService memberLinkService;
    private final Oauth2Properties oauth2Properties;
    private final RefreshTokenCookieUtils refreshTokenCookieUtils;

    @Override
    public void onAuthenticationSuccess(
            HttpServletRequest request,
            HttpServletResponse response,
            Authentication authentication
    ) throws IOException {

        try {
            // 1. 프론트엔드 redirect_uri 쿠키에서 조회
            String loginRedirectUri = cookieRepository
                    .getRedirectUriFromCookie(request, response);

            // 2. OAuth2 사용자 정보 추출
            OAuth2UserInfo userInfo = extractUserInfo(authentication);

            log.info("OAuth2 login success: provider={}, providerId={}",
                    userInfo.provider(), userInfo.providerId());

            // 3. 회원 매핑/생성 + JWT 발급
            Oauth2LoginResultDto result = memberLinkService
                    .processOAuth2Login(userInfo);

            // 4. Refresh Token을 HttpOnly 쿠키에 저장
            refreshTokenCookieUtils.addRefreshTokenCookie(
                    response, result.refreshToken()
            );

            // 5. 프론트엔드 콜백 URL로 리다이렉트
            String targetUrl = buildSuccessUrl(loginRedirectUri);
            getRedirectStrategy().sendRedirect(request, response, targetUrl);

        } catch (Exception e) {
            log.error("OAuth2 success handler failed", e);
            handleFailure(request, response, e);
        }
    }

    /**
     * 성공 리다이렉트 URL 빌드
     */
    private String buildSuccessUrl(String callbackUrl) {
        return UriComponentsBuilder
                .fromUriString(oauth2Properties.authorizedRedirectUri())
                .queryParam(
                        oauth2Properties.cookie().redirectUriName(),
                        callbackUrl
                )
                .encode(StandardCharsets.UTF_8)
                .build()
                .toUriString();
    }

    /**
     * 핸들러 내 예외 발생 시 실패 처리
     */
    private void handleFailure(
            HttpServletRequest request,
            HttpServletResponse response,
            Exception e
    ) throws IOException {
        String targetUrl = UriComponentsBuilder
                .fromUriString(oauth2Properties.authorizedRedirectUri())
                .queryParam("error", "login_failed")
                .encode(StandardCharsets.UTF_8)
                .build()
                .toUriString();

        getRedirectStrategy().sendRedirect(request, response, targetUrl);
    }

    /**
     * Authentication에서 OAuth2UserInfo 추출
     */
    private OAuth2UserInfo extractUserInfo(Authentication authentication) {
        Object principal = authentication.getPrincipal();

        // Java 21 Pattern Matching for switch
        return switch (principal) {
            case CustomOidcUser oidc -> oidc.oauth2UserInfo();
            case CustomOAuth2User oauth2 -> oauth2.oauth2UserInfo();
            default -> throw CustomException.withDetails(
                    ErrorCode.BAD_REQUEST,
                    "Unexpected principal type: " + principal.getClass().getSimpleName()
            );
        };
    }
}
```

### 핵심 포인트

1. **extractUserInfo()**: CustomOidcUser/CustomOAuth2User에서 통합 DTO 추출
2. **processOAuth2Login()**: 회원 매핑/생성 + JWT 발급을 서비스에 위임
3. **Refresh Token 쿠키**: HttpOnly 쿠키로 안전하게 저장
4. **예외 처리**: 핸들러 내 예외도 프론트엔드 친화적으로 응답

---

## 2. 회원 매핑 서비스

OAuth2 인증 후 기존 회원과 매핑하거나 새 회원을 생성합니다.

```java
package com.example.member.service;

import com.example.auth.service.JwtTokenService;
import com.example.member.domain.Member;
import com.example.member.domain.MemberOAuth2Link;
import com.example.member.dto.Oauth2LoginResultDto;
import com.example.member.repository.MemberOAuth2LinkRepository;
import com.example.member.repository.MemberRepository;
import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class MemberOAuth2LinkService {

    private final MemberRepository memberRepository;
    private final MemberOAuth2LinkRepository linkRepository;
    private final JwtTokenService jwtTokenService;

    /**
     * OAuth2 로그인 처리
     * 1. 기존 연동 확인 → 있으면 해당 회원으로 로그인
     * 2. 이메일로 기존 회원 확인 → 있으면 연동 추가
     * 3. 없으면 새 회원 생성 + 연동
     */
    @Transactional
    public Oauth2LoginResultDto processOAuth2Login(OAuth2UserInfo userInfo) {
        // 1. 기존 OAuth2 연동 확인
        Optional<MemberOAuth2Link> existingLink = linkRepository
                .findByProviderAndProviderId(
                        userInfo.provider(),
                        userInfo.providerId()
                );

        Member member;

        if (existingLink.isPresent()) {
            // 기존 연동이 있으면 해당 회원 사용
            member = existingLink.get().getMember();
            // 프로필 정보 업데이트 (선택적)
            updateMemberProfile(member, userInfo);
        } else {
            // 이메일로 기존 회원 찾기
            member = findOrCreateMember(userInfo);
            // OAuth2 연동 추가
            createOAuth2Link(member, userInfo);
        }

        // JWT 토큰 발급
        String accessToken = jwtTokenService.createAccessToken(member);
        String refreshToken = jwtTokenService.createRefreshToken(member);

        return new Oauth2LoginResultDto(accessToken, refreshToken, member.getId());
    }

    private Member findOrCreateMember(OAuth2UserInfo userInfo) {
        // 이메일로 기존 회원 찾기
        if (userInfo.email() != null) {
            Optional<Member> existingMember = memberRepository
                    .findByEmail(userInfo.email());

            if (existingMember.isPresent()) {
                return existingMember.get();
            }
        }

        // 새 회원 생성
        Member newMember = Member.builder()
                .email(userInfo.email())
                .nickname(userInfo.getDisplayName())
                .profileImageUrl(userInfo.profileImageUrl())
                .phoneNumber(userInfo.getNormalizedPhoneNumber())
                .build();

        return memberRepository.save(newMember);
    }

    private void createOAuth2Link(Member member, OAuth2UserInfo userInfo) {
        MemberOAuth2Link link = MemberOAuth2Link.builder()
                .member(member)
                .provider(userInfo.provider())
                .providerId(userInfo.providerId())
                .email(userInfo.email())
                .build();

        linkRepository.save(link);
    }

    private void updateMemberProfile(Member member, OAuth2UserInfo userInfo) {
        // 프로필 이미지, 닉네임 등 업데이트 (선택적)
        if (userInfo.profileImageUrl() != null && member.getProfileImageUrl() == null) {
            member.updateProfileImage(userInfo.profileImageUrl());
        }
    }
}
```

### Oauth2LoginResultDto

```java
package com.example.member.dto;

public record Oauth2LoginResultDto(
        String accessToken,
        String refreshToken,
        Long memberId
) {

}
```

---

## 3. Refresh Token 쿠키 유틸리티

```java
package com.example.global.util;

import com.example.global.properties.JwtProperties;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class RefreshTokenCookieUtils {

    private final JwtProperties jwtProperties;

    /**
     * Refresh Token을 HttpOnly 쿠키에 저장
     */
    public void addRefreshTokenCookie(
            HttpServletResponse response,
            String refreshToken
    ) {
        ResponseCookie cookie = ResponseCookie
                .from("refresh_token", refreshToken)
                .path("/")
                .httpOnly(true)                    // JavaScript 접근 차단
                .secure(jwtProperties.cookie().secure())  // HTTPS 전용
                .maxAge(jwtProperties.refreshTokenExpiration())  // 7일 등
                .sameSite("Lax")                   // CSRF 방어
                .build();

        response.addHeader("Set-Cookie", cookie.toString());
    }

    /**
     * Refresh Token 쿠키 삭제 (로그아웃 시)
     */
    public void deleteRefreshTokenCookie(HttpServletResponse response) {
        ResponseCookie cookie = ResponseCookie
                .from("refresh_token", "")
                .path("/")
                .httpOnly(true)
                .secure(jwtProperties.cookie().secure())
                .maxAge(0)  // 즉시 만료
                .sameSite("Lax")
                .build();

        response.addHeader("Set-Cookie", cookie.toString());
    }
}
```

---

## 4. OAuth2AuthenticationFailureHandler 구현

### 에러 분류 전략

```java
package com.example.oauth2.handler;

import com.example.global.properties.Oauth2Properties;
import com.example.oauth2.repository.HttpCookieOAuth2AuthorizationRequestRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationFailureHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;

@Component
@RequiredArgsConstructor
@Slf4j
public class OAuth2AuthenticationFailureHandler
        extends SimpleUrlAuthenticationFailureHandler {

    /**
     * OAuth2 에러 코드 → 사용자 친화적 에러 정보 매핑
     */
    private static final Map<String, ErrorInfo> ERROR_MAPPINGS = Map.of(
            // 사용자 취소
            "access_denied",
            new ErrorInfo("USER_CANCELLED", "로그인이 취소되었습니다", false),

            // 토큰 오류
            "invalid_token",
            new ErrorInfo("INVALID_TOKEN", "인증 토큰이 유효하지 않습니다", true),

            // Provider 서버 오류
            "server_error",
            new ErrorInfo("PROVIDER_ERROR", "소셜 로그인 서비스에 문제가 발생했습니다", true),

            // 권한 오류
            "insufficient_scope",
            new ErrorInfo("INSUFFICIENT_SCOPE", "필요한 권한이 부족합니다", true),

            // 네트워크 오류
            "temporarily_unavailable",
            new ErrorInfo("TEMPORARILY_UNAVAILABLE", "일시적으로 서비스를 이용할 수 없습니다", true)
    );

    private static final ErrorInfo DEFAULT_ERROR =
            new ErrorInfo("OAUTH2_ERROR", "소셜 로그인 중 오류가 발생했습니다", true);

    private final HttpCookieOAuth2AuthorizationRequestRepository cookieRepository;
    private final Oauth2Properties oauth2Properties;

    @Override
    public void onAuthenticationFailure(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException exception
    ) throws IOException {

        // 1. 모든 OAuth2 쿠키 정리
        cookieRepository.clearAllCookies(response);

        // 2. 에러 분류
        ErrorInfo errorInfo = resolveError(exception);

        // 3. 로깅 (심각도별)
        if (errorInfo.shouldAlert()) {
            // 시스템 오류: 개발팀 알림 필요
            log.error("OAuth2 authentication failed - code: {}, message: {}",
                    errorInfo.code(), exception.getMessage(), exception);
        } else {
            // 사용자 행동 (취소 등): 정보 로깅만
            log.info("OAuth2 authentication cancelled by user");
        }

        // 4. 프론트엔드로 에러 리다이렉트
        String targetUrl = UriComponentsBuilder
                .fromUriString(oauth2Properties.authorizedRedirectUri())
                .queryParam("error", errorInfo.code())
                .queryParam("message", errorInfo.message())
                .encode(StandardCharsets.UTF_8)
                .build()
                .toUriString();

        getRedirectStrategy().sendRedirect(request, response, targetUrl);
    }

    /**
     * 예외에서 에러 정보 추출
     */
    private ErrorInfo resolveError(AuthenticationException exception) {
        if (exception instanceof OAuth2AuthenticationException oauth2Ex) {
            String errorCode = oauth2Ex.getError().getErrorCode();
            return ERROR_MAPPINGS.getOrDefault(errorCode, DEFAULT_ERROR);
        }
        return DEFAULT_ERROR;
    }

    /**
     * 에러 정보 레코드
     * @param code 프론트엔드용 에러 코드
     * @param message 사용자용 메시지
     * @param shouldAlert 개발팀 알림 필요 여부
     */
    private record ErrorInfo(
            String code,
            String message,
            boolean shouldAlert
    ) {

    }
}
```

### 에러 분류 기준

| OAuth2 에러 코드 | 내부 코드 | 사용자 메시지 | 알림 필요 |
| --- | --- | --- | --- |
| `access_denied` | `USER_CANCELLED` | 로그인이 취소되었습니다 | ❌ |
| `invalid_token` | `INVALID_TOKEN` | 인증 토큰이 유효하지 않습니다 | ✅ |
| `server_error` | `PROVIDER_ERROR` | 소셜 로그인 서비스에 문제가 발생했습니다 | ✅ |
| `insufficient_scope` | `INSUFFICIENT_SCOPE` | 필요한 권한이 부족합니다 | ✅ |

### 프론트엔드 에러 처리

```jsx
// /oauth2/callback 페이지
function OAuth2Callback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        const error = searchParams.get('error');
        const message = searchParams.get('message');

        if (error) {
            switch (error) {
                case 'USER_CANCELLED':
                    // 사용자 취소: 조용히 로그인 페이지로
                    navigate('/login');
                    break;

                case 'INVALID_TOKEN':
                case 'PROVIDER_ERROR':
                    // 시스템 오류: 에러 메시지 표시
                    alert(message || '로그인 중 오류가 발생했습니다.');
                    navigate('/login');
                    break;

                default:
                    alert(message || '알 수 없는 오류가 발생했습니다.');
                    navigate('/login');
            }
            return;
        }

        // 성공 처리...
    }, [searchParams, navigate]);

    return <div>로그인 처리 중...</div>;
}
```

---

## 5. Security Configuration에 핸들러 등록

```java
package com.example.global.config;

import com.example.oauth2.handler.OAuth2AuthenticationFailureHandler;
import com.example.oauth2.handler.OAuth2AuthenticationSuccessHandler;
import com.example.oauth2.repository.HttpCookieOAuth2AuthorizationRequestRepository;
import com.example.oauth2.service.CustomOAuth2UserService;
import com.example.oauth2.service.CustomOidcUserService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final CustomOAuth2UserService customOAuth2UserService;
    private final CustomOidcUserService customOidcUserService;
    private final OAuth2AuthenticationSuccessHandler successHandler;
    private final OAuth2AuthenticationFailureHandler failureHandler;
    private final HttpCookieOAuth2AuthorizationRequestRepository cookieRepository;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // ... 기타 설정

                .oauth2Login(oauth2 -> oauth2
                        // 쿠키 기반 AuthorizationRequest 저장소
                        .authorizationEndpoint(authorization -> authorization
                                .authorizationRequestRepository(cookieRepository)
                        )

                        // 커스텀 UserService
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService)
                                .oidcUserService(customOidcUserService)
                        )

                        // 커스텀 핸들러
                        .successHandler(successHandler)
                        .failureHandler(failureHandler)
                );

        return http.build();
    }
}
```

---

## 마치며

OAuth2 인증 핸들러를 구현하여 다음을 달성했습니다:

1. **JWT 발급**: OAuth2 인증 성공 후 자체 JWT 토큰 발급
2. **회원 매핑**: 기존 회원 연동 또는 새 회원 생성
3. **보안 쿠키**: Refresh Token을 HttpOnly 쿠키에 안전하게 저장
4. **에러 분류**: 사용자 행동 vs 시스템 오류 구분
5. **프론트엔드 친화적**: 에러 코드와 메시지를 URL 파라미터로 전달

### 전체 아키텍처 요약

![](https://velog.velcdn.com/images/co-vol/post/afac8893-045e-4764-9a9b-aa97968d3946/image.png)

### 시리즈 정리

이 시리즈에서 구현한 내용:

| 시리즈 | 주제 | 핵심 패턴/기술 |
| --- | --- | --- |
| 1 | OAuth2 기초 | OAuth2 vs OIDC, Spring Security 설정 |
| 2 | Strategy Pattern | Provider별 로직 캡슐화 |
| 3 | Factory Pattern | Provider별 UserInfo 추출기 관리 |
| 4 | 쿠키 인증 | Stateless 상태 관리, CSRF 방어 |
| 5 | 핸들러 | JWT 발급, 에러 처리 전략 |

---

## 참고 자료

- [Spring Security OAuth2 공식 문서](https://docs.spring.io/spring-security/reference/servlet/oauth2/index.html)
- [카카오 로그인 개발 가이드](https://developers.kakao.com/docs/latest/ko/kakaologin/common)
- [JWT.io](https://jwt.io/) - JWT 디버깅 도구
- [OWASP 세션 관리 치트시트](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

---

---

원문: [velog · 2026-01-14](https://velog.io/@co-vol/Spring-OAuth2-SuccessFailure-Handler-JWT-%EB%B0%9C%EA%B8%89%EA%B3%BC-%EC%97%90%EB%9F%AC-%EC%B2%98%EB%A6%AC-%EC%A0%84%EB%9E%B5)
