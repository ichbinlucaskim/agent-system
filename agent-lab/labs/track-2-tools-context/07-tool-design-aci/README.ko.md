# Lab 07 - Tool design and the agent-computer interface

## 목표

이 lab을 마치면 agent-computer interface를 의도적으로 설계할 수 있습니다. tool 이름을 명확히 짓고, 무엇을 하는지만이 아니라 언제 호출해야 하는지를 말하는 schema와 description을 쓰고, 에러 메시지를 복구 지침으로 바꾸고, 나쁜 description이 tool selection을 얼마나 저하시키는지 측정할 수 있습니다.

## 사전 준비

Lab 00부터 06까지, 특히 lab 01의 tool 루프. 개념: JSON Schema, 그리고 모델은 tool 정의에 넣은 것만 본다는 사실.

## 예상 소요 시간

45분에서 60분

## 배경

agent-computer interface는 agent에게 있어 사람에게의 user interface와 같으며, 같은 수준의 주의를 받을 자격이 있습니다. 많은 팀이 prompt 문구에는 며칠을 쓰면서 tool description 문구에는 몇 분을 씁니다. 정작 그 tool이 호출될지 말지를 결정하는 것은 description인데도 그렇습니다.

모델이 tool에 대해 보는 것은 정확히 세 가지입니다. 이름, description, input schema입니다. 여러분의 구현이나 docstring이나 의도는 읽을 수 없습니다. 올바른 선택에 필요한 모든 것이 그 세 필드 안에 들어 있어야 합니다.

description에서 가장 값진 문장은 대개 무엇을 하는지가 아니라 언제 호출해야 하는지를 말하는 문장입니다. `현재 재고를 조회한다`는 능력을 서술합니다. `사용자가 재고나 구매 가능 여부를 물을 때마다 호출하라. 문서에는 재고 수량이 없다`는 트리거를 서술하며, 트리거 조건은 올바른 호출 비율을 측정 가능한 수준으로 끌어올립니다.

schema는 잘못된 호출을 표현하기 어렵게 만들어야 합니다. 닫힌 집합에는 자유 문자열 대신 enum을 쓰고, 실제로 필요한 필드만 required로 두고, 모델이 문자열을 이어 붙여 만들어야 하는 값보다 절대 식별자를 선호하세요. 올바르게만 채울 수 있는 parameter 하나가 지시 한 문단보다 값집니다.

에러 메시지는 prompt입니다. tool이 실패하면 여러분이 반환하는 텍스트가 모델이 다음으로 읽는 내용이므로, 무엇이 잘못됐고 유효한 입력이 무엇인지 명시해야 합니다. `Error: invalid input`은 아무것도 가르치지 않지만, `Unknown SKU 'SKU-999'. Known SKUs are SKU-100, SKU-200, SKU-300`은 모델이 다음 turn에 스스로 호출을 고치게 해 줍니다.

이 모든 것은 측정 가능합니다. 질문 집합을 고정하고 tool description만 바꾼 뒤, 올바른 tool이 선택되는 빈도를 세세요. 그 실험이 이 lab의 핵심이며, tool 문구를 취향의 문제에서 숫자의 문제로 바꿔 줍니다.

## 단계

1. `GOOD_TOOL`과 `VAGUE_TOOL`을 작성하세요. 같은 기능이지만 하나는 트리거 조건이 담긴 description과 제약된 schema를, 다른 하나는 앙상한 description과 느슨한 schema를 갖습니다.
2. `select_tool`을 구현하세요. 주어진 tool 집합으로 모델 호출을 한 번 하고 선택된 tool 이름을 반환하되, 모델이 직접 답했으면 None을 반환합니다.
3. `selection_rate`를 구현하세요. 고정된 질문 집합에 `select_tool`을 돌리고 기대한 tool이 선택된 비율을 반환합니다.
4. `compare_descriptions`를 구현하세요. 같은 질문들을 두 tool 변형에 각각 돌리고 두 비율을 나란히 반환합니다. 이것이 실험입니다.
5. `format_tool_error`를 구현하세요. 실패를 문제와 유효한 입력을 명시하는 메시지로 바꾸고, tool 구현에서 이를 사용합니다.
6. 모호한 description에 가한 어떤 구체적 수정이 selection rate를 가장 많이 회복시켰는지 기록하세요. 그 관찰은 이후 작성하는 모든 tool에 그대로 적용됩니다.

## 검증

```bash
pytest labs/track-2-tools-context/07-tool-design-aci/tests -v
```

schema 유효성과 에러 포매팅은 오프라인으로 검사합니다. 통과했다면 두 tool 정의가 구조적으로 유효하고, 에러 메시지가 실패만 보고하지 않고 유효한 선택지를 명시하며, selection rate 산술이 정확하다는 뜻입니다. 비교 실험 자체는 API key가 필요하며 없으면 skip됩니다.

## 더 나아가기

- 첫 번째 tool과 목적이 겹치는 세 번째 tool을 추가하고 선택 정확도가 얼마나 떨어지는지 측정하세요. 겹치는 tool은 흔하면서도 피할 수 있는 실패 원인입니다.
- `get_stock_level`을 description은 그대로 둔 채 `gsl`로 이름만 바꾸고 다시 측정하세요. 이름은 대부분의 사람이 예상하는 것보다 큰 비중을 차지합니다.
- tool이 일부러 도움이 되지 않는 에러를 반환하게 하고, 모델이 복구하는 데 turn이 몇 번 더 필요한지 세어 보세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: agent-computer interface 설계: tool schema, 이름 짓기, description, 에러 설계.
- **Databricks Generative AI Engineer Associate**: tool and agent framework, evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, software development, experimentation.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
