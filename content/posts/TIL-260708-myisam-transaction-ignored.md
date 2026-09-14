---
title: "[TIL-260708] MyISAM은 트랜잭션을 조용히 무시한다"
date: 2026-07-08
tags: ["MariaDB", "MySQL", "MyISAM", "InnoDB", "트랜잭션", "CodeIgniter3"]
categories: ["TIL"]
description: "paylist가 MyISAM이라 trans_begin/rollback이 조용히 무시돼 orphan 결제건이 남는다. ENGINE=InnoDB 전환으로 트랜잭션이 의도대로 작동."
---

## 개선점

### paylist가 MyISAM이라 트랜잭션이 안 먹는다

**문제**
- 노티 컨트롤러(BaumPnsNoti·SeedNoti·PaysisNoti)가 `trans_begin()` / `trans_commit()` / `trans_rollback()`로 감싸고 그 안에서 `paylist`에 INSERT를 한다
- 근데 `paylist` 엔진이 MyISAM이었다. MyISAM은 트랜잭션 자체가 없어서 INSERT가 `trans_begin` 시점과 무관하게 즉시 반영된다
- 뒤 단계(notilist 저장, 출금 처리)에서 예외 나서 `trans_rollback()`이 불려도 paylist엔 이미 orphan 결제건이 남는다. 결제 데이터인데 정합성이 깨진다

**원인**
- 엔진이 MyISAM인 걸 모르고 트랜잭션 코드를 짰다
- MyISAM에서 trans_* 호출은 에러도 안 나고 조용히 무시된다 — 그래서 "돌아가는 것처럼" 보여서 더 위험

**액션플랜**
- `ALTER TABLE paylist ENGINE=InnoDB`로 전환하면 이 트랜잭션 코드가 원래 의도대로 작동한다
- 전환 전 확인: controllers/models/libraries 전체에 `LOCK TABLES`, `INSERT DELAYED`, `REPAIR/OPTIMIZE TABLE`, FULLTEXT 같은 MyISAM 종속 기능 없음 → 코드 레벨 걸림돌 없음
- 13.5만 행(데이터 48MB + 인덱스 4.6MB)이라 ALTER는 수 초~길어야 1분
- `payment` 테이블(약 10.5만 행)도 같은 트랜잭션 블록에서 쓰이면 동일 리스크 → 별도 확인

---

## 배운 점

### 트랜잭션은 엔진이 지원해야 의미가 있다

**배움**
- `trans_begin()` 썼다고 롤백이 되는 게 아니다. 대상 테이블이 MyISAM이면 그냥 무시된다
- 에러조차 안 나서 코드만 보면 정상처럼 보인다. 실제로 예외 터져 롤백 경로를 타봐야 "어? 데이터가 안 지워지네" 하고 알게 된다

**의미**
- 트랜잭션 코드 짜기 전에 대상 테이블 엔진부터 확인하자. 특히 결제/정산처럼 정합성이 중요한 테이블
- "트랜잭션으로 감쌌으니 안전하다"는 가정은 엔진 확인 없이는 성립 안 한다

---

## 핵심 내용

### 키워드
- `MyISAM`, `InnoDB`, `트랜잭션`, `table-level lock`, `row-level lock`, `ALTER TABLE ENGINE`

### 요약
- MyISAM: 트랜잭션 X, 외래키 X, 쓰기 시 테이블 전체 락 → 롤백 무시 + 노티 동시 수신 시 paylist INSERT가 서로 줄 서서 직렬화됨
- InnoDB: 트랜잭션 O, row-level 락 → 롤백 정상 작동 + 동시성 개선
- 단일 INSERT/UPDATE 하나는 InnoDB에서 그 자체로 원자적. 여러 테이블에 걸친 작업이라야 트랜잭션이 의미 있음

### 코드/명령어
```sql
-- 엔진 확인
SHOW TABLE STATUS WHERE Name = 'paylist';

-- 전환
ALTER TABLE paylist ENGINE=InnoDB;
```
