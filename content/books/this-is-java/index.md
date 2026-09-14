---
title: 이것이 자바다
description: 『이것이 자바다』 챕터 정리. 기초 문법부터 멀티 스레드, 컬렉션, 람다, 스트림까지.
date: 2026-09-14
---

2023년 12월부터 2024년 1월까지 정리했습니다. 앞부분은 문법 확인용이고, 실제로 다시 펴보게 되는 장은 14·15·17장입니다. 스레드 상태와 동기화는 [[redis-lua-first-come-coupon|동시성 테스트의 이중 래치]]를 이해하는 바탕이고, 컬렉션 구현체 선택과 스트림은 Kotlin 컬렉션 API를 쓸 때도 같은 그림입니다.

| 장  | 노트                                          | 한 줄                                   |
| --- | --------------------------------------------- | --------------------------------------- |
| 2   | [[this-is-java/ch02/index\|변수와 타입]]        | 타입 변환 규칙                          |
| 3   | [[this-is-java/ch03/index\|연산자]]             | 오버플로우, NaN/Infinity, 우선순위       |
| 12  | [[this-is-java/ch12/index\|java.base 모듈]]     | Object·System 등 핵심 API               |
| 13  | [[this-is-java/ch13/index\|제네릭]]             | 제한된 타입 파라미터, 와일드카드         |
| 14  | [[this-is-java/ch14/index\|멀티 스레드]]        | 스레드 상태, synchronized, wait/notify  |
| 15  | [[this-is-java/ch15/index\|컬렉션 자료구조]]    | List·Set·Map 구현체 선택                |
| 16  | [[this-is-java/ch16/index\|람다식]]             | 메소드 참조, 생성자 참조                 |
| 17  | [[this-is-java/ch17/index\|스트림과 병렬 처리]] | 중간·최종 처리, 병렬 스트림             |
