---
title: "[TIL-260708] InnoDB 전환 전 buffer_pool 사이징 확인"
date: 2026-07-08
tags: ["MariaDB", "MySQL", "InnoDB", "innodb_buffer_pool_size", "성능최적화"]
categories: ["TIL"]
description: "MyISAM→InnoDB 전환 시 늘어나는 데이터가 buffer pool을 초과하면 디스크 I/O가 늘어난다. 전환과 함께 buffer_pool 상향이 필요."
---

## 배운 점

### InnoDB 전환은 "ALTER 한 방"이 아니라 버퍼풀 예산이 있는 작업

**배움**
- MyISAM → InnoDB로 바꾸면 그 테이블 데이터도 이제 InnoDB buffer pool을 먹는다
- 버퍼풀이 부족하면 hot data가 디스크로 밀려서 I/O가 늘고, 인덱스 추가하려던 게 오히려 느려질 수 있다
- paylist(52MB) 하나 얹었을 뿐인데 128MB 버퍼풀을 넘겨버리는 상황이었다

**의미**
- 엔진 전환·인덱스 추가처럼 InnoDB 용량을 늘리는 작업은 항상 버퍼풀 여유부터 계산하고 들어가자
- 성능 개선한다고 넣은 게 메모리 예산 초과로 역효과 나면 아깝다

---

## 핵심 내용

### 키워드
- `innodb_buffer_pool_size`, `InnoDB`, `버퍼풀`, `디스크 I/O`

### 요약
- 현재 `innodb_buffer_pool_size = 128MB`
- 기존 InnoDB 테이블 합계가 이미 95MB+ (notilist 68.6 + withdrawlist 15.5 + withdraw 9.5 + 기타)로 버퍼풀을 거의 채우고 있음
- 여기에 paylist(52.8MB) 얹으면 148MB → 128MB 초과 → 디스크 I/O 증가
- 서버 RAM 8GB인데 웹서버 + DB가 한 곳에 있음. 순수 DB 전용이면 RAM의 50~70%가 정석이지만, 공존이라 보수적으로 256~512MB로 올리는 게 안전
- 신규 인덱스까지 추가하면 InnoDB 용량이 더 늘어나므로 전환과 버퍼풀 상향을 같이 진행

### 코드/명령어
```sql
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- 런타임 조정(재시작 없이, 지원 버전)
SET GLOBAL innodb_buffer_pool_size = 268435456;  -- 256MB

-- 영구 반영: my.cnf
-- [mysqld]
-- innodb_buffer_pool_size = 512M
```
