# Glossary

이 과정에서 사용하는 용어와, 각 용어를 만들어 보는 lab 번호입니다. 기술 용어는
영어를 그대로 사용합니다. `glossary.md`와 내용을 일치시켜 유지합니다.

## 핵심 building block

**Augmented LLM** (lab 01)
retrieval, tool, memory가 붙은 모델 호출. Building Effective Agents의 기본
building block입니다. 이 과정의 다른 모든 패턴이 이 형태의 호출로 구성됩니다.

**Workflow** (lab 02 - 06)
control flow를 여러분이 작성하는 시스템. 단계와 그 순서가 코드에 있으므로 동작이
예측 가능하고 테스트 가능합니다.

**Agent** (lab 12)
중단 조건이 발동할 때까지 루프 안에서 모델이 다음에 무엇을 할지 결정하는 시스템.
workflow와의 차이는 다음 단계를 누가 고르는가이며, 그 차이 때문에 agent에는
예산이 필요합니다.

**Tool** (lab 01, 07)
이름, description, input schema로 모델에 기술된 행동. 모델은 `tool_use` block을
내보내고, 여러분의 코드가 이를 실행해 `tool_result`를 반환합니다. 모델은 아무것도
직접 실행하지 않습니다.

**Tool result** (lab 01)
tool 호출에 대해 여러분의 코드가 반환하는 출력. `tool_use` id마다 하나씩,
하나의 user message에 모두 담습니다. 실패한 tool은 예외를 던지는 대신 에러로
표시된 result를 반환합니다.

## 패턴

**Prompt chaining** (lab 02)
각 호출이 이전 출력을 소비하는 고정된 호출 시퀀스이며, 보통 단계 사이에
프로그램적 gate를 둡니다.

**Gate** (lab 02)
chain의 두 단계 사이에서 평범한 코드로 수행하는 결정적 검사. 잘못된 중간 결과에
비용을 두 번 치르는 것을 막아 줍니다.

**Routing** (lab 03)
입력을 classify해서 여러 특화 prompt나 model 중 하나로 dispatch하는 것. 어느
곳에도 맞지 않는 입력을 위한 fallback 경로를 둡니다.

**Misroute rate** (lab 03)
라벨링된 집합에서 classifier가 잘못된 경로로 보낸 비율. 라벨링된 데이터가
필요하며, 그것이 없으면 classification prompt의 변경은 추측일 뿐입니다.

**Sectioning** (lab 04)
하나의 작업을 독립적인 부분으로 나누고 부분마다 호출을 동시에 실행하는 것.

**Voting** (lab 04)
같은 작업을 여러 번 실행하고 답을 집계하는 것. 일치는 증거이고 불일치는 상위
확인이 필요하다는 신호입니다.

**Orchestrator-workers** (lab 05)
런타임에 결정한 하위 작업으로 분해하는 lead 호출, 그것을 수행하는 worker 호출,
그리고 결과를 종합하는 lead 호출.

**Evaluator-optimizer** (lab 06)
generator 호출과 critic 호출을 루프로 묶은 것. 명시적 중단 기준과 최대 반복
예산을 갖습니다.

## Tool과 context

**Agent-computer interface (ACI)** (lab 07)
agent가 보는 표면. tool 이름, description, schema, 에러 메시지입니다. 사람에게의
user interface와 같은 역할입니다.

**Retrieval** (lab 01, 08)
요청 시점에 모델이 갖고 있지 않은 사실을 prompt에 넣는 것.

**Chunking** (lab 08)
문서를 검색 가능한 조각으로 나누는 것. chunk 크기와 overlap이 두 개의 손잡이이며,
lab 09에서는 추측 대신 sweep으로 정합니다.

**Embedding** (lab 08)
유사도 검색에 쓰이는 텍스트의 vector 표현. 이 과정은 embedding API가 필요 없도록
결정적인 로컬 hash 기반 stub을 사용합니다.

**Cosine similarity** (lab 08)
`common/vectorstore.py`가 사용하는 유사도 척도. 크기가 아니라 방향을 비교하며,
문서 길이가 제각각일 때 바라는 성질입니다.

**Grounding** (lab 08)
답변이 제공된 구절에서 나오고, 그것을 인용하며, 근거가 없으면 거절하도록 요구하는
것.

**Recall at k** (lab 09)
검색됐어야 할 구절 중 상위 k개 안에 나타난 비율. 핵심 retrieval 지표이며 라벨링된
집합이 필요합니다.

**Hybrid search** (lab 09)
keyword 점수와 vector 점수의 가중 결합. 둘은 서로 다른 방향으로 실패하므로 결합이
대개 각각보다 낫습니다.

**Reranking** (lab 09)
저렴하게 검색한 후보 목록에 대한 두 번째의 더 정밀한 점수화 단계.

**MCP-style server** (lab 10)
함수로 import되는 대신 stdio 위에서 문서화된 프로토콜로 대화하는 tool server.
그 경계가 격리, 독립적 배포, 런타임 discovery를 사 줍니다.

**Context window** (lab 11)
한 번의 요청에서 모델이 보는 token. 예산으로 다루세요. 그 안에 있는 것은 매 turn
비용이 들고 그 안의 다른 것들을 희석합니다.

**Context engineering** (lab 11)
각 단계에서 window를 무엇이 차지할지, 그리고 무엇이 대신 요약이나 파일로 가야
할지 결정하는 일.

**Compaction** (lab 11)
오래된 turn을 요약으로 대체하는 것. 의도적으로 손실이 있으므로, 압축하기 전에
무엇이 핵심인지 결정해야 합니다.

**Scratchpad** (lab 11)
파일에 기록하고 window에는 포인터만 두는 노트. 하나의 실행이 window가 담을 수
있는 것보다 많은 것을 축적할 수 있게 해 줍니다.

## 자율성과 프로덕션

**Agent loop** (lab 12)
message를 보내고, 요청된 tool을 실행하고, 결과를 덧붙이고, 반복합니다. 그 주변에
작성하는 코드의 대부분은 언제 멈출 것인가에 관한 것입니다.

**Step budget, cost ceiling, deadline** (lab 12)
실행에 대한 세 가지 독립적인 한계. 각각 다르게 실패하므로 분리해서 유지하고, 어느
것이 실행을 멈췄는지 보고하세요.

**Non-progress detection** (lab 12)
같은 행동과 관찰이 반복되고 있음을 알아채는 것. 막힌 agent는 크래시하지 않으므로
step 예산만으로는 계속 돌게 됩니다.

**Subagent** (lab 13)
자신만의 context window와 제한된 tool 집합을 가진 child agent. 이득은 context
격리와 능력 제한이고, 비용은 인계 과정입니다.

**Approval gate** (lab 14)
`tool_use` block과 그 실행 사이에 선 사람. 실제 결정을 내릴 수 있을 만큼의 결과를
보여 주어야 합니다.

**Action classification** (lab 14)
행동을 되돌릴 수 있는지와 영향 범위에 따라 자동, 확인 필요, 금지로 분류하고 그것을
코드로 강제하는 것.

**Evaluation suite** (lab 15)
반복 실행되는 사례 집합. 가능한 곳에서는 결정적 검사로, 그렇지 않은 곳에서는
rubric 기반 judge로 채점하고 pass rate로 보고합니다.

**LLM as judge** (lab 15)
모델 호출로 rubric에 따라 출력을 채점하는 것. 측정하려는 변동성을 그 자신이 갖고
있으므로 구체적인 기준과 구조화된 출력이 필요합니다.

**Flaky case** (lab 15)
pass rate가 0과 1 사이에 엄격히 위치하는 사례. 통과도 실패도 아니며, 어떤 사례가
flaky한지 아는 것이 종합 점수보다 유용할 때가 많습니다.

**Trace** (lab 16)
step마다의 구조화된 기록. 이름, 소요 시간, token usage, 에러를 담아 비용과 지연을
실행이 아니라 step에 귀속시킬 수 있게 합니다.

**Guardrail** (lab 17)
모델이 협조하든 하지 않든 실행되는 코드. system prompt의 지시는 통제가 아니라
선호입니다.

**Prompt injection** (lab 17)
모델이 읽는 콘텐츠 안에 숨겨진, 모델을 겨냥한 지시. 통상적인 진입 지점은 사용자의
message가 아니라 tool 결과입니다.

**Smoke test** (lab 18)
최소한의 배포 검사. 기동하는가, 응답하는가, 잘못된 형식의 요청이 깔끔한 에러를
내는가. 품질 평가가 아닙니다.

## API 용어

**Token** (lab 00)
비용과 context budget 양쪽의 단위. 응답의 `input_tokens`는 프롬프트 중 캐시되지
않은 나머지만 센다는 점에 유의하세요.

**`stop_reason`** (lab 00)
생성이 끝난 이유. `tool_use`는 tool 루프를 구동하고, `max_tokens`는 응답이
잘렸다는 뜻이며, `refusal`은 요청이 거절되었다는 뜻입니다.

**Streaming** (lab 00)
생성되는 대로 출력을 받는 것. 답을 바꾸지 않고 보이는 시점만 바꾸며, 긴 응답에서
HTTP timeout을 피하게 해 줍니다.

**System prompt** (lab 00, 01)
대화 앞에 놓이는 지시와 context. 검색된 구절은 보통 출처 라벨과 함께 여기에
들어갑니다.
