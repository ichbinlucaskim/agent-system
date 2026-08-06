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

그 실험에는 경쟁하는 tool이 필요합니다. tool이 하나뿐이면 선택이랄 것이 없습니다. 모델은 질문이 그 tool과 어렴풋이 관련되기만 하면 호출하고, `재고를 조회한다` 한 마디짜리 description도 만점을 받습니다. 이름을 뭉개도 마찬가지입니다. 두 번째 tool을 놓아 두면 실패가 드러나는데, 그 양상은 대개 예상과 반대입니다. 앙상한 description의 피해는 tool이 호출되지 않는 것이 아니라 **아무 데나 호출되는 것**입니다. `재고를 조회한다`는 이 tool이 무엇을 위한 것이 아닌지를 말하지 않으므로, 모델은 재질이나 세척법을 묻는 질문까지 여기로 끌어옵니다. description에서 경계를 그리는 문장이 값진 이유가 이것입니다.

그리고 schema는 제약이면서 동시에 설명입니다. 모델은 enum 값과 필드 description을 읽고 이 tool이 무엇에 관한 것인지 판단하므로, schema를 조이면 인자 품질만이 아니라 선택률도 함께 올라갑니다. 이 lab의 측정에서는 문구를 고치는 것과 schema를 고치는 것이 각각 비슷한 크기로 기여했습니다.

## 단계

1. tool 정의들을 작성하세요. 재고 tool이 경쟁할 상대인 `DOCS_TOOL` 하나, 그리고 같은 이름을 공유하는 재고 tool 변형 넷입니다. `GOOD_TOOL`은 트리거 조건이 담긴 description과 제약된 schema를, `VAGUE_TOOL`은 앙상한 description과 느슨한 schema를 갖습니다. `TRIGGER_ONLY_TOOL`과 `SCHEMA_ONLY_TOOL`은 각각 한 필드만 고쳐서, 어느 변화가 무엇을 회복시켰는지 나눠 볼 수 있게 합니다. `CASES`는 두 tool의 경계에 놓인 질문들로 채우세요.
2. `select_tool`을 구현하세요. 주어진 tool 집합으로 모델 호출을 한 번 하고 선택된 tool 이름을 반환하되, 모델이 직접 답했으면 None을 반환합니다.
3. `selection_rate`를 구현하세요. 고정된 질문 집합에 `select_tool`을 돌리고 기대한 tool이 선택된 비율을 반환합니다. 케이스들은 서로 독립이므로 lab 04에서처럼 동시에 실행하세요.
4. `compare_descriptions`를 구현하세요. 질문들과 경쟁 tool은 고정하고 재고 tool만 바꿔서 네 비율을 나란히 반환합니다. 이것이 실험입니다.
5. `format_tool_error`를 구현하세요. 실패를 문제와 유효한 입력을 명시하는 메시지로 바꾸고, tool 구현에서 이를 사용합니다.
6. 어떤 구체적 수정이 selection rate를 가장 많이 회복시켰는지 기록하세요. 네 비율을 뺄셈하면 문구의 몫과 schema의 몫이 각각 나옵니다. 그 관찰은 이후 작성하는 모든 tool에 그대로 적용됩니다.

## 검증

```bash
pytest labs/track-2-tools-context/07-tool-design-aci/tests -v
```

schema 유효성과 에러 포매팅은 오프라인으로 검사합니다. 통과했다면 모든 tool 정의가 구조적으로 유효하고, 중간 변형들이 각각 한 필드만 다르며, 케이스 집합이 두 tool을 실제로 경쟁시키고, 에러 메시지가 실패만 보고하지 않고 유효한 선택지를 명시하며, selection rate 산술이 정확하다는 뜻입니다. 비교 실험 자체는 API key가 필요하며 없으면 skip됩니다.

## 더 나아가기

- 첫 번째 tool과 목적이 겹치는 세 번째 tool을 추가하고 선택 정확도가 얼마나 떨어지는지 측정하세요. 겹치는 tool은 흔하면서도 피할 수 있는 실패 원인입니다.
- `get_stock_level`을 description은 그대로 둔 채 `gsl`로 이름만 바꾸고 다시 측정하세요. 경쟁 tool을 함께 노출한 채로 재야 차이가 보입니다. tool이 하나뿐일 때는 이름을 뭉개도 선택률이 떨어지지 않습니다.
- tool이 일부러 도움이 되지 않는 에러를 반환하게 하고, 모델이 복구하는 데 turn이 몇 번 더 필요한지 세어 보세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: agent-computer interface 설계: tool schema, 이름 짓기, description, 에러 설계.
- **Databricks Generative AI Engineer Associate**: tool and agent framework, evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, software development, experimentation.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
