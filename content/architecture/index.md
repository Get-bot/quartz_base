---
title: 설계
description: 객체지향 원론에서 DDD 실전, 디자인 패턴 적용까지. "어디를 자를 것인가"에 대한 기록.
date: 2026-09-14
---

설계 노트는 전부 **경계**에 관한 이야기입니다. Aggregate를 어디서 나눌지, 값 객체로 뽑을지 말지, if-else를 언제 객체로 바꿀지, 공유 함수의 계약을 누가 지킬지. 경계를 잘못 그으면 코드가 아니라 팀이 느려집니다. 새 감지 조건 하나에 서비스 클래스를 통째로 열어야 했던 [[chain-of-responsibility-fraud-detection|이상거래 감지 시스템]]이 그랬습니다.

## 도메인 모델

- [[TIL-260410-ddd-domain-design|DDD 도메인 설계 3원칙]] — Rich Domain Model, Value Object 추출, Aggregate 경계 분리를 한 흐름으로
- [[TIL-260429-ddd-rich-domain-aggregate-vo|Rich Domain — Aggregate 분리와 금융 VO]] — Entity를 in-place로 재작성해 Aggregate를 독립시킨 기록. `@Embeddable` 금융 VO 표준 패턴

## 패턴을 꺼내는 시점

패턴은 처음부터가 아니라 **고통이 반복될 때** 꺼냅니다. 그리고 꺼낼 때는 왜 옆의 패턴이 아닌지 적어둡니다.

- [[chain-of-responsibility-fraud-detection|if-else 지옥 탈출기 — Chain of Responsibility]] — "순차 검사 + 하나라도 걸리면 중단"이라 Strategy가 아니라 CoR. 핸들러 자동 등록, 불변 체인, DB 기반 순서 제어까지
- 같은 시기 다른 문제에는 Strategy와 Factory를 골랐습니다: [[02-multi-provider-strategy-pattern|OAuth2 멀티 Provider]], [[03-user-info-factory-pattern|Provider별 응답 파싱]]

## 계약

- [[TIL-260703-shared-function-contract-count|공유 함수 반환값이 호출부마다 다르면 지뢰]] — COUNT 최적화가 엑셀 export를 무한루프로. 공유 함수를 고칠 때는 모든 호출부의 계약을 본다

## 원론

『오브젝트』는 3·4장까지만 읽어 아직 공개하지 않았습니다. 역할·책임·협력과 설계 트레이드오프(캡슐화·응집도·결합도)는 위 DDD 노트들의 배경 이론입니다. 더 읽으면 `books/object/`에서 열립니다.

## 다음에 채울 자리

- Aggregate 간 정합성을 이벤트로 풀 때의 기준 — [[TIL-260420-kafka-consumer-peak-load-shifting|Kafka Peak Load Shifting]]이 그 첫 사례
- "패턴을 걷어낸" 사례. 넣은 기록만 있고 뺀 기록이 없다
