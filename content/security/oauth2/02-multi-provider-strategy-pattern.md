---
title: "Spring OAuth2 멀티 Provider 지원 - Strategy Pattern으로 카카오, 네이버, 구글 통합"
date: 2026-01-08
tags: ["spring-boot", "spring-security", "oauth2", "social-login", "design-pattern", "strategy-pattern"]
description: "카카오·네이버·구글의 서로 다른 응답 구조를 Strategy Pattern으로 캡슐화. 새 Provider는 클래스 추가만으로 확장되는 구조. 시리즈 2편."
source: https://velog.io/@co-vol/Spring-OAuth2-%EB%A9%80%ED%8B%B0-Provider-%EC%A7%80%EC%9B%90-Strategy-Pattern%EC%9C%BC%EB%A1%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4-%EB%84%A4%EC%9D%B4%EB%B2%84-%EA%B5%AC%EA%B8%80-%ED%86%B5%ED%95%A9
---

> 카카오, 네이버, 구글 소셜 로그인을 하나의 아키텍처로 통합합니다. Strategy Pattern을 활용하여 새로운 Provider를 추가할 때 기존 코드 수정 없이 확장할 수 있는 구조를 설계합니다.

## 들어가며

[[01-kakao-login-oidc|이전 글]]에서 카카오 OAuth2 로그인의 기초를 다뤘습니다. 하지만 실제 서비스에서는 네이버, 구글, 애플 등 여러 소셜 로그인을 지원해야 합니다.

문제는 각 Provider마다 **응답 구조가 다르다**는 것입니다:

```java
// 카카오 응답
{
  "id":123456789,
  "kakao_account":{
	  "email":"user@kakao.com",
	  "profile":{"nickname":"홍길동"}
  }
}

// 네이버 응답
{
	"response":{
		"id":"abcd1234",
		"email":"user@naver.com",
		"nickname":"홍길동"
	}
}

// 구글 응답
{
	"sub":"1234567890",
	"email":"user@gmail.com",
	"name":"홍길동"
}
```

이런 상황에서 `if-else` 분기문으로 처리하면 어떻게 될까요?

```java
// 안티패턴: if-else 지옥
if(provider.equals("kakao")){
// 카카오 파싱 로직
}else if(provider.equals("naver")){
// 네이버 파싱 로직
}else if(provider.equals("google")){
// 구글 파싱 로직
}else if(provider.equals("apple")){
// ... 끝없이 증가
}
```

새 Provider가 추가될 때마다 기존 코드를 수정해야 하고, 한 파일이 비대해집니다. **OCP(Open-Closed Principle)** 를 위반하는 대표적인 사례입니다.

이 글에서는 **Strategy Pattern**을 활용하여 이 문제를 해결합니다.

---

## 1. 왜 Strategy Pattern인가?

### Strategy Pattern이란?

Strategy Pattern은 **행위(알고리즘)를 캡슐화**하여 런타임에 교체할 수 있게 하는 디자인 패턴입니다.

![](https://velog.velcdn.com/images/co-vol/post/69112eb6-cb90-4c34-a1a1-7bd522124639/image.png)

### 적용 시 장점

| 장점 | 설명 |
| --- | --- |
| **OCP 준수** | 새 Provider 추가 시 기존 코드 수정 불필요 |
| **단일 책임** | 각 Strategy가 하나의 Provider만 담당 |
| **테스트 용이** | Provider별 독립적인 단위 테스트 가능 |
| **런타임 교체** | 동적으로 Strategy 선택 가능 |

---

## 2. OAuth2ProviderType 열거형 설계

먼저 지원하는 Provider를 열거형으로 정의합니다.

```java
package com.example.oauth2.client.core.provider;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import java.util.Arrays;

@Getter
@RequiredArgsConstructor
public enum OAuth2ProviderType {
    KAKAO("kakao", true, "<https://kauth.kakao.com>"),
    NAVER("naver", false, null),
    GOOGLE("google", true, "<https://accounts.google.com>");

    private final String registrationId;  // application.yml의 registration 이름
    private final boolean oidcSupported;  // OIDC 지원 여부
    private final String issuerUri;       // OIDC issuer URI

    /**
     * registrationId로 Provider 타입을 찾습니다.
     */
    public static OAuth2ProviderType from(String registrationId) {
        return Arrays.stream(values())
                .filter(type -> type.registrationId.equals(registrationId))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException(
                        "Unsupported provider: " + registrationId
                ));
    }
}
```

### 설계 포인트

1. **oidcSupported**: OIDC 지원 여부를 명시합니다. 카카오/구글은 OIDC를 지원하지만, 네이버는 OAuth2만 지원한다고 가정합니다.
2. **issuerUri**: OIDC ID Token의 issuer 검증에 사용합니다.
3. **from() 메서드**: Spring Security의 registrationId로 열거형을 찾습니다.

---

## 3. OAuth2ProviderStrategy 인터페이스

Provider별 로직을 추상화하는 Strategy 인터페이스를 정의합니다.

```java
package com.example.oauth2.client.core.provider;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.user.OAuth2User;
import java.util.Set;

public interface OAuth2ProviderStrategy {

    /**
     * 이 Strategy가 담당하는 Provider 타입
     */
    OAuth2ProviderType getProviderType();

    /**
     * OAuth2User에서 사용자 정보를 추출합니다.
     * @param oauth2User OAuth2/OIDC 인증된 사용자
     * @param idToken OIDC ID Token (OIDC 모드일 때만 non-null)
     * @return 정규화된 사용자 정보
     */
    OAuth2UserInfo extractUserInfo(OAuth2User oauth2User, OidcIdToken idToken);

    /**
     * ID Token 검증 (OIDC Provider만 구현)
     * 기본 구현은 아무것도 하지 않음
     */
    default void validateToken(OidcIdToken idToken) {
        // 기본값: 검증 없음 (OAuth2 전용 Provider용)
    }

    /**
     * 이 Provider에 필요한 scope 목록
     */
    Set<String> getRequiredScopes();
}
```

### 인터페이스 설계 원칙

1. **최소 인터페이스**: 모든 Provider가 구현해야 할 최소한의 메서드만 정의
2. **기본 구현 제공**: `validateToken()`은 OIDC Provider만 필요하므로 기본 구현 제공
3. **타입 안전성**: `OAuth2ProviderType`으로 Provider를 식별

---

## 4. Provider별 구체 클래스 구현

### KakaoOAuth2Strategy (OIDC 지원)

```java
package com.example.oauth2.client.kakao;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderStrategy;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.autoconfigure.security.oauth2.client.OAuth2ClientProperties;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.Set;

@Component
@RequiredArgsConstructor
public class KakaoOAuth2Strategy implements OAuth2ProviderStrategy {

    private final KakaoUserInfoExtractor userInfoExtractor;
    private final OAuth2ClientProperties oauth2Properties;

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.KAKAO;
    }

    @Override
    public OAuth2UserInfo extractUserInfo(OAuth2User oauth2User, OidcIdToken idToken) {
        // OIDC 모드 (ID Token이 있는 경우)
        if (idToken != null && oauth2User instanceof OidcUser oidcUser) {
            return userInfoExtractor.extract(oidcUser);
        }
        // OAuth2 모드 (fallback)
        return userInfoExtractor.extract(oauth2User);
    }

    @Override
    public void validateToken(OidcIdToken idToken) {
        if (idToken == null) return;

        // 1. Issuer 검증
        String issuer = idToken.getIssuer().toString();
        String expectedIssuer = oauth2Properties.getProvider()
                .get("kakao").getIssuerUri();

        if (!issuer.equals(expectedIssuer)) {
            throw new OAuth2AuthenticationException(
                    new OAuth2Error("invalid_token",
                            "Invalid Kakao issuer: " + issuer, null)
            );
        }

        // 2. Audience 검증 (client_id와 일치해야 함)
        String clientId = oauth2Properties.getRegistration()
                .get("kakao").getClientId();

        if (!idToken.getAudience().contains(clientId)) {
            throw new OAuth2AuthenticationException(
                    new OAuth2Error("invalid_token",
                            "Invalid Kakao audience", null)
            );
        }
    }

    @Override
    public Set<String> getRequiredScopes() {
        return Set.of(
                "openid",           // OIDC 필수
                "profile_nickname",
                "profile_image",
                "account_email",
                "phone_number"
        );
    }
}
```

### NaverOAuth2Strategy (OAuth2만 지원)

```java
package com.example.oauth2.client.naver;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderStrategy;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.Set;

@Component
@RequiredArgsConstructor
public class NaverOAuth2Strategy implements OAuth2ProviderStrategy {

    private final NaverUserInfoExtractor userInfoExtractor;

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.NAVER;
    }

    @Override
    public OAuth2UserInfo extractUserInfo(OAuth2User oauth2User, OidcIdToken idToken) {
        // 네이버는 OIDC 미지원, OAuth2 모드만 사용
        return userInfoExtractor.extract(oauth2User);
    }

    // validateToken()은 기본 구현 사용 (아무것도 안 함)

    @Override
    public Set<String> getRequiredScopes() {
        return Set.of("name", "email", "profile_image");
    }
}
```

### GoogleOAuth2Strategy (OIDC 지원)

```java
package com.example.oauth2.client.google;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderStrategy;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.Set;

@Component
@RequiredArgsConstructor
public class GoogleOAuth2Strategy implements OAuth2ProviderStrategy {

    private final GoogleUserInfoExtractor userInfoExtractor;

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.GOOGLE;
    }

    @Override
    public OAuth2UserInfo extractUserInfo(OAuth2User oauth2User, OidcIdToken idToken) {
        if (idToken != null && oauth2User instanceof OidcUser oidcUser) {
            return userInfoExtractor.extract(oidcUser);
        }
        return userInfoExtractor.extract(oauth2User);
    }

    @Override
    public Set<String> getRequiredScopes() {
        return Set.of("openid", "profile", "email");
    }
}
```

---

## 5. 새로운 Provider 추가하기 (확장 예제)

Apple 로그인을 추가한다고 가정해봅시다. 기존 코드를 **전혀 수정하지 않고** 다음 단계만 진행하면 됩니다.

### Step 1: OAuth2ProviderType에 열거값 추가

```java
public enum OAuth2ProviderType {
    KAKAO("kakao", true, "<https://kauth.kakao.com>"),
    NAVER("naver", false, null),
    GOOGLE("google", true, "<https://accounts.google.com>"),
    APPLE("apple", true, "<https://appleid.apple.com>");  // 추가!

    // ... 나머지 동일
}
```

### Step 2: AppleUserInfoExtractor 구현

```java

@Component
public class AppleUserInfoExtractor implements OAuth2UserInfoExtractor {

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.APPLE;
    }

    @Override
    public OAuth2UserInfo extract(OidcUser oidcUser) {
        OidcIdToken idToken = oidcUser.getIdToken();

        return OAuth2UserInfo.builder()
                .providerId(idToken.getSubject())
                .provider(OAuth2ProviderType.APPLE)
                .email(idToken.getEmail())
                .name(oidcUser.getAttribute("name"))
                .attributes(oidcUser.getAttributes())
                .build();
    }

    @Override
    public OAuth2UserInfo extract(OAuth2User oauth2User) {
        // Apple은 OIDC 전용
        throw new UnsupportedOperationException("Apple requires OIDC");
    }
}
```

### Step 3: AppleOAuth2Strategy 구현

```java

@Component
@RequiredArgsConstructor
public class AppleOAuth2Strategy implements OAuth2ProviderStrategy {

    private final AppleUserInfoExtractor userInfoExtractor;

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.APPLE;
    }

    @Override
    public OAuth2UserInfo extractUserInfo(OAuth2User oauth2User, OidcIdToken idToken) {
        if (!(oauth2User instanceof OidcUser oidcUser)) {
            throw new OAuth2AuthenticationException(
                    new OAuth2Error("invalid_request", "Apple requires OIDC", null)
            );
        }
        return userInfoExtractor.extract(oidcUser);
    }

    @Override
    public Set<String> getRequiredScopes() {
        return Set.of("openid", "name", "email");
    }
}
```

### Step 4: application.yml 설정

```yaml
spring:
    security:
        oauth2:
            client:
                registration:
                    apple:
                        client-id: ${APPLE_CLIENT_ID}
                        client-secret: ${APPLE_CLIENT_SECRET}
                        redirect-uri: "{baseUrl}/login/oauth2/code/{registrationId}"
                        authorization-grant-type: authorization_code
                        scope: openid, name, email
                provider:
                    apple:
                        issuer-uri: <https://appleid.apple.com>
                        authorization-uri: <https://appleid.apple.com/auth/authorize>
                        token-uri: <https://appleid.apple.com/auth/token>
```

**끝입니다!** 기존의 `OAuth2UserService`, `SuccessHandler` 등은 전혀 수정할 필요가 없습니다.

---

## 마치며

Strategy Pattern을 적용하여 다음을 달성했습니다:

1. **OCP 준수**: 새 Provider 추가 시 기존 코드 수정 불필요
2. **단일 책임**: 각 Strategy가 하나의 Provider만 담당
3. **테스트 용이**: Provider별 독립적인 단위 테스트 가능
4. **확장성**: Apple, Facebook 등 새 Provider를 쉽게 추가

### 핵심 정리
![](https://velog.velcdn.com/images/co-vol/post/a0676b90-0072-4243-8f4b-a411ff6cabc2/image.png)

---

---

원문: [velog · 2026-01-08](https://velog.io/@co-vol/Spring-OAuth2-%EB%A9%80%ED%8B%B0-Provider-%EC%A7%80%EC%9B%90-Strategy-Pattern%EC%9C%BC%EB%A1%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4-%EB%84%A4%EC%9D%B4%EB%B2%84-%EA%B5%AC%EA%B8%80-%ED%86%B5%ED%95%A9)
