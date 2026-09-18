# humanize-korean 인계 절차

정리본 본문을 `humanize-korean:humanize-korean` 스킬에 넘겨 AI 티를 걷어내고, 결과를 구조 손상 없이 되돌려 붙이는 절차. 스크립트가 분리·재조립·검증을 맡고, LLM은 humanize 스킬 호출 한 번만 한다.

humanize-korean은 문체만 바꾸는 스킬이지만 마크다운 전체를 주면 위험한 지점이 있다 — 불릿을 문단으로 합치거나(C·J 구조 카테고리), 위키링크 표시 텍스트를 다듬거나, 코드블록 안을 건드릴 수 있다. 그래서 **주장 절만** 넘기고 나머지는 빼놓는다. '이 장에서 남은 것'은 사용자의 기억이라 제외한다 — 넘겼더니 쉼표와 어미가 바뀌었다(실측).

## 작업 폴더

```
_workspace/book-digest/<book>-chNN/
├── index.before-digest.md   # Phase 0 백업 (기존 정리본이 있었을 때)
├── body_for_humanize.md     # prepare 산출 — humanize 입력
├── manifest.json            # prepare 산출 — 절 배치·코드블록·frontmatter
├── merged.md                # merge 산출 — 재조립 결과
└── index.before.md          # merge --write 직전 백업
```

humanize-korean 자체는 `_workspace/YYYY-MM-DD-NNN/`을 cwd에 만든다. 폴더명이 겹치지 않으니 같은 `_workspace/` 아래에 공존한다. `.gitignore`에 `_workspace/`가 있어야 한다(Phase 0에서 확인).

## 1. 분리

```
python <skill-dir>/scripts/humanize_io.py prepare \
  --note content/study/<book>/chNN/index.md \
  --out-dir _workspace/book-digest/<book>-chNN
```

- 기본 제외 절: `이 장에서 남은 것`, `여기서 나온 노트`, `넘어간 것`. HTML 주석만 있는 서문도 제외. `--skip "절 제목"`으로 더 뺄 수 있다.
- 코드블록은 `<!-- KEEP:code:n -->`으로 치환된다. 절마다 `<!-- SECTION:i -->` 마커가 앞에 붙는다.
- 출력 줄에 "절 N개 중 M개를 윤문 대상으로"가 나온다. M이 0이면 넘길 게 없으니 Phase 4를 건너뛴다.

## 2. humanize-korean 호출

Skill 도구로 한 번 호출한다. 인자는 파일 경로와 옵션이다.

```
Skill(
  skill = "humanize-korean:humanize-korean",
  args  = "<절대경로>/_workspace/book-digest/<book>-chNN/body_for_humanize.md 파일의 내용을 윤문. 장르: 블로그, 강도: 보수. 이 글은 개인 지식베이스의 기술 노트라 해라체(~다)를 유지한다. H2 제목 줄(## ...), 불릿 구조, 위키링크 [[...]], HTML 주석 <!-- ... -->, 인라인 코드 `...`는 글자 그대로 둔다. 불릿을 문단으로 합치지 않는다."
)
```

- **강도 보수**인 이유: 정리본은 voice.md에 맞춰 이미 사용자 문체에 가깝게 쓴 상태다. 적극 윤문은 사용자 특유의 짧은 문장·판단·`—`를 "AI 티"로 오인해 지울 수 있다.
- **장르 블로그**인 이유: 기술 노트가 humanize의 장르 키 중 blog에 가장 가깝다. essay로 두면 격식이 올라간다.
- 경로(light/standard/heavy)는 humanize의 shim이 route_hint로 정한다. 사용자가 "정밀하게"라고 했을 때만 `--strict`를 붙인다.
- Windows에서 humanize의 shim 명령이 `python3`로 실패하면 `python`으로 바꿔 실행한다.

결과는 `_workspace/YYYY-MM-DD-NNN/final.md`. 가장 최근 run 폴더를 잡는다(Glob `_workspace/*/final.md` 후 수정 시각 최신).

## 3. 재조립 + 검증

```
python <skill-dir>/scripts/humanize_io.py merge \
  --out-dir _workspace/book-digest/<book>-chNN \
  --humanized _workspace/<run_id>/final.md \
  --write
```

merge가 하는 일:

1. `final.md` 끝의 `<!-- HUMANIZE-SUMMARY -->` 블록을 뗀다.
2. `<!-- SECTION:i -->` 마커로 절을 다시 나눈다. 마커가 사라졌으면 H2 순서로 대응시킨다. 그것도 안 맞으면 치명 실패 — 아무것도 덮어쓰지 않는다.
3. `<!-- KEEP:code:n -->`을 원래 코드블록으로 복원한다.
4. **절 단위 검증** — 하나라도 어긋나면 그 절만 원본으로 롤백하고 `!` 줄로 보고한다:
   - 위키링크 타깃 집합이 같은가 (표시 텍스트는 바뀌어도 됨)
   - H2 제목 줄이 살아 있고 수가 같은가 (제목 문장 자체는 바뀌어도 됨)
   - 코드블록 수가 같고 KEEP 잔재가 없는가
   - '이 장에서 남은 것' 불릿 수가 같은가 (`--skip`을 바꿔 그 절까지 넘겼을 때만 걸린다)
5. 제외했던 절·frontmatter와 원래 순서로 재조립해 `merged.md`에 쓴다.
6. `--write`면 노트를 `index.before.md`로 백업하고 `merged.md`로 덮어쓴다. 치명 실패면 `--force`가 없는 한 덮어쓰지 않는다.

출력 마지막 줄의 변경률(문자 기준)을 보고에 적는다. humanize 쪽 게이트가 30% 경고, 50% 중단이니 그보다 훨씬 낮게 나오는 게 정상이다(보수 강도 기준 5~20%).

## 4. 눈으로 한 번

merge 뒤 정리본을 다시 읽는다. 스크립트가 못 잡는 것:

- 주장 절 문단의 **볼드 구절**이 살아 있나
- 소제목 문장이 명사구로 바뀌지 않았나 ("컴파일 시점으로 당긴다" → "컴파일 시점 검사"가 되면 되돌린다)
- 해라체가 합니다체로 올라가지 않았나
- 사용자 손글씨 부분('남은 것', '넘어간 것' 이유)이 그대로인가 — 제외 절이라 그대로여야 정상이다

어긋난 절은 `index.before.md`에서 그 절만 되돌린다. 전체를 되돌리지 않는다.

## 영역 노트를 만들었을 때

같은 절차를 그 파일에 대해 한 번 더 돈다. `--out-dir`는 `_workspace/book-digest/<book>-chNN/<노트-파일명>/`으로 나눈다. 영역 노트는 '남은 것' 절이 없으니 불릿 수 검증은 자동으로 건너뛴다.

## 건너뛰는 경우

- prepare가 윤문 대상 0절이라고 하면
- 사용자가 "윤문은 빼고" 또는 "문체는 내가 볼게"라고 하면
- humanize-korean 스킬이 설치되어 있지 않으면 — 그 사실을 보고하고 voice.md만으로 마친다
