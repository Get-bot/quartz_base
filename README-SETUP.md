# Quartz 5 지식베이스 셋업 가이드

이 폴더(`D:\workspace\quartz_base`)에 Quartz 5 기반 지식베이스 블로그를 만듭니다.
Obsidian으로 노트를 쓰고 → `git push` 하면 → GitHub Actions가 GitHub Pages로 자동 배포합니다.

---

## 사전 준비

| 항목      | 확인                                                          |
| --------- | ------------------------------------------------------------- |
| Node.js   | `node -v` → **v22 이상**. 낮으면 https://nodejs.org 에서 설치 |
| Git       | `git --version`                                               |
| GitHub    | 계정 준비 (저장소는 아직 만들지 않아도 됨)                    |

> GitHub Pages 무료 플랜에서는 **public 저장소**만 배포됩니다. private으로 두려면 GitHub Pro가 필요하거나, Cloudflare Pages를 쓰면 됩니다.

---

## 1. 셋업 스크립트 실행

PowerShell을 열고:

```powershell
cd D:\workspace\quartz_base
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

GitHub 사용자명 / 저장소 이름 / 사이트 제목을 물어봅니다. 인자로 미리 줄 수도 있습니다.

```powershell
# 새로 시작
.\setup.ps1 -GitHubUser <사용자명> -RepoName quartz_base -SiteTitle "범진의 지식베이스"

# 기존 노트 폴더(예: D:\workspace\TIL)를 가져오면서 시작
.\setup.ps1 -GitHubUser <사용자명> -RepoName quartz_base -VaultPath "D:\workspace\TIL"

# user.github.io 저장소로 만들 때 (루트 도메인)
.\setup.ps1 -GitHubUser <사용자명> -RepoName <사용자명>.github.io -UserSite
```

스크립트가 하는 일:

1. Quartz 5 소스를 이 폴더로 clone (`v5` 브랜치)
2. `npm install`
3. `npx quartz create -t obsidian` 으로 초기화 (위키링크 `shortest` 해석, OFM 전체 지원)
4. `quartz.config.yaml` 개인화 — 제목, `locale: ko-KR`, plausible 애널리틱스 제거, 태그 목록/최근 노트 활성화, 푸터 링크
5. Quartz 자체 CI 워크플로 삭제 → `.github/workflows/deploy.yml` (GitHub Pages 배포) 생성
6. 시작 노트 배치 + `origin` 리모트 연결 + 초기 커밋

---

## 2. 로컬에서 확인

```powershell
npx quartz build --serve
```

→ http://localhost:8080 . 파일을 저장하면 자동으로 다시 빌드됩니다.

---

## 3. GitHub에 올리기

1. https://github.com/new 에서 **빈 저장소** 생성
   - 이름: 스크립트에 입력한 저장소 이름과 동일하게
   - **README / .gitignore / license 체크 해제** (충돌 납니다)
2. push

   ```powershell
   git push -u origin v5
   ```

3. 저장소 **Settings → Pages → Source** 를 **`GitHub Actions`** 로 변경
4. **Actions** 탭에서 빌드 확인 (1~2분)
5. `https://<사용자명>.github.io/<저장소이름>` 접속

> 브랜치는 Quartz 기본값인 `v5` 입니다. `main`으로 쓰고 싶으면
> `git branch -m v5 main && git push -u origin main` — 워크플로는 두 브랜치 모두 트리거되게 해두었습니다.

---

## 4. Obsidian 연결

Obsidian → **다른 보관소 열기** → **폴더를 보관소로 열기** → `D:\workspace\quartz_base\content`

설정을 Quartz와 맞춥니다.

- 설정 → 파일 및 링크 → **새 링크 형식: 짧은 경로 (Shortest path when possible)**
- 설정 → 파일 및 링크 → **위키링크 사용: 켬**
- 설정 → 파일 및 링크 → 첨부 파일 폴더: `assets` 정도로 지정

`.obsidian/` 폴더는 빌드에서 자동 제외됩니다.

---

## 5. 이후 루틴

```powershell
# 글 쓰기 → 확인 → 배포
npx quartz build --serve
git add . ; git commit -m "add: 인덱스 실행계획 노트" ; git push
```

---

## 폴더 구조

```
quartz_base/
├─ content/               ← Obsidian vault. 여기만 신경쓰면 됨
│  ├─ index.md            홈
│  ├─ MOC/                주제별 지도
│  ├─ notes/              실제 노트
│  ├─ templates/          Obsidian 템플릿 (배포 제외)
│  └─ private/            비공개 노트 (배포 제외, git에도 안 올라감)
├─ quartz.config.yaml     ← 설정은 전부 여기 한 파일
├─ quartz/                Quartz 엔진 (건드릴 일 없음)
├─ .github/workflows/     배포 워크플로
└─ _setup/                이 셋업 스크립트 자산 (배포 제외)
```

---

## 문제가 생기면

| 증상                                    | 해결                                                                 |
| --------------------------------------- | -------------------------------------------------------------------- |
| 빌드 시 플러그인 에러                   | `npx quartz plugin install --latest`                                  |
| `quartz.config.yaml` 수정 후 반영 안 됨 | `npx quartz plugin install --from-config` 후 재빌드                   |
| Pages 배포가 environment 오류           | Settings → Environments → `github-pages` 삭제 후 워크플로 재실행      |
| CSS/링크가 전부 깨짐                    | `baseUrl` 오타 확인 (`https://` 붙이면 안 됨, 끝에 `/` 없음)          |
| 한글 검색이 잘 안 됨                    | `locale: ko-KR` 확인. 검색은 제목·본문 전문 검색이라 2글자 이상 권장  |

Quartz 공식 문서: https://quartz.jzhao.xyz
