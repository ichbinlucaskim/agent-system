# Lab 01 - The augmented LLM

## 목표

이 lab을 마치면 이후 모든 lab이 재사용하는 기본 building block을 만들 수 있습니다. 즉 retrieval, tool, memory로 확장된 모델 호출과 이를 구동하는 tool use 루프입니다.

## 사전 준비

Lab 00. 개념: Messages API 요청과 응답의 형태, content block, system prompt.

## 예상 소요 시간

30분에서 45분

## 배경

Anthropic의 Building Effective Agents에서 augmented LLM은 기본 building block입니다. 이 과정 이후에 나오는 모든 workflow와 모든 agent가 이 형태의 호출로 구성됩니다. 한 번 제대로 만들어 두면 나머지 과정은 재발명이 아니라 조합이 됩니다.

retrieval은 모델이 갖고 있지 않은 사실을 prompt에 넣는 일입니다. 검색된 각 구절에 출처 id를 붙여서 답변이 이를 인용할 수 있게 하고, 읽는 사람이 어떤 주장이 근거를 갖는지 판별할 수 있게 하세요. 관련 없는 텍스트로 context를 채우는 retrieval은 retrieval이 없느니만 못합니다. token을 소모하고 모델이 주어진 내용을 쓰도록 유도하기 때문입니다.

tool은 schema로 기술된 행동입니다. 모델은 아무것도 직접 실행하지 않습니다. tool 이름과 인자를 담은 `tool_use` block을 내보내면, 여러분의 코드가 그 행동을 수행하고 `tool_result`를 돌려줍니다. 이 분리가 곧 보안 경계 전체이며, lab 14에서 그 사이에 approval gate를 넣을 수 있는 이유이기도 합니다.

retrieval과 tool은 서로 다른 질문에 답합니다. 문서는 작성된 시점에 참이었던 내용을 담습니다. tool은 지금 참인 값을 읽습니다. 재고 수량, 계좌 잔액, 오늘 날짜는 tool 뒤에 있어야 하며, tool description에 그 점을 명시해야 합니다. 그렇지 않으면 모델이 문서를 근거로 답해 버립니다.

API는 stateless이므로 memory는 여러분이 다시 보내기로 선택한 history일 뿐입니다. 따라서 memory는 보관소가 아니라 예산입니다. 이 lab에서는 고정된 turn 수로 잘라내고, lab 11에서 잘라내기를 compaction으로 대체합니다.

루프는 `stop_reason`으로 구동됩니다. 값이 `tool_use`인 동안 응답에 담긴 모든 `tool_use` block을 실행하고, 하나의 user message 안에 `tool_use` id마다 하나씩 대응하는 모든 결과를 담아 반환합니다. 결과를 여러 message로 나누거나 하나를 빠뜨리면 프로토콜 위반입니다. 혼란에 빠진 모델이 무한히 돌지 않도록 최대 라운드 수로 루프를 제한하세요.

## 단계

1. `tokenize`와 `retrieve`를 구현하세요. 각 문서를 질의와의 token 겹침으로 점수화하고, 겹치는 것이 없는 문서는 버리고, 상위 k개를 결정적인 순서로 반환합니다.
2. `build_system`을 구현하세요. 규칙을 먼저 쓰고, 검색된 각 문서를 `[id] text` 형태로 나열합니다. 모델에게 id를 인용하도록, 그리고 근거가 없으면 모른다고 말하도록 지시하세요.
3. `Memory.add`와 `Memory.messages`를 구현하세요. 가장 최근 `max_turns`개 항목만 유지하고, 호출자가 받은 리스트를 수정해 memory를 바꾸지 못하도록 복사본을 반환합니다.
4. `run_tool`을 구현하세요. `INVENTORY`에서 SKU를 조회합니다. 에러는 예외를 던지지 말고 `(text, True)`로 반환하며, 모델이 다음 turn에 복구할 수 있도록 에러 메시지에 유효한 선택지를 명시하세요.
5. `augmented_call`을 구현하세요. retrieval을 수행하고 system prompt를 만들고 질문을 기록한 뒤 루프를 돕니다. 모델을 호출하고 그 content를 append하며, `stop_reason`이 `tool_use`인 동안 모든 block을 실행해 하나의 user message에 모든 결과를 담아 반환합니다. 답변을 memory에 기록하고 반환하세요.
6. `main`을 구현하세요. 공유 `Memory`를 사용해 corpus가 답할 수 있는 질문 하나와 tool만 답할 수 있는 재고 질문 하나를 물어봅니다.

## 검증

```bash
pytest labs/track-1-patterns/01-augmented-llm/tests -v
```

retrieval, memory, tool dispatch는 결정적이므로 해당 테스트는 오프라인으로 실행되며 API key 없이도 통과해야 합니다. end-to-end 테스트 두 개는 key가 없으면 skip됩니다. 통과했다면 모델이 검색된 문서로 정책 질문에 답했고, 재고 질문에서는 추측하지 않고 tool을 사용했다는 뜻입니다.

## 더 나아가기

- `get_stock_level`의 description을 `Get stock.` 정도로 약화시키고 재고 질문을 다시 실행하세요. lab 07에서는 이 관찰을 측정으로 바꿉니다.
- 첫 번째 tool과 기능이 겹치는 두 번째 tool을 추가하고 모델이 어느 쪽을 선택하는지 보세요.
- token 겹침 기반 retrieval을 lab 08의 vector store로 교체하고 같은 질문에 어떤 문서가 돌아오는지 비교하세요.
- `main`을 실행하고 두 번째 답변을 자세히 읽어 보세요. 모델이 첫 답변에서 한 말을 철회한다면, 두 번째 질문에 대해 retrieval이 무엇을 반환했는지 확인하세요. system prompt는 호출마다 현재 질문으로 새로 만들어지는데 memory는 누적되므로, 어떤 답변이 그것을 뒷받침한 문서보다 오래 남을 수 있습니다. 이 문제는 lab 11에서 다룹니다.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: augmented LLM building block, 그리고 agent-computer interface로서의 tool use.
- **Databricks Generative AI Engineer Associate**: RAG 및 LLM chain을 포함한 application development, tool and agent framework.
- **NVIDIA NCA Generative AI LLMs**: LLM integration and deployment, prompt engineering.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
