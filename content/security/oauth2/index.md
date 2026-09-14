---
title: Spring OAuth2 소셜 로그인 시리즈
description: 카카오 로그인 구현에서 시작해 멀티 Provider, 응답 통합, 쿠키 기반 상태 관리, JWT 발급 핸들러까지 5편으로 완결한 시리즈.
date: 2026-09-14
---

2026년 1월에 일주일 동안 쓴 5편입니다. 튜토리얼처럼 읽히지만 매 편마다 하나씩 **설계 결정**이 있습니다. OAuth2 대신 OIDC를 고른 이유, Provider 분기를 if가 아니라 Strategy로 나눈 이유, 세션 대신 쿠키를 택한 이유, 실패를 500으로 뭉개지 않고 분류한 이유.

| 편  | 노트                                                      | 이 편의 결정                                                                   |
| --- | --------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 1   | [[01-kakao-login-oidc\|카카오 로그인 구현]]                 | OAuth2가 아니라 OIDC. 인증이 목적이면 ID 토큰이 있어야 한다                     |
| 2   | [[02-multi-provider-strategy-pattern\|멀티 Provider 지원]] | Provider마다 다른 응답을 Strategy로 캡슐화. 애플 추가 = 클래스 하나              |
| 3   | [[03-user-info-factory-pattern\|사용자 정보 통합]]         | 중첩 JSON 탐색은 유틸로, Extractor 선택은 Factory로                              |
| 4   | [[04-cookie-based-state-csrf-spa\|쿠키 기반 인증]]         | 리다이렉트를 여러 번 거치는 SPA에 세션은 맞지 않는다. 쿠키 + SameSite로 CSRF 방어 |
| 5   | [[05-success-failure-handler-jwt\|Success/Failure Handler]] | 성공하면 자체 JWT, 실패하면 프론트가 분기할 수 있는 에러 코드                    |

## 시리즈 밖에서 이어 읽기

- 발급한 토큰을 어떻게 굴릴지는 [[TIL-260422-jwt-access-refresh-hybrid|JWT Access + Refresh 하이브리드]]에서 이어집니다
- 2편·3편의 패턴 선택 기준은 [[chain-of-responsibility-fraud-detection|Chain of Responsibility 사례]]와 비교해서 읽으면 "왜 여기서는 Strategy였나"가 선명해집니다
