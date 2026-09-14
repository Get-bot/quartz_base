---
title: AI와 일하기
description: Claude Code를 팀원처럼 쓰는 법. CLAUDE.md와 가이드로 에이전트를 조종하고, 스킬·플러그인을 고르고, 그 방식이 삐끗한 자리.
date: 2026-09-14
---

2026년부터 코드의 상당 부분을 Claude Code와 같이 씁니다. 그러자 질문이 바뀌었습니다. "어떻게 구현하지"보다 "**에이전트가 이 규칙을 지키게 하려면 문서를 어떻게 써야 하지**"를 더 자주 묻습니다. 이 폴더는 그 질문의 기록입니다. 도구 사용법이 아니라, 도구가 만든 습관과 그 습관이 실패한 지점.

## 에이전트를 조종하는 문서

- [[claude-md-router-harness-engineering|CLAUDE.md는 매뉴얼이 아니라 라우터다]] — 137줄 CLAUDE.md가 트리거 키워드로 가이드 12종을 라우팅. 가이드가 3,933줄까지 부풀었다 절반으로 줄인 일, 에이전트가 가이드를 안 읽고 추론한 일, OpenAI 하네스 엔지니어링과의 대응표
- [[ai-native-sdlc-playbook|AI-Native SDLC 플레이북 요약]] — 6단계를 산출물·게이트·지표로 압축하고, 내 PDCA·CLAUDE.md·ripgrep 셀프체크가 어디까지 왔는지 대조. "skill은 위반을 드물게, hook은 거의 불가능하게"

## 도구 고르기와 만들기

- [[claude-code-plugins-review|Claude Code 플러그인 18개 후기]] — 워크플로우 플러그인은 하나만, LSP는 내 스택만, 권한 화이트리스트는 프로젝트 시작할 때
- [[TIL-260409-claude-custom-skill-til-manager|Claude Custom Skill 개발 — TIL Manager]] — 이 지식베이스의 TIL이 만들어지는 파이프라인
- [[TIL-260412-simplify-skill-doc-dedup|스킬 문서 중복 제거와 정본화]] — 문서에도 Single Source of Truth
- [[TIL-260708-wsl-mysql-mcp-unc-path|Windows + WSL MySQL MCP UNC 경로 함정]]

## 반복해서 나오는 원칙

- 규칙은 **확인 명령**이 있어야 지켜진다. 린터가 없으면 ripgrep이라도
- skill은 위반을 드물게, hook은 거의 불가능하게 만든다. 지금 내 프로젝트엔 전자만 있다
- 도구는 시스템 프롬프트를 먹는다. 안 쓰는 플러그인은 비용이다
- 외부 라이브러리는 **해석된 실제 버전 → 공식 문서 → 블로그** 순서로 본다 ([[TIL-260420-kafka-consumer-peak-load-shifting|Spring Kafka 4.x 삽질]]에서)
- 하네스도 검증 대상이다. 가이드가 틀리면 에이전트는 틀린 걸 정확하게 따른다

## 연결되는 곳

- 설계 문서를 먼저 쓰는 PDCA는 [[workflow/index|일하는 방식]]에 있습니다. bkit 플러그인으로 돌리지만 방법론 자체는 AI가 없어도 성립해서 따로 두었습니다

## 다음에 채울 자리

- 테스트 파일 편집 차단 hook 하나. 플레이북에서 가장 싸고 효과가 큰 것
- eval 5개. CLAUDE.md를 고칠 때 실제로 나아졌는지 숫자로 재기
