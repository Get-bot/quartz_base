---
title: "[TIL-260703] CodeIgniter3 트랜잭션 managed vs manual"
date: 2026-07-03
tags: ["codeigniter", "php", "transaction", "innodb", "code-review"]
categories: ["TIL"]
description: "CI3 트랜잭션 managed/manual 혼용에서 rollback만 빼면 오히려 악화된다. manual 통일이 정답이고 rollback은 예외 경로의 필수 정리 로직."
---

## 개선점

### CI3 트랜잭션 managed/manual 혼용 — "rollback만 빼기"로 대응하면 악화된다

**문제**
- 코드리뷰 지적: `trans_start()`(managed)로 시작하면서 catch에선 `trans_rollback()`(manual)을 호출한다. managed 모드에서 예외 시 부분 커밋 위험이라고
- 처음엔 "그럼 catch의 rollback만 빼면 되나? 아니면 모델 내부 트랜잭션까지 다 빼야 하나?" 하고 고민했다

**원인 (소스 까보고 확인)**
- CI3 소스를 직접 확인해보니 이 버전 `trans_start()`는 내부에서 그냥 `trans_begin()`을 호출한다 = 사실상 동일 함수
- 그래서 start ↔ rollback은 depth 회계상 이미 짝이 맞는다
- 리뷰어가 우려한 "trans_complete()가 부분 커밋"은 현재 구조에선 실제로 안 난다 — 앱 예외(`throw`)가 나면 `trans_complete()` 도달 전에 catch로 점프하기 때문. 즉 동작상 정상이고, "관용구 혼용으로 인한 명료성" 이슈에 가깝다

**액션플랜**
- ❌ rollback만 빼기: 예외 시 열린 트랜잭션이 방치된다. CI가 자동으로 안 닫아주니 persistent/재사용 커넥션에서 다음 요청·쿼리로 오염된다. rollback은 예외 경로의 필수 정리 로직 → **유지**
- ✅ 정답: 컨트롤러를 manual로 통일. `trans_begin()` → try 안에서 `trans_status()` 체크 → `trans_commit()`, catch에서 `trans_rollback()` 유지
- 모델 내부 단일-statement 트랜잭션 제거는 별개 작업으로. 안전하지만 호출부가 넓어 스코프 분리

---

## 배운 점

### 프레임워크 동작은 소스를 까봐야 정확하다

**배움**
- 리뷰어 지적과 문서만으로 판단했으면 "부분 커밋 위험"을 그대로 믿고 엉뚱하게 고쳤을 것
- 소스로 `trans_start = trans_begin` 확인하니, 이 구조에선 부분 커밋이 실제로 안 일어난다는 게 명확해졌다
- 단일 DML(INSERT/UPDATE 1개)은 InnoDB에서 이미 원자적이라 트랜잭션으로 감싸는 게 무의미하다는 것도 알게 됨

**의미**
- 리뷰 지적을 "일단 문제 되는 줄 빼기"로 대응하면 오히려 악화될 수 있다. 그 코드가 왜 있는지(rollback = 정리 로직) 이해하고 고치자
- managed/manual은 섞지 말고 하나로 통일. 트랜잭션 경계는 호출부(컨트롤러)가 소유하고 모델은 열지 않는 게 명확

---

## 핵심 내용

### 키워드
- `CodeIgniter3`, `trans_begin/trans_commit/trans_rollback`(manual), `trans_start/trans_complete`(managed), `trans_status()`, `trans_strict`, `_trans_depth`

### 요약
- managed = `trans_start`/`trans_complete`(상태 자동 관리), manual = `trans_begin`/`trans_status`/`trans_commit`/`trans_rollback`(수동). CI3에선 `trans_start()` 내부가 `trans_begin()` 호출
- 예외 경로에서 `trans_rollback()`을 빼면 열린 트랜잭션이 방치 → persistent 커넥션 오염
- 단일 DML은 InnoDB에서 원자적 → 트랜잭션 래핑 무의미
- footgun: `trans_strict=FALSE`면 중첩 `trans_complete()` 실패 시 `_trans_status`를 다시 TRUE로 리셋 → 바깥 트랜잭션이 실패를 못 보고 부분 커밋. 그래서 모델은 트랜잭션을 열지 말고 호출부가 경계를 소유하는 게 안전

### 코드/명령어
```php
// manual 통일 패턴
$this->db->trans_begin();
try {
    // ... 여러 테이블 insert/update ...
    if ($this->db->trans_status() === false) {
        throw new Exception('DB 처리 중 오류');
    }
    $this->db->trans_commit();
} catch (Exception $e) {
    $this->db->trans_rollback();   // 필수 정리 로직 — 절대 빼지 말 것
    writeLog(...);
}
```
