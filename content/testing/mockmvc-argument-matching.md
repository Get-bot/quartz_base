---
title: "Spring Boot 테스트에서 발생한 MockMvc 인자 매칭 오류 해결기"
date: 2023-11-21
tags: ["spring-boot", "testing", "mockmvc", "mockito"]
description: "thenThrow가 동작하지 않고 200이 돌아온 이유는 인자 매칭 실패. eq()와 any()로 매처를 명시해 해결한 짧은 기록."
source: https://velog.io/@co-vol/Spring-Boot-%ED%85%8C%EC%8A%A4%ED%8A%B8%EC%97%90%EC%84%9C-%EB%B0%9C%EC%83%9D%ED%95%9C-MockMvc-%EC%9D%B8%EC%9E%90-%EB%A7%A4%EC%B9%AD-%EC%98%A4%EB%A5%98-%ED%95%B4%EA%B2%B0%EA%B8%B0
---

## 1. 문제 상황
최근에 Spring Boot 애플리케이션에서 REST API의 단위 테스트를 진행하던 중, `MockMvc`를 사용한 테스트 케이스에서 예상치 못한 결과를 마주했습니다. 특히, `updateUser API`를 테스트할 때, `NotFoundException`을 발생시켜야 하는 상황에서 계속해서 200 OK 응답이 반환되는 문제가 발생했습니다.
```java
@Test
@DisplayName("사용자 업데이트 API 실패 UserNotFound 테스트")
void updateUserShouldReturn404NotFound() throws Exception {
    // ... 코드 생략 ...
    Mockito.when(userService.update(userId, userUpdateDTO))
        .thenThrow(new NotFoundException("해당하는 유저가 없습니다."));
    // ... 코드 생략 ...
}
```
## 2. 문제 진단
원인 파악을 위해 다음과 같은 점들을 검토했습니다:

1. **Mockito 설정 검증**: `Mockito.when(...).thenThrow(...)` 구문이 정확히 설정되었는지 확인했습니다.
2. **MockMvc 로그 분석**: `andDo(print())`를 통해 상세한 실행 결과를 로깅하여 검토했습니다.
3. **MockMvc와 실제 서버 동작의 차이**: MockMvc는 실제 HTTP 요청을 보내지 않고 서버의 디스패처 서블릿을 모의로 사용한다는 점을 고려했습니다.

## 3. 해결 과정
문제의 원인은 `Mockito`의 인자 매칭이 정확히 이루어지지 않은 것으로 밝혀졌습니다. `userUpdateDTO` 객체가 테스트 중의 `userService.update` 메서드 호출과 정확히 일치하지 않아 예외가 발생하지 않았던 것입니다.

## 4. 해결 방법
ArgumentMatchers의 `any()` 메서드를 사용하여 타입만 일치하면 어떤 객체든 받아들일 수 있도록 설정을 변경했습니다.
```java
@Test
@DisplayName("사용자 업데이트 API 실패 UserNotFound 테스트")
void updateUserShouldReturn404NotFound() throws Exception {
    // ... 코드 생략 ...
    Mockito.when(userService.update(eq(userId), any(UserUpdateDTO.class)))
        .thenThrow(new NotFoundException("해당하는 유저가 없습니다."));
    // ... 코드 생략 ...
}
```
이 변경 후, 테스트는 정상적으로 `NotFoundException`을 발생시키고, 404 Not Found 응답을 반환했습니다.

## 5. 결론
이 경험을 통해 테스트 중에 `Mockito `인자 매칭의 정확성이 얼마나 중요한지 다시 한 번 깨달았습니다. 또한, `ArgumentMatchers`를 효과적으로 사용하여 테스트의 유연성과 견고성을 높일 수 있음을 배웠습니다. 테스트 중 예상치 못한 문제에 직면했을 때, 구체적인 로깅과 세심한 디버깅이 문제 해결의 열쇠가 될 수 있음을 잊지 말아야겠습니다.

---

원문: [velog · 2023-11-21](https://velog.io/@co-vol/Spring-Boot-%ED%85%8C%EC%8A%A4%ED%8A%B8%EC%97%90%EC%84%9C-%EB%B0%9C%EC%83%9D%ED%95%9C-MockMvc-%EC%9D%B8%EC%9E%90-%EB%A7%A4%EC%B9%AD-%EC%98%A4%EB%A5%98-%ED%95%B4%EA%B2%B0%EA%B8%B0)
