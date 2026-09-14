---
unlisted: true
title: 작성 규칙
aliases:
  - 작성-규칙
tags:
  - meta
description: 이 지식베이스의 노트 작성 컨벤션
---

## frontmatter

```yaml
---
title: 노트 제목 # 없으면 파일명이 제목이 됨
tags:
  - spring
  - performance
description: 한 줄 요약 (검색 결과와 OG 이미지에 쓰임)
draft: false # true면 배포에서 제외
aliases:
  - 다른 이름 # 위키링크에서 이 이름으로도 찾아짐
---
```

## 폴더

| 폴더       | 용도                                                 |
| ---------- | ---------------------------------------------------- |
| `MOC/`     | 주제별 지도. 노트가 늘어나면 여기서 길을 만든다       |
| `notes/`   | 실제 노트. 폴더로 분류하지 말고 태그와 링크로 연결    |
| `private/` | 공개하지 않을 노트 (빌드에서 자동 제외)              |
| `templates/` | Obsidian 템플릿 (빌드에서 자동 제외)               |

폴더 구조에 힘을 빼는 게 핵심입니다. **분류는 태그와 링크로** 합니다. 폴더를 깊게 파면 노트를 어디에 둘지 고민하느라 정작 쓰지 않게 됩니다.

## 파일명

**파일명은 영문 소문자 + 하이픈, 제목은 한글**로 씁니다.

```yaml
# 파일: notes/transactional-self-invocation.md
---
title: "@Transactional 은 왜 self-invocation 에서 안 먹히는가"
aliases:
  - 트랜잭셔널-셀프인보케이션 # 한글 위키링크로도 찾아짐
---
```

파일명이 곧 URL이 되기 때문입니다. 한글 파일명도 동작은 하지만 URL이 퍼센트 인코딩되어 (`%EC%9E%91...`) 공유할 때 지저분해집니다. `aliases` 를 걸어두면 Obsidian에서 한글로 `[[...]]` 검색해도 잡힙니다.

## 노트 하나의 크기

- 하나의 노트는 **하나의 주제**. "Spring 정리" 말고 "@Transactional은 왜 self-invocation에서 안 먹히는가"
- 제목이 문장으로 나오면 잘 쪼갠 것
- 3줄짜리 노트도 괜찮습니다. 나중에 링크가 붙으면서 자라납니다

## 링크

```markdown
[[노트-제목]]           # 위키링크
[[노트-제목|표시할 텍스트]]
[[노트-제목#섹션]]      # 특정 섹션으로
![[노트-제목]]          # 내용 전체를 끼워넣기 (transclusion)
```

링크를 걸면 상대 노트 하단에 **백링크**로 자동으로 나타납니다. 이게 폴더보다 강력한 이유입니다.

## 콜아웃

```markdown
> [!note] 참고
> 내용

> [!warning] 주의
> 내용

> [!tip]- 접히는 팁
> 제목 뒤에 `-` 를 붙이면 기본으로 접힘
```

`note`, `tip`, `warning`, `danger`, `example`, `question`, `quote`, `bug`, `success`, `failure`, `abstract`, `todo` 등을 쓸 수 있습니다.

## 코드

언어를 명시하면 하이라이팅이 됩니다.

````markdown
```java title="OrderService.java"
@Transactional
public void placeOrder(OrderCommand cmd) { ... }
```
````

## 이미지

`content/` 아래 아무 곳에나 두고 `![[파일명.png]]` 로 참조합니다. Obsidian에서 붙여넣기하면 자동으로 처리됩니다.
