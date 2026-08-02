# Capstone - 제한을 갖춘 research agent

## 목표

과정에서 다룬 모든 것을 사용하는 agent 하나를 만들고, 그 설계를 숫자로 옹호하는
것입니다. 결과물은 데모가 아닙니다. evaluation suite, 비용과 지연 리포트,
approval gate, 그리고 각 패턴이 왜 거기 있는지에 대한 글로 된 근거를 갖춘
agent입니다.

## 사전 준비

Lab 00부터 18까지. lab 09, 16, 18은 과정에서 선택으로 표시되어 있지만 capstone은
셋 모두를 전제합니다. 09가 없으면 retrieval을 옹호할 수 없고, 16이 없으면 비용을
설명할 수 없으며, 18이 없으면 시스템이 아니라 스크립트를 갖게 됩니다.

## 예상 소요 시간

6시간에서 10시간이며, 여러 차례에 나누어 진행하는 편이 좋습니다.

## 과제 개요

여러분이 선택한 문서 corpus에 대해 질문에 답하고, 부작용이 있는 tool을 최소 하나
이상 통해 그 답에 따라 행동할 수 있는 agent를 만드세요.

실제로 관심 있는 corpus를 고르세요. 어떤 프로젝트의 문서, 정책 모음, 연구 분야,
여러분 자신의 노트 같은 것입니다. 문서 쉰 개에서 오백 개 정도가 적절합니다.
retrieval이 의미를 가질 만큼은 많고, 손으로 라벨링할 수 있을 만큼은 적습니다.

agent는 답하기만 하는 것이 아니라 무언가를 할 수 있어야 합니다. 요약 파일 쓰기,
이슈 열기, 초안 보내기, 레코드 갱신 같은 것입니다. 그 행동이 approval gate를
장식이 아니라 실제로 만들어 줍니다.

## 요구사항

**아키텍처.** track 1의 패턴을 최소 세 개 사용하고, 각각이 왜 거기 있는지 적으세요.
사실 질문은 저렴한 경로로, 분석 질문은 비싼 경로로 보내는 routing 단계. 잘못된
중간 결과가 비쌌을 지점에 gate를 둔 chain. 무엇이 좋은 결과인지 말할 수 있는
곳의 evaluator-optimizer 루프. 개수보다 근거가 중요합니다. 정당화할 수 없는
패턴은 제거해야 합니다.

**Retrieval.** lab 08의 로컬 stub으로 corpus를 chunk로 나누고 embedding하세요.
최소 스무 개의 질의에 그것을 답해야 할 chunk를 라벨링하고, 최종 구성의 recall@k를
여러분이 기각한 기준선 하나 이상과 비교해 보고하세요.

**Tool.** 최소 세 개의 tool이며 그중 하나는 부작용이 있어야 합니다. lab 07에서
배운 대로 description을 작성하세요. 무엇을 하는지만이 아니라 언제 호출해야 하는지
말해야 합니다. 그중 최소 하나는 lab 10의 MCP 스타일 server를 통해 노출하세요.

**자율성.** step 예산, 비용 상한, 진전 없음 탐지를 갖춘 agent 루프. 성공한
실행을 포함해 모든 실행이 중단 사유를 반환해야 합니다.

**사람의 개입.** 모든 행동을 자동, 확인 필요, 금지로 분류하세요. 금지는 코드로
강제합니다. 쓰기 작업 전에는 diff 또는 그에 상응하는 결과 미리보기를 보여 주세요.

**Context.** context 예산보다 긴 대화를 처리하세요. compaction, scratchpad, 또는
둘 다입니다. 무엇을 선택했고 그것이 무엇을 잃는지 밝히세요.

**Guardrail.** input filtering, schema에 대한 output validation, 그리고 신뢰할 수
없는 데이터로 감싼 tool 결과. 모델을 겨냥한 지시가 들어 있는 문서를 agent에
넣는 테스트를 최소 하나 포함하고, 그것을 막는 것이 prompt가 아니라 tool 제한임을
보이세요.

**Evaluation.** 최소 열다섯 개의 사례. 적용 가능한 곳에는 결정적 검사를, 그렇지
않은 곳에만 rubric 기반 judge를 사용합니다. 사례당 최소 세 번의 실행에 걸친 pass
rate를 보고하고 flaky한 것을 표시하세요.

**Observability.** 실행마다의 trace, step별로 귀속된 비용과 지연, 그리고 텍스트
리포트. 비용을 지배하는 step을 찾아내고 그에 대해 무엇을 했는지 밝히세요.

**Packaging.** CLI와 health 엔드포인트. 설정은 전적으로 environment에서 오며 기동
시점에 검증됩니다. 기동과 응답을 증명하는 smoke test를 포함하세요.

## 진행 단계

1. **Corpus와 라벨.** 문서를 모으고 라벨링된 질의 집합을 작성합니다. 이것을 가장
   먼저 하세요. 이후의 모든 것이 이것을 기준으로 측정됩니다.
2. **Retrieval 기준선.** store를 만들고 recall@k를 측정하고, 대안 구성을 하나 더
   시도해서 두 숫자를 모두 보관합니다.
3. **Augmented call.** retrieval과 tool과 memory로 인용과 함께 답합니다. lab 01을
   실제 규모로 하는 것입니다.
4. **패턴.** 여러분의 작업에 실제로 필요한 track 1 패턴을 하나씩 추가하고, 추가할
   때마다 측정합니다.
5. **루프.** workflow를 예산과 중단 사유를 갖춘 agent로 바꿉니다.
6. **안전.** approval gate와 guardrail을 테스트와 함께 추가합니다.
7. **Evaluation과 observability.** suite, trace, 리포트를 만듭니다.
8. **Packaging.** CLI, health, smoke test, 그리고 동료가 따라 할 수 있는 README를
   작성합니다.

## 검증

capstone에는 테스트 harness가 없습니다. 검증 기준은 다음 질문들에 의견이 아니라
증거로 답할 수 있는가입니다.

- 한 번의 실행에 얼마가 들며, 어느 step이 그 비용을 지배합니까?
- retrieval recall@k는 얼마이며, 어떤 구성을 기각했습니까?
- pass rate는 얼마이며, 어떤 사례가 flaky합니까?
- 문서가 agent에게 지시를 무시하라고 하면 어떻게 됩니까?
- 진전이 없는 실행을 무엇이 멈추며, 그것을 어떻게 압니까?
- 아키텍처에서 아무것도 잃지 않고 제거할 수 있는 패턴은 무엇입니까?

마지막 질문이 중요합니다. 옹호할 수 있는 설계에는 무엇이 제 몫을 하지 못하는지
아는 것도 포함됩니다.

## 더 나아가기

- 전체 suite를 서로 다른 두 model로 실행하고 품질만이 아니라 비용 대비 품질을
  비교하세요.
- agent가 완수할 수 없는 작업을 주고, 깔끔하게 멈추고 이유를 보고하며 아무것도
  절반만 쓰지 않는지 확인하세요.
- 저장소를 다른 사람에게 넘기고, 여러분에게 아무것도 묻지 않은 채 README만으로
  설정하는지 지켜보세요.

## 인증 시험 매핑

capstone은 과정이 대응하는 모든 영역을 다룹니다. 그 모두를 하나의 시스템으로
조립하기 때문입니다.

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI
  agents**: workflow 패턴, agent loop, agent-computer interface 설계, context
  engineering을 하나의 애플리케이션으로 조합하기.
- **Databricks Generative AI Engineer Associate**: problem decomposition and
  solution design, data preparation and chunking, RAG 및 LLM chain을 포함한
  application development, MCP server를 포함한 tool and agent framework,
  assembling and deploying applications, governance, evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, alignment,
  experimentation, data analysis and visualization, data preprocessing and
  feature engineering, software development, Python libraries for LLMs, LLM
  integration and deployment.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로
여기고 공식 시험 가이드를 직접 확인하세요. `docs/cert-mapping.md`를 참고하세요.
