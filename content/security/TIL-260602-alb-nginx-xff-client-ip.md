---
title: "[TIL-260602] ALB·nginx 뒤에서 진짜 Client IP 잡기 + XFF 스푸핑 방어"
date: 2026-06-02
tags: ["spring-boot", "security", "tomcat", "aws-alb", "nginx", "x-forwarded-for"]
categories: ["TIL"]
description: "프록시 뒤 IP 기반 보안은 forward-headers-strategy=native 필수. 안 주면 leftmost 신뢰라 XFF 스푸핑에 뚫린다. RemoteIpValve는 internal-proxies 매칭 홉을 오른쪽→왼쪽으로 벗긴다."
---

## 잘한 점

### XFF 체인 직접 그려보고 정규식·nginx 설정까지 검증

**상황**
- IP allowlist 보안 기능 붙이는데 `application-dev.yaml`의 `internal-proxies` 정규식이 placeholder라 실제 값으로 바꿔야 했음
- ALB도 있고 nginx 프록시도 있어서 뭘 신뢰해야 하는지 헷갈렸다

**액션**
- AWS 콘솔에서 dev ALB의 Network mapping 보고 2개 AZ subnet CIDR 확인 (`10.10.1.0/24`, `10.10.2.0/24`)
- 토폴로지가 `ALB → nginx(127.0.0.1) → Tomcat`인 걸 확정하고, `config/nginx-buws.conf`도 직접 검증 (`proxy_pass` localhost, XFF append)

**칭찬**
- placeholder 정규식을 그냥 두지 않고 실제 인프라랑 1:1로 맞춘 거
- `127\.0\.0\.1|10\.10\.[12]\.\d{1,3}` 로 loopback + ALB subnet 둘 다 커버한 거

---

## 개선점

### forward-headers-strategy=native 빠뜨려서 스푸핑 뚫림

**문제**
- L4 스푸핑 테스트에서 "403 기대"인데 200이 나옴 (가짜 XFF가 통과)

**원인**
- inline properties에 `internal-proxies`만 주고 `server.forward-headers-strategy=native`를 안 줬음
- 그러면 framework(`ForwardedHeaderFilter`)가 동작 → XFF leftmost 신뢰 → 공격자가 XFF 앞에 가짜 IP 박으면 우회된다
- `native`(`RemoteIpValve`)로 강제해야 rightmost 신뢰로 제대로 막힌다

**액션플랜**
- IP 기반 보안 켤 때 `forward-headers-strategy=native` 같이 박는 거 체크리스트화
- 차단 응답도 anonymous면 401(`AuthenticationEntryPoint`)이라 테스트 단언을 403→401로 정정

---

## 배운 점

### RemoteIpValve는 XFF를 오른쪽→왼쪽으로 벗긴다

**배움**
- ALB 뒤에선 Tomcat이 받는 TCP 출발지는 항상 프록시 IP. 진짜 client는 XFF 헤더 안에 있다
- `RemoteIpValve`는 XFF를 오른쪽→왼쪽으로 훑으면서 `internal-proxies` 매칭되는 홉을 벗기고, 처음 안 매칭되는 IP를 client로 판정한다
- 그래서 벗길 신뢰 홉을 *전부* 정규식에 넣어야 한다. nginx가 끼면 nginx(loopback) + ALB(subnet) 둘 다
- leftmost vs rightmost 신뢰 차이가 스푸핑 취약점의 핵심이었음

**의미**
- 프록시 뒤 IP 기반 보안은 "어디까지가 신뢰 홉인가"를 정확히 모르면 그냥 뚫린다
- placeholder `10\.10\.\d{1,3}\.\d{1,3}`(/16 전체)는 너무 넓고 loopback도 누락. 신뢰 범위는 좁고 정확하게

---

## 핵심 내용

### 키워드
- `X-Forwarded-For`, `RemoteIpValve`, `forward-headers-strategy=native`, `internal-proxies`, ALB ENI subnet, `AuthenticationEntryPoint` 401

### 요약
- 토폴로지 `Client → ALB → nginx(127.0.0.1) → Tomcat`. Tomcat `remoteAddr=127.0.0.1`, 진짜 client는 XFF 안.
- `RemoteIpValve`: XFF를 오른쪽→왼쪽으로 훑어 `internal-proxies` 매칭 홉 제거, 첫 비매칭 IP = client. 신뢰 홉 전부 등록해야 함.
- `server.forward-headers-strategy=native` → RemoteIpValve(rightmost 신뢰). 안 주면 framework `ForwardedHeaderFilter`(leftmost 신뢰)라 XFF 스푸핑에 무방비.
- anonymous 요청이 게이트에 막히면 403(`AccessDeniedHandler`)이 아니라 401(`AuthenticationEntryPoint`)로 빠진다.

### 코드/명령어
```yaml
# application-dev.yaml
server:
  forward-headers-strategy: native   # 핵심. 없으면 leftmost 신뢰로 스푸핑 뚫림
  tomcat:
    remoteip:
      remote-ip-header: x-forwarded-for
      internal-proxies: '127\.0\.0\.1|10\.10\.[12]\.\d{1,3}'  # nginx loopback + dev ALB 2 AZ subnet
```
