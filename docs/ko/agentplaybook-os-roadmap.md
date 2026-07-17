---
keyflow_id: docs_ko_agentplaybook_os_roadmap
status: draft
type: planning
---

# AgentPlaybook OS 발전 계획

## 방향

AgentPlaybook은 에이전트에게 작업 방법을 알려주는 플레이북을 넘어, 에이전트가 일하는 실행 환경을 관리하는 운영 계층으로 발전한다.

`AgentPlaybook OS`라는 이름은 내부 플랫폼 명칭으로 사용할 수 있다. 다만 완성된 운영체제라고 주장하려면 에이전트의 생명주기, 스케줄링, 컨텍스트, 권한, 통신, 복구를 실제로 책임져야 한다.

## 현재 갖춘 기반

- 라우팅, preflight, 문서 manifest, 검증 gate: 실행 control plane
- execution capsule과 handoff: 작업 컨텍스트 전달
- dispatch와 parallel worker: 초기 작업 분배
- Codex·Claude·Antigravity runtime bridge: 실행기 어댑터
- retry와 finish evidence: 기본 복구와 감사 흐름

## 첫 수직 슬라이스 구현 상태

Agent Kernel의 최소 실행 registry를 추가했다. 각 start hook은 로컬
`.agentplaybook/run-registry.json`에 실행을 `running`으로 등록하고, finish
hook은 같은 preflight evidence에 연결된 최신 실행을 `completed` 또는
`failed`로 전환한다. registry에는 요청 원문이나 로컬 파일 경로를 저장하지
않고 opaque project/run ID, route/request fingerprint, 상태와 시각만 남긴다.

이 registry는 이후 scheduler의 실행 큐, 복구의 stale-run 탐지,
observability의 상태 조회가 공유할 최소 기반이다.

Scheduler의 첫 조각으로 content-free 작업 큐와 capacity 선택기를 추가했다.
작업은 우선순위에 따라 claim되고, 독립 범위가 2개 미만이면 항상 직렬
capacity 1을 사용한다. 독립 범위가 충분한 경우에도 capacity는 2~3개로
제한한다. 이 큐는 아직 runtime worker를 직접 실행하지 않으며, 다음 단계에서
dispatch와 연결한다.

이후 연결 작업에서 다음 기반도 추가했다.

- `agent_capability_policy.py`: read-only/workspace-write capability와
  isolated filesystem 정책
- `agent_ipc.py`: 요청 내용 없이 run/task 상태 이벤트를 남기는 로컬 event
  channel
- `agent_observability.py`: active run, task count, event count를 반환하는
  집계형 status snapshot

Scheduler는 delegated worker launch 직전에 task를 enqueue·claim하고,
worker 종료 코드에 따라 completed/failed로 전환한다. 실제 runtime dispatch
경로와 registry·event channel·status snapshot이 연결된 상태다. stale-run
재개를 위한 stale-run 감지·실패 전환·resume primitive도 추가했다. 상태
조회는 `scripts/agent-os-status.py --project <repo>`로 확인할 수 있다.
세부 운영 환경에 맞춘 보존 기간 튜닝과 자동 재시작 정책 확장은 다음 hardening 단계로 남긴다.

## 운영 hardening 상태

- `retry_task`와 dispatch 재시도 루프로 bounded retry/restart를 제공한다.
- `recover_stale_runs`와 `resume_run`으로 stale 실행을 실패 처리한 뒤 재개할 수 있다.
- `agent_retention.py`와 `agent-os-maintenance.py`가 terminal run/task/event의
  보존 기간과 최대 기록 수를 제한한다.
- retention의 `max_records`는 terminal history에만 적용하며 active run/task는
  실행 중이라는 이유로 삭제하지 않는다.
- bounded retry는 재시도 task를 대상으로 원자적으로 claim해 다른 queued task가
  재시도 슬롯을 가로채지 않도록 한다.
- maintenance CLI는 오래된 queued/running task를 failed로 복구한 뒤 retry
  budget이 남아 있는 task만 다시 queued로 전환한다.
- status snapshot에 `api_version`과 생성 시각을 추가해 외부 소비자가 계약을
  식별할 수 있게 했다.
- registry·scheduler·event의 read-modify-write 구간에 프로세스 간 lock을
  적용해 병렬 worker의 lost update와 capacity 초과 claim을 방지한다.
- multiprocessing 회귀 테스트로 동시 run 등록, event 기록, serial claim의
  보존과 capacity bound를 검증한다.
- capability profile은 runtime `sandbox_mode`와 filesystem 격리 수준을
  `isolation_mode`로 분리해, workspace-write runtime과 isolated-write 경계를
  문서·검증에서 혼동하지 않도록 한다.

운영 환경에 맞춘 실제 보존 기간과 retry 횟수는 maintenance CLI 인자로
설정하며, 기본값은 보수적인 bounded 값으로 유지한다.

## 추가해야 할 계층

### 1. Agent Kernel

에이전트 실행을 하나의 표준 상태 모델로 관리한다.

- `run`, `task`, `worker`, `capsule` 생명주기 정의
- 실행 상태 저장소와 실행 ID
- `start`, `running`, `paused`, `failed`, `completed` 상태
- 중복 실행과 stale 실행 정리
- 부모-자식 실행 관계 관리

완료 기준: 어떤 에이전트가 어떤 작업을 수행 중인지 조회할 수 있고, 중단된 실행을 식별할 수 있다.

### 2. Scheduler

현재의 병렬 dispatch를 실제 작업 스케줄러로 발전시킨다.

- 작업 큐와 우선순위
- 동시 실행 수와 리소스 한도
- 작은 작업의 직렬 실행
- 독립 범위가 있을 때만 worker 분배
- worker 취소, timeout, 재시도
- runtime·모델별 capacity 관리

완료 기준: 에이전트를 많이 띄우는 것이 아니라, 작업 성격에 맞게 필요한 실행만 자동 선택한다.

### 3. Context File System

문서와 규칙을 에이전트가 사용하는 일관된 컨텍스트 자원으로 관리한다.

- 프로젝트·규칙·작업·worker 컨텍스트 분리
- 문서 manifest와 fingerprint
- capsule에 request fingerprint 연결
- 변경 문서만 증분 반영
- 오래된 capsule 자동 무효화
- 문서 읽기 범위와 source-of-truth 구분

완료 기준: 부모와 worker가 같은 근거 묶음을 사용하고, stale 문서나 capsule을 재사용하지 않는다.

### 4. Capability와 Sandbox

작업별 권한을 명시적인 capability 모델로 만든다.

- read-only, workspace-write, isolated-write 프로파일
- 파일·네트워크·child agent 권한
- analysis 작업의 non-authoring 보장
- runtime별 권한 매핑
- 권한 상승 승인과 감사 기록
- 위험 작업 차단 정책

완료 기준: 작업 종류와 runtime이 달라도 허용된 자원 밖의 변경을 수행할 수 없다.

### 5. IPC와 복구

부모·worker·runtime 사이의 통신과 재개를 표준화한다.

- handoff, result, failure 이벤트 형식
- worker heartbeat
- timeout과 cancellation
- 중단된 작업 재개
- partial result 저장
- retry 시 기존 결과와 근거 재사용

완료 기준: worker가 중단되어도 전체 작업을 처음부터 반복하지 않고 안전하게 재개할 수 있다.

### 6. Observability와 표준 API

AI provider가 바뀌어도 같은 운영 계약을 유지한다.

- 실행 상태 조회 CLI와 대시보드
- task·worker·gate audit log
- runtime-neutral task API
- Codex·Claude·Antigravity adapter contract
- versioned task, capsule, evidence schema
- provider와 plugin 확장 규칙

완료 기준: 어떤 AI를 사용해도 같은 입력 계약, 실행 상태, 검증 결과, 출력 형식을 얻는다.

## 권장 구현 순서

1. 실행 상태 모델과 영속 registry
2. scheduler와 worker lifecycle
3. context/capsule 수명주기
4. capability와 sandbox 권한 모델
5. IPC와 복구
6. observability와 외부 API

각 단계는 독립 기능보다 공통 실행 계약과 검증 시나리오를 먼저 정의한 뒤 구현한다.

## OS 명칭을 사용할 시점

내부적으로는 지금부터 `AgentPlaybook OS`를 사용해도 된다. 외부에서 “에이전트 운영체제”라고 강하게 소개하려면 최소한 Agent Kernel, Scheduler, Context File System, Capability/Sandbox까지 구현한 뒤가 적절하다.

그 전까지의 공식 표현은 다음이 안전하다.

> AgentPlaybook OS — 에이전트 실행을 위한 운영 계층
