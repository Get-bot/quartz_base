---
title: "Spring Boot 3 OAuth2 소셜 로그인 가이드 - 카카오 로그인 구현"
date: 2026-01-07
tags: ["spring-boot", "spring-security", "oauth2", "oidc", "social-login", "kakao"]
description: "OAuth2와 OIDC의 차이, 왜 OIDC를 고르는지, Spring Security 6 설정과 카카오 개발자센터 세팅, Authorization Code 플로우까지. 시리즈 1편."
source: https://velog.io/@co-vol/Spring-Boot-3-OAuth2-%EC%86%8C%EC%85%9C-%EB%A1%9C%EA%B7%B8%EC%9D%B8-%EA%B0%80%EC%9D%B4%EB%93%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4-%EB%A1%9C%EA%B7%B8%EC%9D%B8-%EA%B5%AC%ED%98%84
---

> Spring Boot 3와 Spring Security 6를 활용한 카카오 OAuth2 소셜 로그인 구현 방법을 단계별로 알아봅니다. OAuth2와 OIDC의 차이점부터 실제 구현까지 다룹니다.

## 들어가며

최근 대부분의 서비스에서 소셜 로그인은 필수가 되었습니다. 사용자는 복잡한 회원가입 과정 없이 카카오, 네이버, 구글 계정으로 간편하게 로그인할 수 있고, 서비스 제공자는 인증 보안을 OAuth2 Provider에게 위임할 수 있습니다.

이 글에서는 **Spring Boot 3**와 **Spring Security 6**를 사용하여 카카오 소셜 로그인을 구현하는 방법을 다룹니다. 특히 OAuth2와 OIDC의 차이점, 그리고 왜 OIDC를 선택해야 하는지까지 설명합니다.

---

## 1. OAuth2와 OIDC의 차이점 이해하기

### OAuth2란?

**OAuth2**(Open Authorization 2.0)는 **권한 부여(Authorization)** 프로토콜입니다. 사용자가 자신의 리소스(프로필, 이메일 등)에 대한 접근 권한을 제3자 애플리케이션에 부여할 수 있게 해줍니다.

```json
[사용자] → [우리 서비스] → [카카오]
          "카카오 프로필 정보 좀 볼게요"
                    ↓
          [카카오가 Access Token 발급]
                    ↓
          [Access Token으로 UserInfo API 호출]
```

### OIDC란?

**OIDC**(OpenID Connect)는 OAuth2 위에 구축된 **인증(Authentication)** 레이어입니다. OAuth2가 "이 사용자가 권한을 부여했다"만 알려준다면, OIDC는 "이 사용자가 누구인지"까지 표준화된 방식으로 알려줍니다.

```json
[사용자] → [우리 서비스] → [카카오]
          "카카오로 로그인할게요"
                    ↓
          [카카오가 ID Token + Access Token 발급]
                    ↓
          [ID Token에서 바로 사용자 정보 추출]
```

### 핵심 차이점

| 구분         | OAuth2                | OIDC                           |
|------------|-----------------------|--------------------------------|
| **목적**     | 권한 부여 (Authorization) | 인증 (Authentication)            |
| **토큰**     | Access Token만 발급      | ID Token + Access Token        |
| **사용자 정보** | UserInfo API 별도 호출 필요 | ID Token에 포함                   |
| **표준화**    | 사용자 정보 포맷 비표준         | 표준화된 Claims (sub, email, name) |
| **보안**     | 토큰 검증 어려움             | JWT 서명 검증 가능                   |

### 왜 OIDC를 선택해야 할까?

1. **API 호출 감소**: ID Token에서 바로 사용자 정보를 가져올 수 있어 UserInfo API 호출이 줄어듭니다.
2. **보안 강화**: ID Token은 JWT이므로 서명 검증으로 위변조를 방지할 수 있습니다.
3. **표준화된 Claims**: `sub`, `email`, `name` 등 표준화된 필드로 Provider 간 일관성을 유지합니다.

> **Tip**: 카카오는 OIDC를 지원하므로, 반드시 `openid` scope를 추가하여 ID Token을 받아야 합니다.

---

## 2. Spring Security OAuth2 Client 의존성 설정

### build.gradle

```gradle
dependencies {
    // Spring Boot 3.x
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-security'

    // OAuth2 Client (필수)
    implementation 'org.springframework.boot:spring-boot-starter-oauth2-client'

    // OAuth2 Resource Server (JWT 검증용, 선택)
    implementation 'org.springframework.boot:spring-boot-starter-oauth2-resource-server'
}
```

### 의존성 설명

- **spring-boot-starter-oauth2-client**: OAuth2/OIDC 클라이언트 기능을 제공합니다. 카카오, 네이버, 구글 등의 Provider와 통신합니다.
- **spring-boot-starter-oauth2-resource-server**: JWT 토큰 검증 기능을 제공합니다. 자체 JWT를 발급하는 경우 필요합니다.

---

## 3. application.yml Provider 설정

### 카카오 OIDC 설정

```yaml
spring:
    security:
        oauth2:
            client:
                registration:
                    kakao:
                        client-id: ${KAKAO_CLIENT_ID}  # 카카오 REST API 키
                        client-secret: ${KAKAO_CLIENT_SECRET}  # 보안 → Client Secret
                        redirect-uri: "{baseUrl}/login/oauth2/code/{registrationId}"
                        authorization-grant-type: authorization_code
                        client-authentication-method: client_secret_post
                        scope:
                            - openid          # OIDC 필수!
                            - profile_nickname
                            - profile_image
                            - account_email
                            - phone_number
                        client-name: Kakao
                provider:
                    kakao:
                        issuer-uri: https://kauth.kakao.com
                        authorization-uri: https://kauth.kakao.com/oauth/authorize
                        token-uri: https://kauth.kakao.com/oauth/token
                        user-info-uri: https://kapi.kakao.com/v2/user/me
                        user-name-attribute: id
```

### 설정 항목 설명

| 항목                    | 설명                          |
|-----------------------|-----------------------------|
| `client-id`           | 카카오 개발자센터의 REST API 키       |
| `client-secret`       | 카카오 보안 설정의 Client Secret 코드 |
| `redirect-uri`        | 인증 후 콜백 URL (Spring 기본값 사용) |
| `scope`               | 요청할 권한 범위 (`openid` 필수!)    |
| `issuer-uri`          | OIDC Provider의 발급자 URI      |
| `user-name-attribute` | Principal name으로 사용할 속성     |

### Scope 종류

```yaml
scope:
    - openid            # OIDC ID Token 발급 (필수)
    - profile_nickname  # 닉네임
    - profile_image     # 프로필 이미지
    - account_email     # 이메일
    - phone_number      # 전화번호 (비즈앱 필요)
    - name              # 실명 (비즈앱 필요)
```

> **주의**: `phone_number`와 `name` scope는 카카오 비즈니스 앱에서만 사용 가능합니다.

---

## 4. 카카오 개발자센터 앱 설정

### Step 1: 애플리케이션 생성

1. [카카오 개발자센터](https://developers.kakao.com/)에 접속합니다.
2. **내 애플리케이션** → **애플리케이션 추가하기**를 클릭합니다.
3. 앱 이름과 사업자명을 입력합니다.

### Step 2: REST API 키 확인

**앱 설정** → **앱 키**에서 **REST API 키**를 복사합니다. 이것이 `client-id`입니다.

### Step 3: 보안 설정

**보안** 메뉴에서:

1. **Client Secret** 코드를 생성합니다.
2. **활성화 상태**를 ON으로 변경합니다.

### Step 4: 카카오 로그인 활성화

**카카오 로그인** 메뉴에서:

1. **활성화 설정**을 ON으로 변경합니다.
2. **OpenID Connect 활성화 설정**을 ON으로 변경합니다. (OIDC 사용 시 필수!)

### Step 5: Redirect URI 등록

**카카오 로그인** → **Redirect URI**에 다음을 등록합니다:

```
http://localhost:8080/login/oauth2/code/kakao
https://your-domain.com/login/oauth2/code/kakao
```

### Step 6: 동의항목 설정

**동의항목** 메뉴에서 필요한 정보의 동의 수준을 설정합니다:

| 항목          | 권장 설정  |
|-------------|--------|
| 닉네임         | 필수 동의  |
| 프로필 사진      | 선택 동의  |
| 카카오계정(이메일)  | 선택 동의  |
| 카카오계정(전화번호) | 비즈앱 전용 |

---

## 5. OAuth2 인증 플로우 이해하기

### Authorization Code Grant 플로우

![](https://velog.velcdn.com/images/co-vol/post/57ceab11-d270-4278-8810-7c619a11ebc5/image.png)

### Spring Security 기본 동작

Spring Security OAuth2 Client는 다음 엔드포인트를 자동으로 생성합니다:

| 엔드포인트                                    | 설명                                |
|------------------------------------------|-----------------------------------|
| `/oauth2/authorization/{registrationId}` | OAuth2 인증 시작                      |
| `/login/oauth2/code/{registrationId}`    | OAuth2 콜백 (Authorization Code 수신) |

### 실제 요청 URL 예시

```
# 1. 프론트엔드에서 로그인 버튼 클릭 시
GET /oauth2/authorization/kakao?redirect_uri=/mypage

# 2. 카카오 인증 후 콜백
GET /login/oauth2/code/kakao?code=xxx&state=yyy

# 3. 인증 성공 후 프론트엔드로 리다이렉트
GET /oauth2/callback?redirect_uri=/mypage
```

---

## 마치며

이번 글에서는 Spring Boot 3에서 카카오 OAuth2 소셜 로그인을 구현하기 위한 기초를 다뤘습니다. OAuth2와 OIDC의 차이점을 이해하고, 의존성 설정부터 카카오 개발자센터 설정까지 단계별로 진행했습니다.

### 핵심 정리
1. **가능하면 OIDC를 선택하세요**`openid` 스코프를 추가하면 ID Token을 통해 사용자 정보를 안전하고 빠르게 얻을 수 있습니다 (JWT 서명 지원).

2. **보안 설정은 꼼꼼하게**

  - **Client Secret:** 보안을 위해 활성화는 필수입니다. 특히 카카오는 `client-secret-post` (본문 포함), 그 외는 보통 `client-secret-basic` (헤더 포함) 방식을 사용하므로 설정 시 주의가 필요합니다.
  - **Redirect URI:** 오타 하나로도 인증이 실패할 수 있으니 정확하게 등록되었는지 확인하세요.

3. **권한(Scope)은 최소한으로**
사용자가 거부감을 느끼지 않도록 꼭 필요한 권한만 요청하세요. 단, OIDC를 사용한다면 `openid`는 필수입니다.

---

## 참고 자료

- [Spring Security OAuth2 공식 문서](https://docs.spring.io/spring-security/reference/servlet/oauth2/index.html)
- [카카오 로그인 개발 가이드](https://developers.kakao.com/docs/latest/ko/kakaologin/common)
- [OpenID Connect 스펙](https://openid.net/specs/openid-connect-core-1_0.html)

---

---

원문: [velog · 2026-01-07](https://velog.io/@co-vol/Spring-Boot-3-OAuth2-%EC%86%8C%EC%85%9C-%EB%A1%9C%EA%B7%B8%EC%9D%B8-%EA%B0%80%EC%9D%B4%EB%93%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4-%EB%A1%9C%EA%B7%B8%EC%9D%B8-%EA%B5%AC%ED%98%84)
