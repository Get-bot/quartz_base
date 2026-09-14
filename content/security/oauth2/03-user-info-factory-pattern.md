---
title: "Spring OAuth2 사용자 정보 통합 - Factory Pattern으로 Provider별 응답 파싱하기"
date: 2026-01-12
tags: ["spring-boot", "spring-security", "oauth2", "social-login", "design-pattern", "factory-pattern"]
description: "Provider별 중첩 JSON을 통합 DTO로 변환하는 Extractor를 Factory Pattern으로 관리. OIDC/OAuth2 모드 분기 포함. 시리즈 3편."
source: https://velog.io/@co-vol/Spring-OAuth2-%EC%82%AC%EC%9A%A9%EC%9E%90-%EC%A0%95%EB%B3%B4-%ED%86%B5%ED%95%A9-Factory-Pattern%EC%9C%BC%EB%A1%9C-Provider%EB%B3%84-%EC%9D%91%EB%8B%B5-%ED%8C%8C%EC%8B%B1%ED%95%98%EA%B8%B0
---

> 카카오, 네이버, 구글은 각각 다른 JSON 응답 구조를 가집니다. Factory Pattern을 활용하여 Provider별 응답을 통합된 DTO로 변환하는 시스템을 구축합니다.

## 들어가며

[[02-multi-provider-strategy-pattern|이전 글]]에서 Strategy Pattern으로 Provider별 로직을 캡슐화했습니다. 이번에는 각 Provider의 **서로 다른 응답 구조**를 어떻게 통합하는지 다룹니다.

### 문제: Provider마다 다른 응답 구조

```json
// 카카오 응답 - 중첩 구조
{
  "id": 123456789,
  "kakao_account": {
    "email": "user@kakao.com",
    "profile": {
      "nickname": "홍길동",
      "profile_image_url": "https://..."
    }
  }
}

// 네이버 응답 - response 래퍼
{
  "resultcode": "00",
  "message": "success",
  "response": {
    "id": "abcd1234",
    "email": "user@naver.com",
    "nickname": "홍길동"
  }
}

// 구글 응답 - 플랫 구조
{
  "sub": "1234567890",
  "email": "user@gmail.com",
  "name": "홍길동",
  "picture": "https://..."
}
```

이 세 가지를 하나의 통합된 형태로 변환해야 합니다:

```java
OAuth2UserInfo {
    providerId: "123456789"
    provider: KAKAO
    email: "user@kakao.com"
    nickname: "홍길동"
    profileImageUrl: "https://..."
}
```

---

## 1. OAuth2UserInfo: 통합 DTO 설계

모든 Provider의 사용자 정보를 담는 통합 DTO를 정의합니다.

```java
package com.example.oauth2.client.core.dto;

import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import lombok.Builder;
import org.springframework.util.StringUtils;
import java.util.Map;
import java.util.regex.Pattern;

@Builder
public record OAuth2UserInfo(
    String providerId,           // Provider 내 고유 ID
    OAuth2ProviderType provider, // Provider 타입
    String email,
    String name,                 // 실명 (비즈앱 전용)
    String nickname,
    String phoneNumber,
    String profileImageUrl,
    Map<String, Object> attributes  // 원본 응답 전체
) {
    // 한국 국가코드 패턴
    private static final Pattern KOREA_CODE = Pattern.compile("^82");
    private static final Pattern NON_DIGIT = Pattern.compile("\\\\D");

    /**
     * 표시 이름을 반환합니다.
     * 우선순위: nickname → name → email 로컬파트 → username
     */
    public String getDisplayName() {
        if (StringUtils.hasText(nickname)) {
            return nickname;
        }
        if (StringUtils.hasText(name)) {
            return name;
        }
        if (StringUtils.hasText(email) && email.contains("@")) {
            return email.substring(0, email.indexOf('@'));
        }
        return getUsername();
    }

    /**
     * 시스템 내 고유 username을 반환합니다.
     * 형식: "PROVIDER_providerId" (예: "KAKAO_123456")
     */
    public String getUsername() {
        return provider.name() + "_" + providerId;
    }

    /**
     * 전화번호를 정규화합니다.
     * - 숫자만 추출
     * - 한국 국가코드(82) → 0으로 변환
     * 예: "+82 10-1234-5678" → "01012345678"
     */
    public String getNormalizedPhoneNumber() {
        if (!StringUtils.hasText(phoneNumber)) {
            return null;
        }

        String digitsOnly = NON_DIGIT.matcher(phoneNumber).replaceAll("");
        if (digitsOnly.isEmpty()) {
            return null;
        }

        return KOREA_CODE.matcher(digitsOnly).replaceFirst("0");
    }
}
```

### 설계 포인트

| 필드 | 설명 |
| --- | --- |
| `providerId` | Provider 내 고유 ID (카카오 id, 네이버 id 등) |
| `provider` | Provider 타입 열거형 |
| `attributes` | 원본 응답 전체 (디버깅/확장용) |
| `getUsername()` | 시스템 내 고유 식별자 생성 |
| `getNormalizedPhoneNumber()` | 전화번호 정규화 |

---

## 2. OAuth2UserInfoExtractor 인터페이스

Provider별 추출 로직을 추상화하는 인터페이스입니다.

```java
package com.example.oauth2.client.core.userinfo;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;

public interface OAuth2UserInfoExtractor {

    /**
     * 이 Extractor가 담당하는 Provider 타입
     */
    OAuth2ProviderType getProviderType();

    /**
     * OIDC 모드: ID Token + UserInfo에서 추출
     */
    OAuth2UserInfo extract(OidcUser oidcUser);

    /**
     * OAuth2 모드: UserInfo Endpoint 응답에서만 추출
     */
    OAuth2UserInfo extract(OAuth2User oauth2User);

    /**
     * 지원 여부 확인
     */
    default boolean supports(String registrationId) {
        return getProviderType().getRegistrationId().equals(registrationId);
    }
}
```

### OIDC vs OAuth2 모드

- **OIDC 모드**: ID Token claims와 UserInfo를 조합 (더 신뢰성 높음)
- **OAuth2 모드**: UserInfo Endpoint 응답만 사용 (네이버 등 OIDC 미지원 Provider용)

---

## 3. OAuth2Attributes: 중첩 Map 탐색 유틸리티

OAuth2 응답은 대부분 중첩된 Map 구조입니다. 이를 쉽게 탐색하는 유틸리티를 만듭니다.

```java
package com.example.oauth2.client.core.userinfo;

import lombok.extern.slf4j.Slf4j;
import org.springframework.util.StringUtils;
import java.util.Collections;
import java.util.Map;
import java.util.function.Function;

@Slf4j
public record OAuth2Attributes(Map<String, Object> attributes) {

    public OAuth2Attributes(Map<String, Object> attributes) {
        this.attributes = attributes != null ? attributes : Collections.emptyMap();
    }

    // ==================== Factory Methods ====================

    public static OAuth2Attributes of(Map<String, Object> attributes) {
        return new OAuth2Attributes(attributes);
    }

    public static OAuth2Attributes empty() {
        return new OAuth2Attributes(Collections.emptyMap());
    }

    // ==================== Navigation ====================

    /**
     * 중첩된 Map을 OAuth2Attributes로 래핑하여 반환
     * 존재하지 않으면 빈 OAuth2Attributes 반환
     *
     * 예: getChild("kakao_account").getChild("profile")
     */
    public OAuth2Attributes getChild(String key) {
        return new OAuth2Attributes(getMapInternal(key));
    }

    /**
     * 점(.) 표기법으로 깊은 탐색
     *
     * 예: getPath("kakao_account.profile.nickname")
     */
    public OAuth2Attributes getPath(String path) {
        if (!StringUtils.hasText(path)) {
            return this;
        }

        OAuth2Attributes current = this;
        for (String key : path.split("\\\\.")) {
            current = current.getChild(key);
            if (current.isEmpty()) {
                return OAuth2Attributes.empty();
            }
        }
        return current;
    }

    // ==================== Primitive Getters ====================

    public String getString(String key) {
        Object value = attributes.get(key);
        return value != null ? String.valueOf(value) : null;
    }

    public Long getLong(String key) {
        Object value = attributes.get(key);
        return switch (value) {
            case null -> null;
            case Long l -> l;
            case Number n -> n.longValue();
            default -> parseLongSafely(String.valueOf(value));
        };
    }

    public Boolean getBoolean(String key) {
        Object value = attributes.get(key);
        return switch (value) {
            case null -> null;
            case Boolean b -> b;
            default -> Boolean.parseBoolean(String.valueOf(value));
        };
    }

    // ==================== Custom Mapping ====================

    /**
     * 값을 커스텀 함수로 변환
     */
    public <T> T map(String key, Function<String, T> mapper) {
        String value = getString(key);
        if (!StringUtils.hasText(value)) {
            return null;
        }

        try {
            return mapper.apply(value);
        } catch (Exception e) {
            log.debug("Failed to map value '{}' for key '{}'", value, key);
            return null;
        }
    }

    // ==================== Utility ====================

    public boolean has(String key) {
        return attributes.containsKey(key) && attributes.get(key) != null;
    }

    public boolean isEmpty() {
        return attributes.isEmpty();
    }

    // ==================== Internal ====================

    @SuppressWarnings("unchecked")
    private Map<String, Object> getMapInternal(String key) {
        Object value = attributes.get(key);
        if (value instanceof Map) {
            return (Map<String, Object>) value;
        }
        return Collections.emptyMap();
    }

    private Long parseLongSafely(String value) {
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            log.debug("Failed to parse Long: '{}'", value);
            return null;
        }
    }
}
```

### 사용 예시

```java
// Before: 전통적인 방식 (NullPointerException 위험!)
Map<String, Object> account = (Map<String, Object>) attributes.get("kakao_account");
Map<String, Object> profile = (Map<String, Object>) account.get("profile");
String nickname = (String) profile.get("nickname");

// After: OAuth2Attributes 사용 (안전하고 깔끔!)
OAuth2Attributes attrs = OAuth2Attributes.of(attributes);
String nickname = attrs.getChild("kakao_account")
                       .getChild("profile")
                       .getString("nickname");

// 또는 점 표기법으로 한 줄에
String nickname = attrs.getPath("kakao_account.profile.nickname")
                       .getString("nickname");
```

---

## 4. Factory Pattern으로 Extractor 관리

Spring DI를 활용하여 모든 Extractor를 자동으로 수집하고 관리합니다.

```java
package com.example.oauth2.client.core.userinfo;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Component
public class OAuth2UserInfoExtractorFactory {

    private final Map<OAuth2ProviderType, OAuth2UserInfoExtractor> extractorMap;

    /**
     * 생성자에서 모든 Extractor를 수집하여 Map으로 변환
     * Spring이 OAuth2UserInfoExtractor 구현체를 모두 주입
     */
    public OAuth2UserInfoExtractorFactory(List<OAuth2UserInfoExtractor> extractors) {
        this.extractorMap = extractors.stream()
                .collect(Collectors.toMap(
                        OAuth2UserInfoExtractor::getProviderType,
                        Function.identity()
                ));
    }

    /**
     * Provider 타입으로 Extractor 조회
     */
    public OAuth2UserInfoExtractor getExtractor(OAuth2ProviderType providerType) {
        OAuth2UserInfoExtractor extractor = extractorMap.get(providerType);
        if (extractor == null) {
            throw new IllegalArgumentException(
                "No extractor found for: " + providerType
            );
        }
        return extractor;
    }

    /**
     * registrationId로 Extractor 조회
     */
    public OAuth2UserInfoExtractor getExtractor(String registrationId) {
        return getExtractor(OAuth2ProviderType.from(registrationId));
    }

    /**
     * OAuth2User에서 UserInfo 추출 (OIDC/OAuth2 자동 감지)
     */
    public OAuth2UserInfo extract(String registrationId, OAuth2User oauth2User) {
        OAuth2UserInfoExtractor extractor = getExtractor(registrationId);

        // OIDC User인 경우 OIDC 모드로 추출
        if (oauth2User instanceof OidcUser oidcUser) {
            return extractor.extract(oidcUser);
        }

        // 일반 OAuth2 User인 경우
        return extractor.extract(oauth2User);
    }
}
```

### Factory Pattern의 장점

![](https://velog.velcdn.com/images/co-vol/post/dc6d996a-9b7b-4bb4-8cbe-edcff0b8e59d/image.png)

1. **자동 수집**: `@Component` 붙은 Extractor가 자동으로 등록됨
2. **느슨한 결합**: Factory는 구체 클래스를 모름
3. **확장 용이**: 새 Extractor 추가해도 Factory 수정 불필요

---

## 5. Provider별 Extractor 구현

### KakaoUserInfoExtractor

```java
package com.example.oauth2.client.kakao;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import com.example.oauth2.client.core.userinfo.OAuth2Attributes;
import com.example.oauth2.client.core.userinfo.OAuth2UserInfoExtractor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.Map;

import static org.apache.commons.lang3.ObjectUtils.firstNonNull;

@Component
@Slf4j
public class KakaoUserInfoExtractor implements OAuth2UserInfoExtractor {

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.KAKAO;
    }

    /**
     * OIDC 모드: ID Token claims + attributes 조합
     */
    @Override
    public OAuth2UserInfo extract(OidcUser oidcUser) {
        OidcIdToken idToken = oidcUser.getIdToken();
        Map<String, Object> attributes = oidcUser.getAttributes();
        KakaoUserDetail detail = parseKakaoResponse(attributes);

        return OAuth2UserInfo.builder()
                // ID Token의 sub가 더 신뢰성 있음
                .providerId(firstNonNull(idToken.getSubject(), detail.getProviderId()))
                .provider(OAuth2ProviderType.KAKAO)
                // ID Token claims 우선, 없으면 attributes에서
                .email(firstNonNull(idToken.getEmail(), detail.email()))
                .name(detail.name())
                .nickname(firstNonNull(idToken.getNickName(), detail.nickname()))
                .phoneNumber(detail.phoneNumber())
                .profileImageUrl(firstNonNull(idToken.getPicture(), detail.profileImageUrl()))
                .attributes(attributes)
                .build();
    }

    /**
     * OAuth2 모드: UserInfo Endpoint 응답만 사용
     */
    @Override
    public OAuth2UserInfo extract(OAuth2User oauth2User) {
        Map<String, Object> attributes = oauth2User.getAttributes();
        KakaoUserDetail detail = parseKakaoResponse(attributes);

        return OAuth2UserInfo.builder()
                .providerId(detail.getProviderId())
                .provider(OAuth2ProviderType.KAKAO)
                .email(detail.email())
                .name(detail.name())
                .nickname(detail.nickname())
                .phoneNumber(detail.phoneNumber())
                .profileImageUrl(detail.profileImageUrl())
                .attributes(attributes)
                .build();
    }

    /**
     * 카카오 응답 파싱
     */
    private KakaoUserDetail parseKakaoResponse(Map<String, Object> attributes) {
        OAuth2Attributes root = OAuth2Attributes.of(attributes);
        OAuth2Attributes account = root.getChild("kakao_account");
        OAuth2Attributes profile = account.getChild("profile");

        return KakaoUserDetail.builder()
                .id(root.getLong("id"))
                .nickname(profile.getString("nickname"))
                .profileImageUrl(profile.getString("profile_image_url"))
                .name(account.getString("name"))
                .email(account.getString("email"))
                .phoneNumber(account.getString("phone_number"))
                .build();
    }
}
```

### KakaoUserDetail (응답 DTO)

```java
package com.example.oauth2.client.kakao;

import lombok.Builder;

@Builder
public record KakaoUserDetail(
    Long id,
    String nickname,
    String profileImageUrl,
    String name,        // 실명 (비즈앱 전용)
    String email,
    String phoneNumber  // 비즈앱 전용
) {
    public String getProviderId() {
        return id != null ? String.valueOf(id) : null;
    }
}
```

### NaverUserInfoExtractor

```java
package com.example.oauth2.client.naver;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import com.example.oauth2.client.core.userinfo.OAuth2Attributes;
import com.example.oauth2.client.core.userinfo.OAuth2UserInfoExtractor;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.Map;

@Component
public class NaverUserInfoExtractor implements OAuth2UserInfoExtractor {

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.NAVER;
    }

    @Override
    public OAuth2UserInfo extract(OidcUser oidcUser) {
        // 네이버는 OIDC 미지원, OAuth2 모드로 폴백
        return extract((OAuth2User) oidcUser);
    }

    @Override
    public OAuth2UserInfo extract(OAuth2User oauth2User) {
        Map<String, Object> attributes = oauth2User.getAttributes();

        // 네이버 응답은 "response" 객체 안에 실제 데이터가 있음
        OAuth2Attributes response = OAuth2Attributes.of(attributes)
                .getChild("response");

        return OAuth2UserInfo.builder()
                .providerId(response.getString("id"))
                .provider(OAuth2ProviderType.NAVER)
                .email(response.getString("email"))
                .name(response.getString("name"))
                .nickname(response.getString("nickname"))
                .phoneNumber(response.getString("mobile"))
                .profileImageUrl(response.getString("profile_image"))
                .attributes(attributes)
                .build();
    }
}
```

### GoogleUserInfoExtractor

```java
package com.example.oauth2.client.google;

import com.example.oauth2.client.core.dto.OAuth2UserInfo;
import com.example.oauth2.client.core.provider.OAuth2ProviderType;
import com.example.oauth2.client.core.userinfo.OAuth2Attributes;
import com.example.oauth2.client.core.userinfo.OAuth2UserInfoExtractor;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Component;
import java.util.Map;

@Component
public class GoogleUserInfoExtractor implements OAuth2UserInfoExtractor {

    @Override
    public OAuth2ProviderType getProviderType() {
        return OAuth2ProviderType.GOOGLE;
    }

    @Override
    public OAuth2UserInfo extract(OidcUser oidcUser) {
        OidcIdToken idToken = oidcUser.getIdToken();

        return OAuth2UserInfo.builder()
                .providerId(idToken.getSubject())
                .provider(OAuth2ProviderType.GOOGLE)
                .email(idToken.getEmail())
                .name(idToken.getFullName())
                .nickname(idToken.getGivenName())
                .profileImageUrl(idToken.getPicture())
                .attributes(oidcUser.getAttributes())
                .build();
    }

    @Override
    public OAuth2UserInfo extract(OAuth2User oauth2User) {
        OAuth2Attributes attrs = OAuth2Attributes.of(oauth2User.getAttributes());

        return OAuth2UserInfo.builder()
                .providerId(attrs.getString("sub"))
                .provider(OAuth2ProviderType.GOOGLE)
                .email(attrs.getString("email"))
                .name(attrs.getString("name"))
                .nickname(attrs.getString("given_name"))
                .profileImageUrl(attrs.getString("picture"))
                .attributes(oauth2User.getAttributes())
                .build();
    }
}
```

---

## 마치며

Factory Pattern을 적용하여 다음을 달성했습니다:

1. **통합 DTO**: 모든 Provider의 응답을 `OAuth2UserInfo`로 통합
2. **안전한 파싱**: `OAuth2Attributes`로 NullPointerException 방지
3. **자동 확장**: Spring DI로 새 Extractor 자동 등록
4. **OIDC/OAuth2 자동 감지**: Factory가 적절한 추출 모드 선택

### 아키텍처 요약
![](https://velog.velcdn.com/images/co-vol/post/a56ad468-583d-4537-84af-1f53b90bcb10/image.png)

---

원문: [velog · 2026-01-12](https://velog.io/@co-vol/Spring-OAuth2-%EC%82%AC%EC%9A%A9%EC%9E%90-%EC%A0%95%EB%B3%B4-%ED%86%B5%ED%95%A9-Factory-Pattern%EC%9C%BC%EB%A1%9C-Provider%EB%B3%84-%EC%9D%91%EB%8B%B5-%ED%8C%8C%EC%8B%B1%ED%95%98%EA%B8%B0)
