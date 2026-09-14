---
title: "[TIL-260708] EXPLAIN + 카디널리티로 인덱스 잡기"
date: 2026-07-08
tags: ["MariaDB", "MySQL", "EXPLAIN", "인덱스", "카디널리티", "성능최적화"]
categories: ["TIL"]
description: "type:ALL/possible_keys:null이면 풀스캔. 카디널리티 높은 컬럼에 복합인덱스. 주석 속 인덱스는 SHOW INDEX로 실제 존재를 검증하자."
---

## 잘한 점

### EXPLAIN + 카디널리티로 인덱스 우선순위 잡기

**상황**
- 노티 컨트롤러 3개(BaumPnsNoti 96회·SeedNoti 58회·PaysisNoti 41회, hot path 상위 3개 총 195회)가 노티 들어올 때마다 중복체크/기존건 조회 쿼리를 날리는데 느렸다

**액션**
- 감으로 인덱스 때려박지 않고 EXPLAIN부터 돌렸다 → `type: ALL`, `possible_keys: null`. 완전 풀스캔이었다
- 카디널리티(선택도) 조회: `appNo` 96%, `tid` 96%, `authNo` 73%, `transaction_no` 93%. 다 선택도가 높아서 인덱스 효과가 크다
- 선택도 근거로 복합인덱스 설계 → 스캔 행 수 수십만 → 1~수 건

**칭찬**
- "일단 인덱스 추가"가 아니라 EXPLAIN + 카디널리티라는 근거로 우선순위를 매긴 것
- READ-ONLY 연결이라 직접 못 만드는 상황에서도 운영 반영 순서(1순위부터)까지 정리해둔 점

---

## 개선점

### 주석엔 있는데 실제 DB엔 없는 인덱스

**문제**
- `NotiListModel` 코드 주석에 "(type, reg_date) 인덱스로 range 스캔 가능"이라고 적혀 있었다
- 근데 실제 DB엔 그 인덱스가 없었다. 관리자 노티 리스트 조회가 풀스캔 + filesort 중

**원인**
- 리팩토링 때 쿼리는 그 인덱스를 전제로 최적화했는데, 정작 인덱스 생성(ALTER)을 안 했다
- 주석만 믿고 "인덱스 있겠거니" 하고 넘어감

**액션플랜**
- 주석에 적힌 인덱스 가정은 `SHOW INDEX`로 실제 존재를 검증하자
- 인덱스를 전제로 쿼리를 최적화하면 인덱스 생성까지 같은 작업에 묶어라. 쿼리만 고치고 인덱스를 빼먹으면 최적화가 무의미

---

## 핵심 내용

### 키워드
- `EXPLAIN`, `type: ALL`, `possible_keys: null`, `카디널리티(선택도)`, `복합인덱스`, `filesort`, `커버링 인덱스`

### 요약
- `type: ALL` + `possible_keys: null` = 인덱스 못 쓰고 풀스캔
- 카디널리티(고유값 비율)가 높은 컬럼일수록 인덱스로 걸러지는 행이 많아 효과 큼
- 필터 + 정렬을 한 인덱스로 커버하려면 `(필터컬럼, 정렬컬럼)` 순서로 복합인덱스
- 조건에 안 쓰이는 JOIN 컬럼은 인덱스에서 빼도 됨

### 코드/명령어
```sql
-- 실행계획
EXPLAIN SELECT ... ;

-- 인덱스 실제 존재 확인 (주석 믿지 말고)
SHOW INDEX FROM notilist;

-- 제안 인덱스 예
ALTER TABLE notilist ADD INDEX notilist_appno_appdtm_paytype_method_ix (appNo, appDtm, paytype, method_type);
ALTER TABLE notilist ADD INDEX notilist_type_regdate_ix (type, reg_date);
```
