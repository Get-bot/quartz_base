---
title: "[TIL-260911] MCP stdio 서버의 stdout은 프로토콜 채널이다"
date: 2026-09-11
tags: ["mcp", "nodejs", "json-rpc", "claude-code", "troubleshooting"]
categories: ["TIL"]
description: "console.log 한 줄이 JSON-RPC를 깨뜨린다. globalThis.console을 stderr 바인딩 Console로 교체하고, 전송 계층엔 진짜 stdout writer를 따로 쥐어주는 3단 순서"
---

## 잘한 점

### console 인스턴스를 통째로 갈아끼워 stdout 오염 경로를 한 번에 닫음

**상황**
- MCP stdio 서버는 stdout이 JSON-RPC 전용 채널이다. 여기에 한 바이트라도 딴 게 섞이면 클라이언트가 프레임을 못 읽는다
- 문제는 내 코드만 조심한다고 되는 게 아니라는 것 — 의존성이 어딘가에서 `console.log`를 찍으면 그대로 프로토콜이 깨진다
- 처음엔 `console.log`/`console.info` 정도만 stderr로 돌리면 될 줄 알았다

**액션**
- 메서드를 하나씩 rebind하는 대신 `globalThis.console`을 `new Console({ stdout: process.stderr, stderr: process.stderr })`로 교체했다
- 이러면 `log`·`info`·`debug`·`dir`만이 아니라 `table`·`group`·`groupCollapsed`·`groupEnd`·`count`·`countReset`·`time`·`timeEnd`·`timeLog`까지 한 번에 닫힌다. 이것들 전부 Node에서 stdout으로 나간다
- 서버 모드에서만 설치한다. `doctor`, `host add`, `--version`은 stdout에 찍는 게 정상인 CLI라 가드를 안 깐다

**칭찬**
- 메서드 목록을 세는 대신 클래스를 갈아끼운 판단. 세는 쪽을 골랐으면 `console.countReset` 같은 건 100% 빠뜨렸을 거고, Node가 메서드를 하나 더 추가하면 그때 또 샌다
- "console 몇 개 막으면 되겠지"에서 멈추지 않고 어디까지 stdout으로 나가는지 실제로 확인한 것

---

## 개선점

### process.stdout.write를 막았더니 서버 응답까지 같이 막혔다

**문제**
- console만으로는 불안해서 `process.stdout.write` 자체를 감쌌다
- 그랬더니 서버가 응답을 아예 못 보냈다. 로그는 깨끗한데 클라이언트 쪽에서 아무것도 안 온다

**원인**
- `StdioServerTransport`가 바로 그 `process.stdout.write`의 **정당한 호출자**였다. 내부에서 `this._stdout.write(json)`을 부르고 `_stdout`의 기본값이 `process.stdout`이다
- 내가 깐 가드가 JSON-RPC 프레임까지 같이 stderr로 보내고 있었다. 오염을 막으려던 가드가 프로토콜을 막은 셈

**액션플랜**
- `captureProcessStdout()`을 옵트인으로 두고 기본 off로 바꿨다. 이걸 켜려면 전송 계층에 진짜 writer를 따로 쥐어줘야 한다
- `protocolStdoutStream()`이 원본 `write`를 클로저로 잡은 `Writable`을 돌려준다. 가드가 안 깔린 상태에서도 그냥 `process.stdout`으로 통과하므로 조건 없이 써도 된다
- 순서가 곧 계약이라 `src/AGENTS.md`에 "이 순서를 바꾸면 서버 응답 자체가 stderr로 새어 나갑니다"라고 박아뒀다. 코드만 봐서는 세 줄의 순서가 왜 중요한지 안 보인다

---

## 배운 점

### 가드는 "무엇을 막는가"보다 "어느 층에 놓는가"

**배움**
- 같은 stdout인데 내 로그와 프로토콜 프레임이 섞여 흐른다. 둘을 나누는 기준은 채널이 아니라 **층**이다 — 애플리케이션 층(console)은 막고 전송 층(transport)은 열어둬야 한다
- "더 낮은 층에서 막을수록 안전하다"가 항상 참이 아니다. `process.stdout.write`는 내 코드와 SDK가 공유하는 지점이라, 거기서 막으면 남의 정당한 사용까지 막힌다
- 진짜 writer를 미리 확보해두는 패턴이 핵심이다. 가드를 깔기 **전에** 원본 참조를 떼어놓지 않으면 되돌릴 방법이 없다

**의미**
- 전역을 건드리는 코드는 순서에 의존하는데, 그 순서가 타입이나 시그니처로는 안 드러난다. 주석이나 AGENTS.md 같은 데 명시적으로 남겨야 6개월 뒤의 내가 안 깨뜨린다
- MCP 서버를 또 만들면 기동 첫 줄이 이 가드가 될 거다. 이번엔 깨져보고 알았지만 다음엔 처음부터 깔고 시작하자

---

## 핵심 내용

### 키워드
- `MCP stdio transport`, `JSON-RPC`, `globalThis.console` 교체, `StdioServerTransport`, `Writable`

### 요약
- MCP stdio 서버에서 stdout은 JSON-RPC 전용이다. `console.*`는 전부 stderr로 보내야 하고, 개별 메서드 rebind 대신 `new Console({ stdout: process.stderr, stderr: process.stderr })`로 전역 console을 교체하면 `table`/`group`/`count`/`timeEnd` 계열까지 한 번에 닫힌다.
- `process.stdout.write`를 감싸는 건 별개 문제다. `StdioServerTransport`가 그 함수로 프레임을 보내므로, 감싸기 전에 원본 writer를 확보해 전송 계층에 넘겨야 한다.
- 순서는 `installStdoutGuard()` → `protocolStdoutStream()` → `captureProcessStdout()` → `server.connect()`. 2번과 3번이 뒤바뀌면 응답이 stderr로 샌다.
- 가드는 서버 모드에만 건다. stdout에 찍는 게 정상인 CLI 경로(`doctor`, `--version`)에는 걸지 않는다.

### 코드/명령어
```ts
// 서버 모드 기동 — 이 순서가 계약이다
installStdoutGuard();                       // console → stderr
const protocolStdout = protocolStdoutStream(); // 진짜 writer를 먼저 확보
captureProcessStdout();                     // 이제 process.stdout.write를 막아도 안전
const transport = new StdioServerTransport(process.stdin, protocolStdout);
await server.connect(transport);
```

```ts
// 가드 본체 — 메서드를 세지 않고 클래스를 교체한다
export function installStdoutGuard(): void {
  if (guardState !== null) return;
  const previousConsole = globalThis.console;
  globalThis.console = new Console({ stdout: process.stderr, stderr: process.stderr });
  guardState = { previousConsole, originalStdoutWrite: null };
}
```

```ts
// 전송 계층 전용 통로 — 원본 write를 클로저로 들고 있는다
export function protocolStdoutStream(): Writable {
  return new Writable({
    write(chunk, encoding, callback) {
      const write = guardState?.originalStdoutWrite ?? process.stdout.write.bind(process.stdout);
      write(chunk, encoding);
      callback();
    },
  });
}
```

### 참고 자료
- MCP stdio transport 스펙: https://modelcontextprotocol.io/docs/concepts/transports
- Node.js `Console` 클래스 (stdout/stderr 주입): https://nodejs.org/api/console.html#new-consolestdout-stderr-ignoreerrors
