---
title: "[TIL-260602] 환경 프로필을 기능 토글로 쓰면 안 되는 이유"
date: 2026-06-02
tags: ["Spring Boot", "Kotlin", "@Profile", "@ConditionalOnProperty", "테스트", "설계"]
categories: ["TIL"]
description: "환경 프로파일(dev/prod)을 기능 on/off 스위치로 쓰면 테스트가 환경에 결합된다. 기능은 전용 토글(@ConditionalOnProperty)로 분리하는 게 맞다."
---

## 잘한 점

### "테스트가 dev 쓰는 게 이상한데?" 직감이 맞았음

**상황**
- 통합 테스트 일부가 `@ActiveProfiles("dev")`나 `@ActiveProfiles("test", "dev")`를 쓰는 게 눈에 거슬렸음
- 테스트가 환경 프로파일인 dev를 쓰는 게 이상해 보였다

**액션**
- 왜 dev를 쓰는지 추적 → 프로덕션 코드가 환경 프로파일을 기능 스위치로 쓰고 있던 게 원인이란 걸 찾음
- 무거운 `@ConditionalOnProperty` 리팩토링 대신 BankPgDiagnostic `@Profile`에 `test`만 추가하는 surgical한 방법을 택함

**칭찬**
- "테스트가 이상하다"는 직감을 흘려보내지 않고 근본 원인(프로덕션 코드의 설계 냄새)까지 추적한 거
- 이상론(`@ConditionalOnProperty`)과 현실(작은 변경) 사이에서 균형 잡은 판단

---

## 개선점

### 환경 프로파일이 기능 토글 역할을 하고 있었음

**문제**
- `SecurityConfig`: `ipAllowlistEnabled = acceptsProfiles("dev", "prod")`
- `BankPgDiagnostic`: `@Profile("local", "dev", "stg")`
- 이 게이트들을 테스트하려면 해당 프로파일을 켜는 수밖에 없어서 테스트가 dev를 끌어왔다

**원인**
- 환경(dev/prod)과 기능 on/off가 한 축에 묶여 있음
- 환경 추가(qa 등)할 때마다 `"dev","prod"` 목록을 매번 고쳐야 하는 구조

**액션플랜**
- 이상적으론 `security.ip-allowlist.enabled` 같은 전용 프로퍼티 + `@ConditionalOnProperty`로 분리 → 테스트는 `@ActiveProfiles("test")`만 두고 inline으로 기능만 토글
- 당장은 BankPgDiagnostic만 `@Profile`에 `test` 추가 (prod엔 test 없으니 안전)

---

## 배운 점

### "dev를 쓰려는 게 아니라 prod를 빼려는 것"

**배움**
- 환경 프로파일을 기능 토글로 쓰면 테스트가 환경에 결합된다. 테스트가 dev 쓰는 건 증상이지 원인이 아님
- BankPgDiagnostic이 `@Profile`에 prod를 안 넣은 본질은 "prod에서 이 위험한 진단 엔드포인트를 빼려는 것". 환경이 아니라 "노출 여부"가 진짜 기준이었다
- 스케줄링은 이미 잘 돼 있었음: `@EnableScheduling` + `@Profile("!test")`로 `SchedulingConfig` 자체가 test에서 미등록. `@ActiveProfiles("test", "dev")`도 test 포함이라 `!test`=false라 안전

**의미**
- 기능 on/off는 환경 프로파일이 아니라 전용 토글(`@ConditionalOnProperty`)로 빼는 게 맞다
- 환경과 기능을 같은 축에 묶으면 테스트도, 환경 추가도 다 비싸진다

---

## 핵심 내용

### 키워드
- `@Profile`, `@ConditionalOnProperty`, `@ActiveProfiles`, `Environment.acceptsProfiles`, `@EnableScheduling @Profile("!test")`

### 요약
- 안티패턴: 환경 프로파일(dev/prod)을 기능 on/off 스위치로 사용 → 테스트가 환경 프로파일에 결합되고, 환경 추가 시 목록 수정 비용 발생.
- `@Profile("!test")`는 "활성 프로파일에 test가 없을 때" 매칭. `@ActiveProfiles("test", "dev")`는 test 포함이라 false → 빈 미등록.
- 권장: 기능은 `@ConditionalOnProperty(전용 프로퍼티)`로 분리. 테스트는 `@ActiveProfiles("test")` 유지 + inline 토글.
- 현실 절충: 위험 엔드포인트(BankPgDiagnostic)는 `@Profile`에 `test` 추가로 충분 — prod엔 test 없어 노출 안 됨.
