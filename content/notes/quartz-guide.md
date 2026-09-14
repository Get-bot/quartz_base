---
unlisted: true
title: Quartz 사용법
aliases:
  - quartz-사용법
tags:
  - meta
description: 로컬 미리보기부터 배포까지의 일상 루틴
---

## 일상 루틴

```bash
# 1. 로컬 미리보기 (파일 저장하면 자동 리로드)
npx quartz build --serve
# → http://localhost:8080

# 2. 글 쓰고 나서 배포
git add .
git commit -m "add: 인덱스 실행계획 노트"
git push
# → GitHub Actions가 빌드 + Pages 배포 (1~2분)
```

`npx quartz sync` 한 방으로 commit + push를 해주기도 하지만, 커밋 메시지를 직접 관리하고 싶다면 그냥 git 명령을 쓰는 게 낫습니다.

## Obsidian 연결

`content/` 폴더를 Obsidian vault로 열면 됩니다.

- Obsidian → `다른 보관소 열기` → `폴더를 보관소로 열기` → `content` 선택
- 설정 → 파일 및 링크 → **새 링크 형식: 짧은 경로** (Quartz의 `shortest` 설정과 맞춤)
- 설정 → 파일 및 링크 → **위키링크 사용: 켬**

`.obsidian/` 폴더는 빌드에서 자동으로 제외됩니다.

## 설정 바꾸기

`quartz.config.yaml` 하나만 보면 됩니다.

```yaml
configuration:
  pageTitle: 사이트 제목
  baseUrl: user.github.io/repo # 여기 틀리면 RSS/사이트맵/OG가 깨짐
  locale: ko-KR
  theme:
    colors:
      lightMode: { ... } # 색상 커스터마이징
plugins:
  - source: "@quartz-community/graph"
    enabled: true # 켜고 끄기
```

설정을 저장하면 `--serve` 중일 때 자동으로 다시 빌드됩니다.

## 자주 쓰는 플러그인 토글

| 플러그인             | 하는 일                        |
| -------------------- | ------------------------------ |
| `graph`              | 노트 연결 그래프               |
| `explorer`           | 좌측 파일 트리                 |
| `backlinks`          | 이 노트를 참조한 노트 목록     |
| `search`             | 전문 검색                      |
| `recent-notes`       | 최근 노트 목록                 |
| `comments`           | giscus 댓글 (별도 설정 필요)   |
| `encrypted-pages`    | 비밀번호로 잠그는 노트         |
| `explicit-publish`   | `publish: true` 인 노트만 배포 |

> [!warning] 플러그인을 새로 켰다면
> `enabled: true` 로 바꾼 뒤에는 설치가 필요합니다.
>
> ```bash
> npx quartz plugin install --from-config
> ```

## 비공개로 두고 싶은 노트

셋 중 하나를 쓰면 됩니다.

1. `content/private/` 폴더에 넣기 — 빌드에서 제외
2. frontmatter에 `draft: true` — 빌드에서 제외
3. `encrypted-pages` 플러그인 + frontmatter `password: ...` — 배포는 되지만 비밀번호 필요

## 커스텀 도메인을 붙일 때

기본 셋업에서는 `cname` 플러그인을 꺼두었습니다. 이 플러그인은 `baseUrl` 의 호스트를 그대로 `CNAME` 파일로 내보내는데, `user.github.io/repo` 형태의 project page 에서는 `user.github.io` 가 커스텀 도메인으로 잘못 설정되어 배포가 깨집니다.

실제 도메인(`notes.example.com` 등)을 붙일 때만 이렇게 하세요.

```yaml
configuration:
  baseUrl: notes.example.com
plugins:
  - source: "@quartz-community/cname"
    enabled: true
```

그리고 DNS에 `CNAME` 레코드로 `notes.example.com` → `user.github.io` 를 추가한 뒤, 저장소 Settings > Pages > Custom domain 에 입력합니다.

## Quartz 업그레이드

```bash
npx quartz upgrade
```

`upstream` 리모트에서 최신 Quartz를 가져와 머지합니다. `content/` 와 `quartz.config.yaml` 은 보존됩니다.
