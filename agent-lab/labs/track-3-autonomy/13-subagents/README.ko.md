# Lab 13 - Subagents

## 목표

이 lab을 마치면 고유한 context window와 제한된 tool 집합을 가진 child agent에게 범위가 한정된 작업을 위임할 수 있고, 같은 작업에서 single agent 실행과 subagent 실행을 비교해 위임이 실제로 무엇을 치르고 무엇을 얻는지 확인할 수 있습니다.

## 사전 준비

Lab 05, 12. 개념: agent 루프, context 격리, orchestrator 패턴.

## 예상 소요 시간

45분에서 60분

## 배경

subagent는 자신만의 새 context window, 자신만의 system prompt, 그리고 부모보다 좁은 tool 집합을 가지고 실행되는 child agent입니다. 부모는 작업 설명을 건네고 보고서를 받습니다. subagent가 그 과정에서 읽은 모든 것은 그 자신의 context에 남고 부모의 context에는 들어가지 않습니다.

context 격리가 이렇게 하는 주된 이유입니다. 파일 마흔 개를 읽고 한 문단을 반환하는 검색은 부모에게 파일 마흔 개가 아니라 한 문단만큼의 비용만 남깁니다. 탐색이 다른 곳에서 일어났기 때문에 부모가 긴 실행 내내 일관성을 유지할 수 있는 것입니다.

더 좁은 tool 집합이 두 번째 이유이며 종종 더 중요한 이유입니다. 읽기만 필요한 subagent에게는 읽기 tool만 주면 되므로, 그가 읽는 문서 안의 prompt injection에는 악용할 쓰기 tool 자체가 없습니다. 구조적으로 능력을 제한하는 것이 그것을 쓰지 말라고 모델에 지시하는 것보다 낫습니다.

위임은 공짜가 아닙니다. 각 subagent는 자신의 context를 처음부터 다시 세우고 보고서를 만들며, 부모는 다시 그 보고서를 읽습니다. 부모가 tool 호출 몇 번으로 끝낼 수 있는 일이라면 그 오버헤드가 이득을 넘어서며, 정직한 답은 직접 하라는 것입니다.

쓸모 있는 형태는 진짜로 독립적인 작업에 대한 fan-out입니다. 검사할 파일 여러 개, 확인할 후보 여러 개, 참조할 출처 여러 개 같은 경우입니다. 추론의 흐름을 공유하는 순차적 작업은 부모에 남아야 합니다. 그것을 나누면 매 단계마다 인계 비용을 치르게 되기 때문입니다.

이 lab은 의견이 아니라 측정으로 끝납니다. 같은 작업을 두 방식으로 실행하고 각각의 총 token, 실제 소요 시간, 답변 품질을 기록하세요. 결과는 대개 열성적인 쪽이나 회의적인 쪽 어느 예상보다도 덜 일방적이며, 여러분의 작업에 따라 달라집니다.

## 단계

1. `SubagentSpec`을 정의하세요. 이름, system prompt, 허용된 tool 이름 리스트, step 예산을 가진 dataclass입니다.
2. `restrict_tools`를 구현하세요. spec이 허용한 tool 정의만 반환하고, 부모가 갖고 있지 않은 이름에는 예외를 던집니다. 능력은 지시가 아니라 구성으로 부여됩니다.
3. `run_subagent`를 구현하세요. spec 고유의 prompt, 제한된 tool, 그리고 부모 history가 전혀 없는 새 message 리스트로 lab 12의 agent 루프를 실행합니다.
4. `single_agent`를 구현하세요. 비교 기준선으로, 모든 tool을 가진 하나의 agent가 위임 없이 같은 작업을 해결합니다.
5. `with_subagents`를 구현하세요. 독립적인 하위 작업들로 fan-out하고 그들의 subagent를 동시에 실행하며, 부모는 보고서만 읽게 합니다.
6. `compare`를 구현하세요. 하나의 작업에 두 방식을 모두 실행하고 총 token, 실제 소요 시간, 두 답변을 나란히 반환합니다.

## 검증

```bash
pytest labs/track-3-autonomy/13-subagents/tests -v
```

tool 제한과 context 격리는 구조적 속성이며 오프라인으로 테스트됩니다. 통과했다면 subagent가 허용된 tool만 받고, 부모에게 없는 tool을 요청하면 조용히 통과하지 않고 예외가 발생하며, subagent의 message 리스트에 부모 history가 전혀 없고, `compare`가 두 방식의 token 합계를 보고한다는 뜻입니다.

## 더 나아가기

- 독립적인 두 부분으로 이루어진 작업과 엄격하게 순차적인 작업 각각에 비교를 실행하세요. 두 번째가 위임이 불리해야 하는 경우입니다.
- 모델을 겨냥한 지시가 들어 있는 문서를 subagent에게 주고, 제한된 tool 집합 덕분에 그것이 무해해지는지 확인하세요. lab 17을 미리 보는 셈입니다.
- 병렬 subagent 수를 바꿔 가며 추가된 조정 비용이 더 이상 값을 하지 못하는 지점을 찾으세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: agent 수준으로 확장된 orchestrator-workers, 설계로서의 능력 제한.
- **Databricks Generative AI Engineer Associate**: tool and agent framework, problem decomposition and solution design.
- **NVIDIA NCA Generative AI LLMs**: software development, experimentation.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
