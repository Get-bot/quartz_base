#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_digest.py — book-digest 산출물 검증 (LLM 0콜, 결정적)

사용: python verify_digest.py --book kotlin-in-action --chapter 1 [--root <레포 루트>] [--json]
      --root 를 생략하면 cwd에서 위로 올라가며 quartz.config.yaml 이 있는 폴더를 찾는다.

검사:
  raw        frontmatter(book/chapter/status), '## 절 지도' 와 체크 항목
  raw-code   원본 백업(_workspace/book-digest/<book>-chNN/raw.original.md)이 있으면 raw 코드블록이 원본과 같은지
             (줄 끝 공백·언어 태그 무시. 다르면 WARN — Phase 1 보고의 오타·붙여넣기 오류 수정 목록과 맞춰 본다)
  digest     frontmatter 필수 필드·태그 kebab-case, '이 장에서 남은 것' 3~5불릿, 주장 절이 절 번호로 시작하지 않는지
  template   정리본에 템플릿 안내문이 남아 있는지 (raw를 study/ 에 쓴 채로 두면 여기서 걸린다)
  skipped    절 지도의 [ ]/[~] 항목이 정리본 '넘어간 것'에 전부 있는지, 이유가 비어 있는지
  extracted  '여기서 나온 노트' 절이 있다면 실제로 뺀 노트를 링크하고 있는지 (빈 절이면 절을 지운다)
  code       정리본 코드블록의 줄이 전부 raw 코드블록에 있는지(앞뒤 공백 무시, `// ...` 생략 줄 허용), 블록 수(보고용 — 상한 없음)
             줄 단위 대조라 raw의 서로 다른 블록에서 줄을 섞어 와도 통과한다. 지어낸 줄을 잡는 검사다
  transcript 정리본 문장 중 raw와 글자 그대로 같은 비율 (보고용 — 책 문장을 옮겨도 되므로 판정하지 않는다. 코드블록은 세지 않는다)
  links      정리본·책 index 의 [[위키링크]]가 content/ 안에서 해소되는지 (경로·파일명·alias·접미 매칭)
  book-index study/<book>/index.md 표에 이 장 행이 있는지
  residue    윤문 잔재 주석(HUMANIZE-SUMMARY / KEEP / SECTION)

exit 0 = FAIL 없음, 1 = FAIL 있음
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
WIKI_RE = re.compile(r"(?<!!)\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEC_NUM_RE = re.compile(r"(?<![\d.])(\d+\.\d+(?:\.\d+)?)(?![\d.])")
MAP_ITEM_RE = re.compile(r"^\s*-\s*\[( |x|X|~)\]\s*(.+?)\s*$", re.M)
FIXED_HEADINGS = ("이 장에서 남은 것", "넘어간 것", "여기서 나온 노트")
# 들여쓴 펜스(불릿 안 코드블록)와 4백틱 이상 펜스도 코드블록이다. 0열만 보면 그 안의 코드가 검사를 빠져나간다.
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.S | re.M)
ELIDE_RE = re.compile(r"^//\s*\.\.\.$")
# content/templates/book.md 의 안내문. 정리본에 남으면 템플릿을 채우다 만 것이다.
TEMPLATE_PHRASES = (
    "책을 덮고 나서도 기억나는 것 3~5줄",
    "## 주장 하나를 문장으로",
    "그 주장이 딛고 선 개념부터",
    "이름만 나열하면 나중에 찾아올 값이 없다",
    "읽지 않았거나 훑기만 한 절",
    "○○○",
    "노트-파일명",
)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def parse_fm(text):
    """최소 YAML: key: value / key: [a, b] / key:\\n  - a"""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm, key = {}, None
    for line in m.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        mk = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if mk and not line[0].isspace():
            key, val = mk.group(1), mk.group(2).strip()
            val = re.sub(r"\s+#.*$", "", val)
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                fm[key] = []
            else:
                fm[key] = val.strip("\"'")
        elif key is not None and re.match(r"^\s*-\s+", line):
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(re.sub(r"^\s*-\s+", "", line).strip().strip("\"'"))
    return fm, text[m.end():]


def sections(body):
    """H2 제목 → 본문. 코드블록 안의 '## ' 무시."""
    out, cur, in_code = {}, None, False
    for ln in body.split("\n"):
        if ln.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
        if not in_code and ln.startswith("## "):
            cur = ln[3:].strip()
            out[cur] = []
        elif cur is not None:
            out[cur].append(ln)
    return {k: "\n".join(v) for k, v in out.items()}


def find_section(secs, prefix):
    for k, v in secs.items():
        if k.startswith(prefix):
            return k, v
    return None, None


def bullets(text):
    return [ln for ln in text.split("\n") if re.match(r"^\s*[-*]\s+\S", ln)]


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "quartz.config.yaml").exists():
            return p
    return start


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, check, msg):
        self.items.append({"level": level, "check": check, "msg": msg})

    def fail(self, c, m):
        self.add("FAIL", c, m)

    def warn(self, c, m):
        self.add("WARN", c, m)

    def ok(self, c, m):
        self.add("PASS", c, m)

    def info(self, c, m):
        self.add("INFO", c, m)

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)

    @property
    def failed(self):
        return self.count("FAIL") > 0


def build_link_index(content: Path):
    """키: content 상대 slug(확장자 없음, /), 파일명(stem), 폴더명(index.md일 때), alias."""
    idx = {}

    def put(k, rel):
        idx.setdefault(k, set()).add(rel)

    for p in content.rglob("*.md"):
        rel = p.relative_to(content).with_suffix("").as_posix()
        put(rel, rel)
        put(p.stem, rel)
        if p.stem == "index" and p.parent != content:
            put(p.parent.relative_to(content).as_posix(), rel)
        try:
            fm, _ = parse_fm(read(p))
        except Exception:
            continue
        al = fm.get("aliases", [])
        if isinstance(al, str):
            al = [al]
        for a in al:
            put(a, rel)
    return idx


def resolve(target, idx):
    t = target.strip().replace("\\", "/").strip("/")
    if t.endswith(".md"):
        t = t[:-3]
    if t in idx:
        return True
    suffix = "/" + t
    return any(k.endswith(suffix) for k in idx if "/" in k)


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def strip_non_content(text):
    """HTML 주석·코드블록 안의 링크는 검사하지 않는다 (템플릿 예시·설명용)."""
    return FENCE_RE.sub("", strip_comments(text))


def code_blocks(text):
    """코드블록 본문 목록. 줄 끝 공백과 앞뒤 빈 줄을 걷어낸다. HTML 주석 안의 블록은 뺀다."""
    return ["\n".join(ln.rstrip() for ln in m.group(2).strip("\n").split("\n"))
            for m in FENCE_RE.finditer(strip_comments(text))]


def code_lines(blocks):
    """코드블록들의 비어 있지 않은 줄(앞뒤 공백 제거). 줄 단위 대조에 쓴다."""
    return [ln.strip() for b in blocks for ln in b.split("\n") if ln.strip()]


def first_line(block):
    return next((ln.strip() for ln in block.split("\n") if ln.strip()), "")[:50]


def check_links(text, idx, rep, label):
    targets = [t.rstrip("\\") for t in WIKI_RE.findall(strip_non_content(text))]  # 표 안 \| 이스케이프 제거
    bad = sorted({t for t in targets if not resolve(t, idx)})
    if bad:
        rep.fail("links", f"{label}: 해소 안 되는 위키링크 {len(bad)}개 — {', '.join(bad)}")
    else:
        rep.ok("links", f"{label}: 위키링크 {len(targets)}개 모두 해소")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None)
    ap.add_argument("--book", required=True)
    ap.add_argument("--chapter", required=True, type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = Path(a.root).resolve() if a.root else find_root(Path.cwd().resolve())
    content = root / "content"
    ch = f"ch{a.chapter:02d}"
    raw_p = content / "private" / f"{a.book}-{ch}-raw.md"
    dig_p = content / "study" / a.book / f"{ch}.md"
    bidx_p = content / "study" / a.book / "index.md"
    orig_p = root / "_workspace" / "book-digest" / f"{a.book}-{ch}" / "raw.original.md"
    rep = Report()
    rep.info("paths", f"root={root} raw={raw_p.relative_to(root)} digest={dig_p.relative_to(root)}")

    if not content.exists():
        rep.fail("root", f"content/ 가 없다: {root} — --root 를 확인")
        return finish(rep, a)

    # ---------------------------------------------------------------- raw
    raw_body, raw_skipped = "", []  # (num, text, has_reason)
    map_known = False  # 절 지도를 읽었을 때만 '넘어간 것' 유무를 판정한다
    if not raw_p.exists():
        rep.fail("raw", f"원문 없음: {raw_p}")
    else:
        raw_fm, raw_body = parse_fm(read(raw_p))
        for k in ("book", "chapter", "status"):
            if k not in raw_fm:
                rep.fail("raw-fm", f"raw frontmatter에 {k} 없음")
        if str(raw_fm.get("book", "")) != a.book:
            rep.fail("raw-fm", f"raw book='{raw_fm.get('book')}' ≠ '{a.book}'")
        if str(raw_fm.get("chapter", "")) != str(a.chapter):
            rep.fail("raw-fm", f"raw chapter='{raw_fm.get('chapter')}' ≠ {a.chapter}")
        if raw_fm.get("status") != "digested":
            rep.warn("raw-fm", f"raw status='{raw_fm.get('status')}' — 정리본을 만들었으면 digested 로")
        want_digest = f"study/{a.book}/{ch}"
        if raw_fm.get("digest") and str(raw_fm["digest"]).strip("/") != want_digest:
            rep.warn("raw-fm", f"raw digest='{raw_fm['digest']}' ≠ '{want_digest}'")

        _, map_txt = find_section(sections(raw_body), "절 지도")
        if map_txt is None:
            rep.fail("raw-map", "'## 절 지도' 절 없음")
        else:
            items = MAP_ITEM_RE.findall(map_txt)
            if not items:
                rep.fail("raw-map", "절 지도에 '- [x] N.n 제목' 항목 없음")
            else:
                map_known = True
                n_read = sum(1 for m, _ in items if m in "xX")
                for mark, text in items:
                    if mark in (" ", "~"):
                        num = SEC_NUM_RE.search(text)
                        has_reason = bool(re.search(r"—\s*\S|\s-\s+\S", text))
                        raw_skipped.append((num.group(1) if num else None, text, has_reason))
                rep.ok("raw-map", f"절 지도 {len(items)}절 — 읽음 {n_read}, 건너뜀/훑음 {len(raw_skipped)}")
                for num, text, _ in raw_skipped:
                    if num is None:
                        rep.warn("raw-map", f"절 번호 없는 건너뜀 항목: '{text}' — 대조 불가")

        # Phase 1 은 코드를 고치지 않는다. 원본 백업이 있으면 코드블록이 그대로인지 본다.
        if orig_p.exists():
            orig_c, raw_c = Counter(code_blocks(read(orig_p))), Counter(code_blocks(raw_body))
            only_raw, only_orig = list((raw_c - orig_c).elements()), list((orig_c - raw_c).elements())
            if only_raw or only_orig:
                # 블록 첫 줄은 양쪽이 같은 경우가 많아(붙여넣기 오류는 블록 중간에 있다) 달라진 줄을 보여준다.
                raw_lines, orig_lines = set(code_lines(only_raw)), set(code_lines(only_orig))
                added, removed = sorted(raw_lines - orig_lines), sorted(orig_lines - raw_lines)
                rep.warn(
                    "raw-code",
                    f"원본과 다른 코드블록 — raw에만 {len(only_raw)}개, 원본에만 {len(only_orig)}개 "
                    f"(블록: {'; '.join(f'`{first_line(b)}`' for b in only_raw + only_orig)}). "
                    f"raw에만 있는 줄: {', '.join(f'`{s[:50]}`' for s in added[:5]) or '없음'} / "
                    f"원본에만 있는 줄: {', '.join(f'`{s[:50]}`' for s in removed[:5]) or '없음'}"
                    " — Phase 1 보고의 오타·붙여넣기 오류 수정 목록과 맞는지 본다",
                )
            else:
                rep.ok("raw-code", f"코드블록 {sum(raw_c.values())}개가 원본과 같음")
        else:
            rep.info("raw-code", f"원본 백업 없음({orig_p.relative_to(root)}) — raw ↔ 원본 코드 대조 생략")

    # ---------------------------------------------------------------- link index (digest·book index 공용)
    idx = build_link_index(content)

    # ---------------------------------------------------------------- digest
    if not dig_p.exists():
        rep.fail("digest", f"정리본 없음: {dig_p}")
    else:
        dig_text = read(dig_p)
        dig_fm, dig_body = parse_fm(dig_text)
        secs = sections(dig_body)

        for k in ("title", "date", "tags", "description"):
            if not dig_fm.get(k):
                rep.fail("digest-fm", f"frontmatter {k} 비어 있음")
        title = str(dig_fm.get("title", ""))
        if title and not re.match(rf"^{a.chapter}\.\s", title):
            rep.warn("digest-fm", f"title이 '{a.chapter}. '로 시작하지 않음: '{title}'")
        tags = dig_fm.get("tags", [])
        tags = [tags] if isinstance(tags, str) else tags
        bad_tags = [t for t in tags if not TAG_RE.match(t)]
        if bad_tags:
            rep.fail("digest-tags", f"kebab-case 아닌 태그: {bad_tags}")
        for need in ("book", a.book):
            if need not in tags:
                rep.warn("digest-tags", f"태그에 '{need}' 없음")
        if str(dig_fm.get("draft", "")).lower() == "true":
            rep.info("draft", "draft: true — 배포 제외 상태. 해제는 사용자가")

        _, left = find_section(secs, "이 장에서 남은 것")
        if left is None:
            rep.fail("digest-left", "'## 이 장에서 남은 것' 없음")
        else:
            n = len(bullets(left))
            (rep.ok if 3 <= n <= 5 else rep.warn)("digest-left", f"남은 것 {n}줄" + ("" if 3 <= n <= 5 else " (3~5 권장)"))

        claims = [h for h in secs if not h.startswith(FIXED_HEADINGS)]
        if not claims:
            rep.warn("digest-claims", "주장 절이 없음 — 얇은 노트")
        else:
            secish = [h for h in claims if re.match(r"^\d+(\.\d+)+", h)]
            if secish:
                rep.fail("digest-claims", f"소제목이 책 절 번호로 시작: {secish} — 주장 문장으로 바꾼다")
            nounish = [h for h in claims if len(h) <= 12 and not re.search(r"[다까나가라야지]\s*$|\?$", h)]
            if nounish:
                rep.warn("digest-claims", f"문장이 아닌 것 같은 소제목: {nounish}")
            rep.ok("digest-claims", f"주장 절 {len(claims)}개: " + " / ".join(claims))

        left_over = [p for p in TEMPLATE_PHRASES if p in strip_comments(dig_body)]
        if left_over:
            rep.fail("template", f"템플릿 안내문이 남아 있음: {left_over} — raw를 study/ 에 쓴 채라면 Phase 1 로 옮긴다")

        # '넘어간 것'은 건너뛴 절이 있을 때만 두는 절이다. 없으면 절 자체를 만들지 않는다.
        _, skipped_txt = find_section(secs, "넘어간 것")
        if skipped_txt is None:
            if raw_skipped:
                rep.fail("digest-skipped", f"절 지도에 건너뛴 절이 {len(raw_skipped)}개인데 '## 넘어간 것' 없음")
            elif map_known:
                rep.ok("digest-skipped", "건너뛴 절 없음 — '넘어간 것' 절 없음")
            else:
                rep.info("digest-skipped", "raw 절 지도를 못 읽어 '넘어간 것' 유무는 대조 불가")
        elif not bullets(skipped_txt):
            rep.fail("digest-skipped", "'넘어간 것' 절에 항목이 없음 — 건너뛴 절이 없으면 절 자체를 지운다")
        else:
            dig_items = bullets(skipped_txt)
            dig_nums = set()
            for ln in dig_items:
                m = SEC_NUM_RE.search(ln)
                if m:
                    dig_nums.add(m.group(1))
                if not re.search(r"—\s*\S|\s-\s+\S", ln):
                    rep.warn("digest-skipped", f"이유가 비어 있음: '{ln.strip()}' — 사용자에게 묻는다")
            raw_nums = {n for n, _, _ in raw_skipped if n}
            missing = [f"{n} {t}" for n, t, _ in raw_skipped if n and n not in dig_nums]
            if missing:
                rep.fail("skipped-sync", "절 지도에서 건너뛴 절이 '넘어간 것'에 없음: " + "; ".join(missing))
            elif raw_nums:
                rep.ok("skipped-sync", f"건너뛴 절 {len(raw_nums)}개 모두 '넘어간 것'에 있음")
            extra = sorted(dig_nums - raw_nums)
            if extra and raw_p.exists():
                rep.warn("skipped-sync", f"'넘어간 것'에는 있는데 절 지도에서 건너뜀 표시가 아닌 절: {extra}")

        _, extracted = find_section(secs, "여기서 나온 노트")
        if extracted is not None:
            links = WIKI_RE.findall(strip_non_content(extracted))
            if links:
                rep.ok("extracted", f"'여기서 나온 노트' 링크 {len(links)}개")
            else:
                rep.fail("extracted", "'여기서 나온 노트' 절에 링크가 없음 — 뺀 노트가 없으면 절 자체를 지운다")

        # 정리본 코드는 raw 코드블록 발췌만 허용한다. 줄 단위로 대조한다(앞뒤 공백 무시).
        raw_code_lines = set(code_lines(code_blocks(raw_body)))
        dig_code = code_blocks(dig_body)
        orphans = [
            (i, s)
            for i, b in enumerate(dig_code, 1)
            for s in code_lines([b])
            if not ELIDE_RE.match(s) and s not in raw_code_lines
        ]
        if orphans:
            rep.fail(
                "code",
                f"raw 코드블록에 없는 줄 {len(orphans)}개 — "
                + "; ".join(f"블록{i} `{s[:50]}`" for i, s in orphans[:5])
                + (" …" if len(orphans) > 5 else ""),
            )
        elif dig_code:
            rep.ok("code", f"코드블록 {len(dig_code)}개, 모든 줄이 raw 코드블록에 있음")
        rep.info("code", f"코드블록 {len(dig_code)}개")

        rnorm = norm(strip_non_content(raw_body))
        sents = []
        for ln in strip_non_content(dig_body).split("\n"):
            s = ln.strip()
            if not s or s.startswith("#") or re.match(r"^\s*-\s*\[\[", s):
                continue
            s = re.sub(r"^\s*[-*>]\s+", "", s)
            sents += [x for x in re.split(r"(?<=[.!?])\s+", s) if len(norm(x)) >= 15]
        hits = sum(1 for x in sents if norm(x) in rnorm) if rnorm else 0
        ratio = hits / len(sents) if sents else 0.0
        rep.info(
            "transcript",
            f"정리본 문장 {len(sents)}개 중 raw와 글자 그대로 같은 것 {hits}개 ({ratio:.0%}) — 보고용 수치",
        )

        check_links(dig_body, idx, rep, "정리본")

        if re.search(r"HUMANIZE-SUMMARY|KEEP:code|SECTION:\d", dig_text):
            rep.fail("residue", "윤문 잔재 주석(HUMANIZE-SUMMARY / KEEP / SECTION)이 남아 있음")

    # ---------------------------------------------------------------- book index
    if not bidx_p.exists():
        rep.fail("book-index", f"책 index 없음: {bidx_p}")
    else:
        bt = read(bidx_p)
        row = re.search(rf"^\|\s*{a.chapter}\s*\|.*{ch}(?![\w/])", bt, re.M)
        (rep.ok if row else rep.fail)("book-index", f"책 index 표에 {a.chapter}장 행 " + ("있음" if row else "없음"))
        check_links(bt, idx, rep, "책 index")

    return finish(rep, a)


def finish(rep, a):
    if a.json:
        print(json.dumps(rep.items, ensure_ascii=False, indent=2))
    else:
        for i in rep.items:
            print(f"[{i['level']}] {i['check']}: {i['msg']}")
        print(f"\n{'FAIL 있음' if rep.failed else 'FAIL 없음'} — PASS {rep.count('PASS')} / WARN {rep.count('WARN')} / FAIL {rep.count('FAIL')}")
    sys.exit(1 if rep.failed else 0)


if __name__ == "__main__":
    main()
