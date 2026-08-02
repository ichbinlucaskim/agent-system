# Lab 05 - Orchestrator and workers

## 목표

이 lab을 마치면 lead 호출이 작업을 동적으로 계획하고 분해하며 worker 호출이 하위 작업을 수행하고 lead가 결과를 종합하는 workflow를 만들 수 있고, 이것이 parallelization과 어떻게 다른지 설명할 수 있습니다.

## 사전 준비

Lab 00부터 04까지. 개념: 동시성, 구조화된 출력, 그리고 고정된 계획과 생성된 계획의 구분.

## 예상 소요 시간

45분에서 60분

## 배경

이 패턴을 구분 짓는 특징은 하위 작업이 사전에 알려져 있지 않다는 점입니다. parallelization에서는 코드를 작성할 때 section을 정합니다. 여기서는 lead 호출이 작업을 읽고 하위 작업이 무엇인지 결정합니다. 그래서 주제 조사나 아직 보지 못한 파일들에 걸친 코드 변경처럼 열린 작업에 적합합니다.

그 유연성이 바로 위험을 키우는 지점이기도 합니다. 생성된 계획은 비어 있거나, 지나치게 크거나, 중복되거나, 말이 안 될 수 있습니다. 계획을 신뢰할 수 없는 입력으로 취급하세요. worker 호출에 한 푼이라도 쓰기 전에 형태를 검증하고, 하위 작업 수에 상한을 두고, 중복을 제거하고, 필수 필드가 없는 항목을 거부합니다.

worker는 좁아야 합니다. 각 worker는 하위 작업 설명과 그 작업에 필요한 context만 받아야 하며 대화 전체를 받아서는 안 됩니다. 좁은 context가 worker 호출을 저렴하게 유지하고, 한 하위 작업의 잡음이 다른 작업의 답을 오염시키지 않게 합니다.

synthesis는 이어 붙이기가 아니라 실제 단계입니다. lead는 worker 출력을 읽고 원래 작업에 대한 답을 만들어 내며, worker 사이의 모순을 해소하고 결과적으로 무관한 것으로 드러난 내용을 걷어냅니다. synthesis 단계가 그저 문자열 연결이라면 단계만 늘어난 sectioning을 만든 셈입니다.

여기서는 비용이 빠르게 증가합니다. 계획 호출 하나, worker 호출 N개, synthesis 호출 하나이며 synthesis prompt에는 모든 worker 출력이 담깁니다. worker 수에 상한을 두고, 나중에 비싼 실행을 설명할 수 있도록 계획을 결과와 함께 기록하세요.

## 단계

1. `plan`을 구현하세요. 작업을 읽고 각각 id와 설명을 가진 하위 작업 리스트를 구조화된 데이터로 반환하는 lead 호출 하나입니다.
2. `validate_plan`을 구현하세요. 필드가 빠진 항목을 거부하고, 중복을 제거하고, `max_subtasks`로 잘라냅니다. 생성된 계획은 신뢰할 수 없는 입력입니다.
3. `run_worker`를 구현하세요. 좁은 system prompt와 해당 하위 작업에 필요한 context만으로 하위 작업 하나를 수행하고, 결과와 하위 작업 id를 반환합니다.
4. `orchestrate`를 구현하세요. 계획을 세우고 검증한 뒤 상한을 둔 채 worker를 동시에 실행하고 종합합니다. 계획, worker 결과, 최종 답변을 반환합니다.
5. `synthesize`를 구현하세요. worker 출력으로 원래 작업에 답하고 그들 사이의 모순을 해소하는 마지막 lead 호출입니다.
6. worker 실패를 치명적이지 않게 만드세요. 해당 하위 작업에 에러를 기록하고, 성공한 것들로 synthesis를 계속 진행합니다.

## 검증

```bash
pytest labs/track-1-patterns/05-orchestrator-workers/tests -v
```

계획 검증과 orchestration의 control flow는 stub planner를 사용해 오프라인으로 테스트됩니다. 통과했다면 잘못된 형식의 계획이 실행되지 않고 거부되며, 하위 작업 상한이 지켜지고, 실패한 worker가 실행 전체를 중단시키지 않으며, 반환 결과에 계획이 포함되어 비싼 실행을 설명할 수 있다는 뜻입니다.

## 더 나아가기

- 같은 작업을 손으로 쓴 계획으로 lab 04의 sectioning처럼 실행하고, 생성된 계획과 품질 및 비용을 비교하세요.
- worker가 상한 내에서 하위 작업을 하나 더 요청할 수 있게 하고, 스스로 확장되는 계획이 얼마나 빨리 커지는지 관찰하세요.
- worker에 lead보다 작은 model을 주고 그것이 최종 품질에서 어떤 대가를 치르는지 측정하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: orchestrator-workers: 동적으로 분해하고 worker 출력을 종합하는 lead 호출.
- **Databricks Generative AI Engineer Associate**: problem decomposition and solution design, tool and agent framework.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, software development.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
