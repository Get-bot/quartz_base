#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""humanize_io.py — 정리본 ↔ humanize-korean 사이의 분리·재조립·검증 (LLM 0콜, 결정적)

prepare : 노트에서 frontmatter를 떼고, 윤문 대상 절(주장 절)만 모아
          body_for_humanize.md 로 쓴다. 코드블록은 <!-- KEEP:code:n --> 로 치환해 보호하고,
          절마다 <!-- SECTION:i --> 마커를 앞에 붙인다.
          '이 장에서 남은 것'·'여기서 나온 노트'·'넘어간 것' 절과 HTML 주석만 있는 서문은 제외한다.
          '남은 것'은 사용자의 기억이라 윤문 대상이 아니다 — 윤문을 돌리면 쉼표·어미가 바뀐다(실측).
merge   : humanize 결과(final.md)에서 HUMANIZE-SUMMARY 블록을 떼고, 코드블록을 복원하고,
          제외했던 절·frontmatter와 원래 순서로 재조립한다. 절 단위로 구조(위키링크·H2·코드블록·
          '남은 것' 불릿 수)가 보존됐는지 검증해 어긋난 절만 원본으로 롤백한다.
          --write 면 노트를 덮어쓴다(원본은 <out-dir>/index.before.md 백업). 절 대응 자체가
          실패한 치명 오류에서는 --force 가 없는 한 덮어쓰지 않는다.

사용:
  python humanize_io.py prepare --note content/study/<book>/chNN.md --out-dir _workspace/book-digest/<book>-chNN
  python humanize_io.py merge   --out-dir _workspace/book-digest/<book>-chNN --humanized _workspace/<run_id>/final.md [--write] [--force]

exit: prepare 0 / merge 0 = 롤백 없음, 1 = 절 롤백 있음(merged.md는 유효), 2 = 치명 실패
"""
import argparse
import difflib
import json
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
# verify_digest.py 의 FENCE_RE 와 같은 펜스 규칙 — 들여쓴 펜스(불릿 안 코드블록)와 4백틱 이상 펜스도 보호한다.
CODE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[ \t]*$", re.S | re.M)
WIKI_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
KEEP_RE = re.compile(r"<!--\s*KEEP:code:(\d+)\s*-->")
SEC_MARK_RE = re.compile(r"<!--\s*SECTION:(\d+)\s*-->")
SUMMARY_RE = re.compile(r"\n*<!--\s*HUMANIZE-SUMMARY.*\Z", re.S)
BULLET_RE = re.compile(r"^\s*[-*]\s+\S", re.M)
SKIP_DEFAULT = ["이 장에서 남은 것", "여기서 나온 노트", "넘어간 것"]
LEFT_HEADING = "이 장에서 남은 것"
FIXED_HEADINGS = (LEFT_HEADING, "여기서 나온 노트", "넘어간 것")


def read(p):
    return Path(p).read_text(encoding="utf-8").replace("\r\n", "\n")


def write(p, s):
    Path(p).write_text(s, encoding="utf-8", newline="\n")


def split_fm(text):
    m = FM_RE.match(text)
    return (text[: m.end()], text[m.end():]) if m else ("", text)


def split_sections(body):
    """H2 단위 분할. 첫 H2 앞은 heading=None 서문. 코드블록 안의 '## '는 무시."""
    secs, cur, in_code = [], {"heading": None, "lines": []}, False
    for ln in body.split("\n"):
        if ln.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
        if not in_code and ln.startswith("## "):
            secs.append(cur)
            cur = {"heading": ln[3:].strip(), "lines": [ln]}
        else:
            cur["lines"].append(ln)
    secs.append(cur)
    return secs


def sec_text(sec):
    return "\n".join(sec["lines"])


def is_skip(sec, skip):
    h = sec["heading"]
    if h is None:  # 서문: HTML 주석·공백만이면 제외
        return not re.sub(r"<!--.*?-->", "", sec_text(sec), flags=re.S).strip()
    return any(h.startswith(s) for s in skip)


def h2_count(text):
    return len(re.findall(r"^## ", text, re.M))


# ---------------------------------------------------------------- prepare
def cmd_prepare(a):
    text = read(a.note)
    fm, body = split_fm(text)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    codes, parts, entries = [], [], []

    def protect(m):
        codes.append(m.group(0))
        return f"<!-- KEEP:code:{len(codes)} -->"

    for i, sec in enumerate(split_sections(body)):
        raw = sec_text(sec)
        e = {"index": i, "heading": sec["heading"], "humanize": not is_skip(sec, a.skip)}
        if e["humanize"]:
            e["original"] = raw
            parts.append(f"<!-- SECTION:{i} -->\n" + CODE_RE.sub(protect, raw).strip("\n"))
        else:
            e["text"] = raw
        entries.append(e)

    manifest = {
        "note": str(Path(a.note).resolve()),
        "frontmatter": fm,
        "sections": entries,
        "code_blocks": codes,
    }
    write(out / "body_for_humanize.md", "\n\n".join(parts) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    n = sum(1 for e in entries if e["humanize"])
    skipped = [e["heading"] or "(서문)" for e in entries if not e["humanize"]]
    print(f"prepare: 절 {len(entries)}개 중 {n}개를 윤문 대상으로 → {out / 'body_for_humanize.md'}")
    print(f"         코드블록 {len(codes)}개 보호 / 제외 절: {', '.join(skipped) if skipped else '없음'}")
    if n == 0:
        print("         윤문 대상이 없다. Phase 4를 건너뛴다.")
    return 0


# ---------------------------------------------------------------- merge
def strip_summary(t):
    return SUMMARY_RE.sub("", t).rstrip("\n") + "\n"


def split_humanized(text, targets):
    """SECTION 마커가 살아 있으면 마커로, 아니면 H2 순서로 대상 절에 대응. (chunks|None, how)"""
    if SEC_MARK_RE.search(text):
        pieces = SEC_MARK_RE.split(text)  # [pre, idx, chunk, idx, chunk, ...]
        chunks = {int(pieces[j]): pieces[j + 1].strip("\n") for j in range(1, len(pieces), 2)}
        return chunks, "SECTION 마커"
    secs = [s for s in split_sections(text) if s["heading"] is not None or sec_text(s).strip()]
    if len(secs) != len(targets):
        return None, f"마커가 사라졌고 H2 절 수도 다르다: 윤문본 {len(secs)} vs 대상 {len(targets)}"
    return {t["index"]: sec_text(s).strip("\n") for t, s in zip(targets, secs)}, "H2 순서(마커 유실)"


def verify_section(e, new, rollbacks, notes):
    """구조가 어긋나면 원본을 돌려주고 rollbacks에 사유를 남긴다."""
    old = e["original"]
    label = e["heading"] or "(서문)"

    ow = sorted(t.strip() for t in WIKI_RE.findall(old))
    nw = sorted(t.strip() for t in WIKI_RE.findall(new))
    if ow != nw:
        rollbacks.append(f"'{label}': 위키링크 타깃 변경 {ow} → {nw}")
        return old

    if e["heading"] is not None and not new.lstrip("\n").startswith("## "):
        rollbacks.append(f"'{label}': H2 제목 줄이 사라짐")
        return old
    if h2_count(old) != h2_count(new):
        rollbacks.append(f"'{label}': H2 수 {h2_count(old)} → {h2_count(new)}")
        return old

    if len(CODE_RE.findall(old)) != len(CODE_RE.findall(new)) or KEEP_RE.search(new):
        rollbacks.append(f"'{label}': 코드블록 복원 불일치")
        return old

    # 절마다 불릿 수를 보존한다. 정리본의 불릿은 그 장이 가르친 개념 목록이라
    # 문단으로 합쳐지면(humanize의 C·J 구조 카테고리) 지식베이스로서의 값이 사라진다.
    ob, nb = len(BULLET_RE.findall(old)), len(BULLET_RE.findall(new))
    if ob != nb:
        rollbacks.append(f"'{label}': 불릿 {ob} → {nb}")
        return old

    if e["heading"] is not None:
        new_h = new.lstrip("\n").split("\n", 1)[0][3:].strip()
        if new_h != e["heading"]:
            # 고정 절 제목은 이후 단계(prepare의 skip 목록, verify, 책 index 추출)가 이름으로 절을 찾는다.
            # 바뀌면 조용히 깨지므로 롤백한다. 주장 절 제목은 그 줄만 원본으로 되돌린다.
            if e["heading"].startswith(FIXED_HEADINGS):
                rollbacks.append(f"'{label}': 고정 절 제목이 '{new_h}'로 변경됨")
                return old
            # 소제목은 검색·백링크가 걸리는 문장이라 윤문이 손대면 본문만 살리고 제목 줄은 되돌린다.
            # (실측: 윤문이 주장 절 제목에서 쉼표를 지워 humanize 쪽 golden 게이트가 heading_lost FAIL을 냈다)
            new = "## " + e["heading"] + "\n" + new.lstrip("\n").partition("\n")[2]
            notes.append(f"소제목 복원: '{new_h}' → '{e['heading']}'")
    return new


def cmd_merge(a):
    out = Path(a.out_dir)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    hum = strip_summary(read(a.humanized))
    targets = [e for e in manifest["sections"] if e["humanize"]]
    codes = manifest["code_blocks"]

    fatal, rollbacks, notes = [], [], []
    chunks, how = split_humanized(hum, targets)
    if chunks is None:
        fatal.append(how)
        chunks = {}
    else:
        notes.append(f"절 대응: {how}")

    def restore(m):
        i = int(m.group(1))
        return codes[i - 1] if 0 < i <= len(codes) else m.group(0)

    rebuilt, before_parts, after_parts = [], [], []
    for e in manifest["sections"]:
        if not e["humanize"]:
            rebuilt.append(e["text"])
            continue
        new = chunks.get(e["index"])
        if new is None:
            rollbacks.append(f"'{e['heading'] or '(서문)'}': 윤문 결과에 이 절이 없음")
            new = e["original"]
        else:
            new = KEEP_RE.sub(restore, new)
            new = verify_section(e, new, rollbacks, notes)
        rebuilt.append(new)
        before_parts.append(e["original"])
        after_parts.append(new)

    body = "\n\n".join(s.strip("\n") for s in rebuilt if s.strip("\n")).strip("\n") + "\n"
    merged = manifest["frontmatter"] + ("\n" if manifest["frontmatter"] else "") + body
    write(out / "merged.md", merged)

    before, after = "\n".join(before_parts), "\n".join(after_parts)
    ratio = 1 - difflib.SequenceMatcher(None, before, after).ratio() if before else 0.0

    for n in notes:
        print("·", n)
    for r in rollbacks:
        print("!", "롤백 —", r)
    for f in fatal:
        print("!!", "치명 —", f)
    print(f"merge: 윤문 대상 {len(targets)}절 중 반영 {len(targets) - len(rollbacks)} / 롤백 {len(rollbacks)}"
          f" / 변경률(문자) {ratio:.0%} → {out / 'merged.md'}")

    if a.write:
        if fatal and not a.force:
            print("치명 실패가 있어 노트를 덮어쓰지 않았다. merged.md를 확인하고 --force 또는 수동 반영.")
        else:
            note = Path(manifest["note"])
            shutil.copy2(note, out / "index.before.md")
            write(note, merged)
            print(f"노트 덮어씀: {note} (백업 {out / 'index.before.md'})")
    return 2 if fatal else (1 if rollbacks else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--note", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--skip", action="append", default=None, help="윤문에서 제외할 절 제목(접두 일치). 반복 가능")
    m = sub.add_parser("merge")
    m.add_argument("--out-dir", required=True)
    m.add_argument("--humanized", required=True)
    m.add_argument("--write", action="store_true")
    m.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cmd == "prepare":
        if a.skip is None:
            a.skip = SKIP_DEFAULT
        sys.exit(cmd_prepare(a))
    sys.exit(cmd_merge(a))


if __name__ == "__main__":
    main()
