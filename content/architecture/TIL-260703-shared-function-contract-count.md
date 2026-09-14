---
title: "[TIL-260703] 공유 함수 반환값이 호출부마다 다르면 지뢰"
date: 2026-07-03
tags: ["mysql", "performance", "refactoring", "architecture", "pagination", "codeigniter"]
categories: ["TIL"]
description: "COUNT(*) 최적화가 같은 함수를 다른 계약으로 쓰던 엑셀 export를 무한루프로 만들었다. 공유 함수 수정 시 모든 호출부 계약을 검토하자."
---

## 잘한 점

### 페이지네이션 COUNT를 전용 COUNT(*)로 최적화

**상황**
- `noti_list` 한 화면 그리는 데 쿼리가 6개나 나갔다
- 그중 COUNT(총건수)용 호출인데도 무거운 목록 쿼리(`@ROWNUM` 서브쿼리 + JOIN 2개, LIMIT 없이 조건 전체 행을 PHP로 끌어옴)와 합계 쿼리 2개를 다 실행하고, 마지막에 `num_rows()`로 개수만 셌다

**액션**
- `SELECT_COUNT` 요청이면 전용 `SELECT COUNT(*)`로 조기 리턴하게 바꿨다. 페이지당 쿼리 6개 → 3개
- `member` JOIN은 검색조건이 `m.name`을 참조할 수 있어 유지, `calculate` JOIN은 조건에 안 쓰여 제외
- LEFT JOIN은 행을 증식시키지 않으니 `num_rows()` 카운트와 결과값 동일, 뷰 영향 없음

**칭찬**
- "전체 materialize 후 세기"라는 낭비를 정확히 짚어서 COUNT 경로만 딱 떼어낸 것

---

## 개선점

### 같은 함수를 엑셀 export가 다른 계약으로 쓰고 있었다 (무한루프 유발)

**문제**
- COUNT(*) 최적화를 넣었더니 엑셀 export 루프가 무한루프에 빠질 뻔했다
- 엑셀 루프는 `noti_list(..., paginationDto, SELECT_COUNT)`를 "배치 LIMIT 적용 후 행 수"로 쓰고 있었다. 0이면 종료하는 구조
- 근데 내 최적화는 paginationDto를 무시하고 항상 전체 건수를 반환한다 → 절대 0이 안 됨 → 무한루프

**원인**
- 같은 `SELECT_COUNT` 인자인데 호출부마다 반환값의 의미가 달랐다: 페이지네이션은 "필터 전체 총건수", 엑셀은 "이번 배치 행 수"
- 함수 하나 고칠 때 한쪽 호출부만 보고 "안전한 최적화"라고 판단

**액션플랜**
- 공유 함수 시그니처를 바꾸기 전엔 Grep으로 모든 호출부를 찾아 각각의 계약(반환값 기대)을 확인하자
- 같은 파라미터가 문맥마다 다른 걸 반환하는 함수는 그 자체가 위험 신호 → 분리 대상

---

## 배운 점

### "안전한 최적화"가 다른 호출부의 암묵적 계약을 깬다

**배움**
- 시그니처가 같아도 호출 맥락마다 함수에 거는 기대가 다를 수 있다
- 내가 최적화한 반환값 의미(전체 총건수)가, 다른 호출부가 의존하던 의미(배치 후 행 수)를 조용히 깨뜨렸다

**의미**
- 공유 함수 수정 = 모든 호출부 계약 검토, 예외 없이
- 부수로 배운 것: `@ROWNUM` 서브쿼리로 행번호를 만들면 LIMIT가 바깥에만 걸려서 안쪽에서 필터 전체를 매번 스캔·정렬한다. LIMIT를 안쪽에 직접 걸고 ROWNUM은 PHP에서 계산하는 게 맞다

---

## 핵심 내용

### 키워드
- `SELECT COUNT(*)`, `num_rows() 안티패턴`, `@ROWNUM 페이징`, `LIMIT 푸시다운`, `공유 함수 계약`

### 요약
- 총건수는 전용 `SELECT COUNT(*)`로. 조건 전체를 materialize한 뒤 `num_rows()`로 세는 건 낭비
- MySQL엔 ROWNUM이 없어 `@ROWNUM:=@ROWNUM+1` 세션변수 + `(SELECT @ROWNUM:=0) R` 서브쿼리로 흉내내는데, 그 서브쿼리 때문에 바깥 LIMIT가 안쪽 스캔을 못 줄인다 → 안쪽에 `ORDER BY ... LIMIT` 직접, ROWNUM은 `총건수 - offset - i`로 PHP 계산
- 공유 함수 반환값이 호출부마다 다르면, 한쪽 최적화가 다른 쪽을 깬다

### 코드/명령어
```php
if ($selectType == GlobalTextUtil::SELECT_COUNT) {
    $countSql = 'SELECT COUNT(*) AS cnt FROM ... ' . $sword; // 목록/합계 쿼리 생략
    $countRow = $this->db->query($countSql)->row();
    return $countRow ? (int) $countRow->cnt : 0;
}
// ⚠️ 단, 이 함수를 "배치 후 행 수"로 쓰는 엑셀 export 호출부가 있으면 그쪽도 같이 고쳐야 함
```
