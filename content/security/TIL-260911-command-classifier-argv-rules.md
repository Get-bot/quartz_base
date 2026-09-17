---
title: "[TIL-260911] 정규식은 argv의 위치를 모른다 — 명령 분류기를 위치 규칙으로 옮긴 이유"
date: 2026-09-11
tags: ["security", "mcp", "ssh", "parsing", "path-traversal"]
categories: ["TIL"]
description: "cp /dev/null /etc/passwd는 정규식으로 못 잡는다. 출발지와 목적지를 구분하려면 argv 위치를 봐야 한다. 진단 출력과 경로 검사까지 이어진 이야기"
---

## 잘한 점

### 정규식으로 안 되는 판정을 argv 위치 규칙 13개로 옮김

**상황**
- ssh-mcp는 SSH로 보낼 명령을 safe / privileged / destructive로 등급 매기고, 등급에 따라 사람 승인을 요구한다
- 명령을 만들어 보내는 쪽이 사람이 아니라 모델이라, "실수로 위험한 걸 보낸다"가 아니라 **우회를 전제로** 설계해야 한다
- 그때까지 분류는 정규식 패턴 표 하나였다

**액션**
- 정규식이 구조적으로 못 하는 판정을 argv 위치 규칙으로 이전했다. 대표 사례가 `cp /dev/null /etc/passwd` — 정규식은 `/etc/passwd`가 **출발지인지 목적지인지** 모른다. `move-to-system` 규칙은 `cp`·`mv`·`install`·`ln`의 목적지 argv만 본다
- `rm`은 플래그가 어떻게 보이든 프로그램 이름이 `rm`이면 destructive로 잡는다. `rm -- <path>`처럼 `--` 뒤로 숨기는 형태가 정규식에서 새고 있었다
- 래퍼도 벗긴다. `busybox rm -rf /`, `sudo busybox rm -rf /srv`, `pkexec rm -rf /srv` 전부 `destructive:rm-command`로 떨어진다
- 인용 우회는 normalize 단계에서 접는다. `'rm'`, `"rm"`, `r""m`, `r\m`이 전부 같은 `rm`이 된다
- 우회 코퍼스 104개 / 안전 코퍼스 71개 / 관리자 26개로 회귀를 고정했다 (테스트가 최소 60·60·12를 단언한다)

**칭찬**
- 막는 쪽만이 아니라 **오탐도 같은 강도로** 잡은 것. `git push --force-with-lease`, `iptables -L`, `mount`를 안전으로 되돌리고, `>>` append는 시스템 경로일 때만 파괴적으로 좁혔다
- 안전 코퍼스를 우회 코퍼스와 비슷한 크기로 유지한 것도 의식적인 선택이었다. 오탐이 쌓이면 사람이 결국 게이트를 꺼버리니까, 그쪽이 더 위험하다

---

## 개선점

### 진단 도구가 정규식 표만 보여주면 "이 표를 지우면 안전해진다"로 읽힌다

**문제**
- `ssh-mcp doctor --patterns`가 정규식 패턴 표만 출력하고 있었다
- 그 출력만 본 운영자는 `rm-*` 패턴을 전부 지우면 `rm -rf /`가 안전으로 판정된다고 결론 낼 수 있다. 실제로는 argv 규칙이 잡으니 그렇게 안 되는데, 출력 어디에도 그 사실이 없었다

**원인**
- 분류 경로가 정규식과 argv 규칙 둘인데 진단 출력은 하나만 비췄다
- argv 규칙은 정규식이 없어서 "출력할 게 없다"고 넘어간 게 컸다. 근데 정작 그것들이 **끌 수 없는 규칙**이라 더 중요했다

**액션플랜**
- `ARGV_RULES` 표를 `doctor --patterns` 출력에 추가하고 해제 불가를 명시했다. `--json`에는 `argvRules` 배열로 나가고 카운트도 분리했다
- doctor 항목 14를 새로 넣었다. `missingCorePatterns()`가 비지 않으면 FAIL — 빌드나 호스트별 override가 핵심 파괴 패턴 17개 중 하나라도 빠뜨리면 즉시 보이게 했다
- 핵심 패턴은 `remove` 지시를 무시하고 warn만 남긴다. 비핵심 패턴만 remove로 매칭이 끊긴다

---

## 배운 점

### 문자열 검사와 구조 검사 — 경로에서도 똑같은 함정을 만났다

**배움**
- 분류기를 통과해도 파일 경로로 뚫린다. 업로드/다운로드의 `local_path`가 `~/.ssh-mcp` 안을 가리키면 모델이 `hosts.json`·개인키·감사 로그를 덮어써서 안전장치 자체를 무력화할 수 있다
- 막으려고 `path.resolve`부터 썼는데 이게 함정이었다. `path.resolve`는 `..`를 **문자열 수준에서** 접는다. `/tmp/link/../hosts.json`은 lexical로는 `/tmp/hosts.json`이지만, `link`가 심링크면 실제로는 전혀 다른 데 떨어진다
- `realpathSync`로 디렉터리를 풀고 basename을 다시 붙여야 한다. 아직 존재하지 않는 다운로드 대상 때문에 가장 가까운 존재하는 조상까지 거슬러 올라가 푸는 처리도 필요했다
- 정규식이 argv 위치를 모르는 것과 `path.resolve`가 심링크를 모르는 것이 정확히 같은 종류의 실수다. 둘 다 **문자를 보고 구조를 봤다고 착각**한 것

**의미**
- 입력을 검사하는 코드를 볼 때마다 물어볼 질문이 생겼다 — 이 검사는 구조를 보는가, 아니면 문자를 보는가
- 방어를 한 겹에 몰지 말자. 분류기가 뚫려도 경로 봉쇄가 남고, 경로가 뚫려도 승인 게이트가 남는 배치가 맞다
- 안전장치를 검사하는 도구(doctor)도 안전장치다. 그게 반쪽만 보여주면 사람이 잘못된 결론을 내린다

---

## 핵심 내용

### 키워드
- `argv 위치 규칙`, `셸 정규화(normalize)`, `우회 코퍼스`, `realpath vs path.resolve`, `defense in depth`

### 요약
- 명령 등급 판정은 문자열 매칭이 아니라 **argv 파싱 + 위치 규칙** 문제다. 정규식은 토큰이 몇 번째 인자인지 모르므로 출발지와 목적지를 구분할 수 없다 (`cp /dev/null /etc/passwd`).
- 래퍼(`busybox`, `sudo`, `pkexec`, `su -c`)와 인용 우회(`'rm'`, `r""m`, `r\m`)는 분류 **전에** normalize 단계에서 접는다. 분류기는 정규화된 argv만 본다.
- 우회 코퍼스만 키우면 오탐이 늘고, 오탐이 늘면 사람이 게이트를 끈다. 안전 코퍼스를 비슷한 크기로 같이 유지해야 한다 (104 / 71 / 26).
- 끌 수 있는 규칙과 끌 수 없는 규칙을 진단 출력에서 구분해 보여줘야 한다. 안 그러면 "패턴을 지우면 통과한다"는 오해가 생긴다.
- `path.resolve`는 `..`를 lexical로 접기 때문에 심링크 우회를 못 막는다. 경로 봉쇄는 `realpathSync` 기준으로 해야 한다.

### 코드/명령어
```ts
// argv 위치 규칙 — 정규식이 없고, 끌 수도 없다
argvRule('destructive', 'rm-command',
  'the program is rm, whatever the flags look like (covers rm -- <path>)');
argvRule('destructive', 'move-to-system',
  'the destination of cp, mv, install or ln is a system path or a home dotfile');
argvRule('destructive', 'interpreter-substitution',
  'an interpreter was handed a process substitution, e.g. bash <(curl ...)');
```

```ts
// path.resolve만으로는 부족하다: '..'를 lexical로 접으므로
// /tmp/link/../hosts.json 이 link를 따라가면 다른 곳에 떨어진다
export function realResolve(target: string): string {
  const absolute = path.resolve(target);
  const parts = [path.basename(absolute)];
  let current = path.dirname(absolute);
  for (;;) {
    try {
      return path.resolve(fs.realpathSync(current), ...parts.reverse());
    } catch {
      const parent = path.dirname(current);      // 아직 없는 경로(download 대상)면
      if (parent === current) return absolute;   // 존재하는 조상까지 올라간다
      parts.push(path.basename(current));
      current = parent;
    }
  }
}
```

```bash
# 끌 수 있는 규칙과 없는 규칙을 같이 보여준다
ssh-mcp doctor --patterns
ssh-mcp doctor --patterns --json   # patterns[] 와 argvRules[] 가 분리되어 나온다
```

### 참고 자료
- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- Node.js `fs.realpathSync`: https://nodejs.org/api/fs.html#fsrealpathsyncpath-options
