---
title: 인증과 보안
description: 토큰을 어디에 두고, 누구를 믿고, 무엇을 즉시 끊을 수 있어야 하는가. JWT 기초부터 OAuth2 시리즈, 컬럼 암호화, 프록시 뒤 IP까지.
date: 2026-09-14
---

보안 노트의 공통 질문은 "**신뢰의 경계를 어디에 긋는가**"입니다. 서명만 믿을 것인가(Stateless), 서버 상태를 볼 것인가(Stateful). 프록시가 붙여준 헤더를 어디까지 믿을 것인가. 애플리케이션이 암호화할 것인가, DB에 맡길 것인가. 정답은 없고 요구사항(금융 수준인가, 모바일 트래픽인가)이 결정합니다. 그래서 각 노트는 선택 자체보다 **왜 그 선택을 했는지**에 무게를 둡니다.

## 토큰

- [[jwt-basics|JWT란?]] — 구조, 등록 클레임, 서명 검증, 알려진 취약점. 아래 노트들의 공통 전제
- [[TIL-260422-jwt-access-refresh-hybrid|JWT Access + Refresh 하이브리드]] — Access는 Stateless로 빠르게, Refresh는 Stateful로 즉시 끊을 수 있게. Device Family Rotation, Kill-Switch, 그리고 Replay 탐지가 정당한 사용자까지 차단할 수 있다는 딜레마

## 소셜 로그인 시리즈 (`oauth2/`)

카카오 로그인 하나에서 시작해 멀티 Provider, 쿠키 기반 상태 관리, JWT 발급 핸들러까지 5편. [[oauth2/index|시리즈 안내]]에 편마다의 설계 결정을 정리했습니다.

- [[01-kakao-login-oidc|① 카카오 로그인과 OIDC]] · [[02-multi-provider-strategy-pattern|② Strategy Pattern 멀티 Provider]] · [[03-user-info-factory-pattern|③ Factory Pattern 응답 통합]] · [[04-cookie-based-state-csrf-spa|④ 쿠키 기반 상태와 CSRF]] · [[05-success-failure-handler-jwt|⑤ Success/Failure Handler]]

## 인가와 데이터 보호

- [[TIL-260429-aes-gcm-rbac-aop|AES-GCM 컬럼 암호화 + @RequireRole AOP]] — 권한 체크를 횡단 관심사로 분리. 마지막 ADMIN 회수 차단 같은 운영 가드까지
- [[jooq-threadlocal-multitenancy|jOOQ ThreadLocal 멀티테넌시]](Spring) — 권한을 API마다 검사하지 않고 쿼리 조건으로 강제하는 접근. 누락되면 컴파일 에러가 아니라 데이터 유출이라는 점이 설계를 결정했다

## 네트워크 경계

- [[TIL-260602-alb-nginx-xff-client-ip|ALB·nginx 뒤에서 진짜 Client IP 잡기]] — `forward-headers-strategy=native` 없이는 XFF 스푸핑에 뚫린다. RemoteIpValve는 오른쪽에서 왼쪽으로 벗긴다

## 다음에 채울 자리

- 2FA를 붙였을 때 Replay 탐지 정책이 어떻게 바뀌는지 — [[TIL-260422-jwt-access-refresh-hybrid|JWT 하이브리드]]의 액션플랜
- 키 회전 운영 — AES-GCM 키와 JWT 서명 키를 무중단으로 바꾸는 절차
