---
keyflow_id: sys_8fdd4e4c5710
status: draft
type: ai-generated
---

# AgentPlaybook OS v26.07.6

2026-07-17

이번 릴리즈는 AgentPlaybook을 공유 규칙 모음에서 실행 수명주기와 상태를
관리하는 AgentPlaybook OS로 확장하는 기반을 정리했습니다.

## 주요 변경

- 실행 상태 레지스트리, 스케줄러, IPC, 관측성 계층을 연결했습니다.
- 병렬 워커의 상태 기록을 프로세스 간 락으로 보호하고 stale run/task 복구와
  보존 정리 경로를 추가했습니다.
- retry 대상 지정 claim, 동시 실행 중 run 전환 식별, context snapshot 갱신을
  원자화하고 멀티프로세스 회귀 테스트를 추가했습니다.
- lifecycle hook을 안정적인 `agentplaybook-hook` 런처로 통일했습니다.
- 사이트와 README의 제품 명칭을 AgentPlaybook OS로 정리하고, 시작 프롬프트가
  현재 런처와 로컬 규칙 우선 원칙을 안내하도록 갱신했습니다.

## 검증

- 전체 테스트 421개 통과
- VibeGuard 정적 감사 통과
- 동시 context snapshot/start 스트레스 검증 통과

이 릴리즈는 특정 AI 제공자에 종속되지 않는 실행 기반을 제공하며, 실제 운영
정책과 프로젝트 규칙은 각 저장소의 로컬 지침이 계속 소유합니다.
