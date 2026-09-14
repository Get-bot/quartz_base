---
title: "[TIL-260708] Windows+WSL MySQL MCP UNC 경로 함정"
date: 2026-07-08
tags: ["MCP", "Claude Code", "WSL", "Windows", "MySQL", "트러블슈팅"]
categories: ["TIL"]
description: "Windows에서 CWD가 UNC(\\\\wsl.localhost)면 npx가 cmd.exe 때문에 못 떠 MCP가 Connection closed. wsl 래핑으로 우회. MCP 정의는 .claude.json에만."
---

## 개선점

### Windows+WSL에서 MySQL MCP가 "Connection closed"로 죽음 — UNC 경로 함정

**문제**
- `@benborla29/mcp-server-mysql`를 `.claude.json`에 등록했는데, MCP 도구 목록엔 뜨지만 `mysql_query` 하면 `Connection closed`가 났다
- DB 포트(3306)는 TCP로 도달됐다. 네트워크 문제는 아니었다

**원인**
- Claude Code가 이 MCP 서버를 CWD = `\\wsl.localhost\Ubuntu\...` (UNC 경로)로 띄운다
- Windows `npx`는 `cmd.exe`를 거치는데, cmd는 UNC를 현재 디렉터리로 못 쓴다 (`UNC paths are not supported. Defaulting to Windows directory`)
- 이 상태에서 `initialize` 핸드셰이크까진 응답하는데, `mysql_query` 호출에선 아무 응답 없이 프로세스가 끊긴다 → Claude 쪽엔 `Connection closed`로 보인다
- (별개로 DB 계정 권한 이슈도 있었음 — SUPER 등)

**액션플랜**
- `command`를 `wsl`로 감싸서 MCP 서버가 WSL 쪽에서 실행되게 해 UNC를 우회 (WSL에 node/npx 있어야 함)
- 권한 이슈는 별도 계정으로 해결

---

## 배운 점

### MCP 서버 정의는 어디에 넣나 / settings.local.json의 역할

**배움**
- MCP 서버 정의(command·env)가 들어가는 곳은 딱 두 곳: `.claude.json`의 `projects/<이 프로젝트 경로>/mcpServers`(프로젝트 전용, git에 안 올라감) 또는 글로벌 `mcpServers`
- `settings.local.json`엔 MCP 서버를 **정의할 수 없다.** 여긴 권한(permissions)과 MCP 활성/비활성 플래그(`enabledMcpjsonServers`, `disabledMcpjsonServers`)만 담는다
- 지금 설정도 이미 "현재 프로젝트 전용"이었다 — `.claude.json` 안 이 프로젝트 경로 하위에 있어서 다른 프로젝트엔 영향 없음

**의미**
- "Connection closed"를 무조건 네트워크/DB 탓으로 보지 말자. Windows+WSL 조합에선 CWD가 UNC라 실행 자체가 실패하는 경우가 있다
- `initialize`는 되는데 실제 tool 호출만 죽으면 → 서버 프로세스가 뜬 뒤 조용히 끊기는 상황을 의심

---

## 핵심 내용

### 키워드
- `MCP`, `@benborla29/mcp-server-mysql`, `UNC 경로`, `cmd.exe`, `wsl 래핑`, `.claude.json`, `settings.local.json`

### 요약
- Windows에서 프로젝트 CWD가 `\\wsl.localhost\...` UNC면 npx(cmd.exe 경유)가 못 뜬다 → MCP 서버가 initialize만 되고 query에서 죽음 → `Connection closed`
- 해결: `command`를 `wsl`로 래핑해 WSL에서 실행
- MCP 서버 정의는 `.claude.json`(projects/<경로>/mcpServers 또는 글로벌 mcpServers)에만. `settings.local.json`은 권한 + 활성/비활성 토글 전용

### 코드/명령어
```json
// .claude.json — UNC 우회를 위해 wsl로 래핑하는 형태
"mcpServers": {
  "mcp_server_mysql": {
    "command": "wsl",
    "args": ["npx", "-y", "@benborla29/mcp-server-mysql"],
    "env": { "MYSQL_HOST": "...", "MYSQL_PORT": "3306", "MYSQL_USER": "...", "MYSQL_PASS": "...", "MYSQL_DB": "..." }
  }
}
```
