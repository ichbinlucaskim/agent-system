# Lab 11 - Context and memory

## 목표

이 lab을 마치면 context window를 여러분이 관리하는 예산으로 다룰 수 있습니다. token 비용을 추정하고, 한도 아래에서 anchor를 보호하며 history를 버리거나 compaction하고, 대량의 세부 내용을 모델이 여전히 닿을 수 있는 scratchpad 파일로 옮기고, 무엇을 window 안에 두고 무엇을 밖에 둘지 의도적으로 결정할 수 있습니다.

## 사전 준비

Lab 00부터 08까지, 특히 lab 01의 memory와 lab 07의 tool 설계. 개념: token 세기, 그리고 모델이 필요로 하는 것과 단지 쓸 수 있을 뿐인 것의 차이.

## 예상 소요 시간

45분에서 60분

## 배경

context engineering은 각 단계에서 window를 무엇이 차지할지 결정하는 일입니다. window가 크면 이 일이 불필요해 보이는데, 그것이 함정입니다. 여유가 있다고 window를 채우면 매 turn 비용이 들고, 실제로 중요한 자료가 어쩌면 쓸모 있을지 모르는 자료로 희석됩니다.

쓸모 있는 context는 세 계층으로 나뉩니다. 지금 당장 모델이 그 위에서 추론하므로 window에 원문 그대로 있어야 하는 것. 요지만으로 충분하므로 digest로 압축할 수 있는 것. 그리고 window 안에는 포인터만 두고 완전히 파일로 빠져야 하는 것입니다. 장시간 실행되는 agent context의 대부분은 세 번째 계층에 속하는데 실수로 첫 번째 계층에 들어가 있곤 합니다.

예산을 짜려면 비용을 알아야 합니다. 이 lab은 문자 수 기반의 대략적인 token 추정을 사용하는데, 버릴지 남길지 결정하는 데는 충분하지만 청구에는 부적합합니다. 정확한 숫자가 필요할 때는 추정하지 말고 API로 token을 세세요.

context의 일부는 anchor이며 절대 버려서는 안 됩니다. system prompt, 작업 서술, 그리고 모델이 지켜야 하는 제약이 그렇습니다. 오래된 순서로만 잘라내는 budgeter는 결국 그 일이 무엇인지 정의하는 지시를 버리게 되고, 그 실패는 모델이 이유 없이 나빠지는 것처럼 보입니다.

anchor는 그 교훈의 절반일 뿐이고, 나머지 절반은 놓치기 쉽습니다. **나이 순서가 아니라 가치 순서로 자르세요.** 오래된 turn 스무 개를 대체한 digest는 구조상 window에서 anchor가 아닌 가장 오래된 message이므로, 가장 오래된 것부터 버리는 budgeter는 digest를 버리고 그 뒤에 온 잡담을 남깁니다. 이건 compaction의 취지를 그대로 뒤집습니다. 애써 보존한 식별자, 결정, 제약이 먼저 나가고 인사말이 원문 그대로 살아남습니다. 각 message에 계층을 부여하고 압축된 것보다 원문 turn을 먼저 희생시키세요.

compaction은 의도적으로 손실이 있습니다. 열 개의 turn을 digest로 대체하는 것은 그 turn들에서 무엇이 핵심인지 결정했을 때만 안전하며, 그것은 대개 산문이 아니라 식별자, 결정, 제약입니다. 좋은 compaction은 이후 단계가 다시 물어봐야 했을 내용을 남깁니다. 그리고 크기에 상한이 있어야 하며 기대에 맡길 수 없습니다. 문장을 통째로 남기는 추출식 요약은, 거의 모든 문장에 식별자가 든 history에서는 원본보다 긴 결과를 만들어냅니다. 아무것도 절약하지 못하는 compaction은 순손실이므로, 대체할 turn들을 이기지 못하는 compactor는 아예 실행을 거부해야 합니다. 같은 이유로 이미 한도에 맞는 history는 compaction하지 마세요.

scratchpad는 세 번째 계층을 구체화한 것입니다. agent가 발견한 내용을 파일에 쓰고, window에는 한 줄짜리 포인터만 두고, 세부가 필요할 때만 파일을 읽습니다. 이것이 하나의 실행이 window가 한 번에 담을 수 있는 것보다 훨씬 많은 지식을 축적하는 방법이며, 포인터가 실행 가능할 때만 성립합니다. 포인터는 노트 이름을 말하고, 모델이 열어볼 가치가 있는지 판단할 수 있도록 크기를 말하고, 그것을 여는 tool과 함께 와야 합니다. 따라갈 방법이 없는 포인터는 계층이 아니라 막힌 길입니다.

자르기의 결과 두 가지가 사람들을 걸려 넘어지게 하는데, 예산과 무관해 보이는 에러로 나타나기 때문입니다. 첫째는 기계적입니다. 두 user turn 사이의 assistant turn을 버리면 user message가 연속으로 두 개 남고, 첫 user turn을 버리면 목록이 assistant message로 시작할 수 있습니다. 둘 다 budgeter가 만든 일이므로, 정규화는 API가 항의한 뒤의 재시도가 아니라 budgeter 쪽에 속합니다. 둘째는 더 이상하고 직접 볼 만합니다. 나이 순으로만 자른 history는 대화 중간에서 시작하는데, 결정이 이미 단언되어 있고 assistant가 이미 그것에 동의한 상태입니다. 이는 모델이 거짓 전제를 받아들이게 하려고 심어놓은 대화와 구별되지 않으며, 모델은 그런 context에 아예 답하기를 거부할 수 있습니다. digest는 이 문제도 해결하는데, 침묵의 공백을 남기는 대신 자신이 무엇을 대체하는지 선언하기 때문입니다.

마지막으로 측정에 관한 이야기입니다. context를 바꿔가며 답변을 비교할 때, **빈 답변은 나쁜 답변이 아닙니다.** 거부, 또는 `max_tokens`로 끝난 실행은 window에 무엇이 있었는지와 무관하며, 그것을 context 실패로 채점하면 예산이 일으키지 않은 문제를 고치려고 예산을 조정하게 됩니다. 결론을 내리기 전에 `stop_reason`을 읽으세요.

## 단계

1. `estimate_tokens`와 `total_tokens`를 구현하세요. 문자 수 기반의 대략적인 추정이며, docstring에 청구용 숫자가 아니라 추정치임을 명시합니다.
2. `budget_messages`를 구현하세요. anchor로 표시된 message는 절대 버리지 않고, 나머지는 계층별로 각 계층 안에서 오래된 것부터 버려서 digest보다 원문 turn이 먼저 희생되게 합니다. 남은 anchor 아닌 message를 버릴 수 있는 마지막 패스로 마무리하세요. 그러지 않으면 계층 이름의 오타 하나가 message를 window에 영구히 고정시킵니다.
3. `compact`를 구현하세요. 최근 몇 개 turn보다 오래된 모든 것을 식별자, 결정, 제약을 보존하는 digest로 대체하고 digest 계층으로 표시합니다. 크기에 상한을 두고, digest가 대체할 대상보다 작아지지 못하면 compaction을 거부하세요.
4. `Scratchpad`와 `scratchpad_index`를 구현하세요. `data/` 아래에 노트를 쓰고 읽고 나열하며, 각 노트의 이름, 크기, 그것을 여는 tool을 담은 포인터를 만듭니다.
5. `build_context`를 구현하세요. anchor, digest, 최근 turn, scratchpad 포인터를 한도에 맞는 message 리스트로 조립하되, 원본 history가 이미 맞는다면 compaction을 아예 건너뜁니다.
6. `to_api_messages`, `READ_NOTE_TOOL`, `run_read_note`, `answer_with_scratchpad`를 구현하세요. budgeting이 깨뜨린 형태를 정규화하고, 모델이 필요하다고 판단한 노트를 직접 열게 합니다.
7. 이른 history의 사실 하나와 노트에만 있는 사실 하나가 모두 필요한 질문을 하나 만들고, 세 가지 context에서 답하게 하세요. 전부 window에 넣기, 나이 순으로만 자르기, 그리고 budgeting한 context입니다. token 비용과 각 답변이 실제로 두 사실을 담고 있는지를 함께 비교하세요.

## 검증

```bash
pytest labs/track-2-tools-context/11-context-memory/tests -v
```

budgeting 로직 전체가 오프라인으로 실행되고, 모델이 관여하는 하나의 테스트는 모델을 stub으로 둡니다. 검사 대상은 어떤 context가 모델에 닿았는지이기 때문입니다.

통과했다면 한도를 초과하게 되더라도 budgeter가 anchor를 절대 버리지 않고, digest보다 원문 turn이 먼저 희생되면서도 남은 것이 없으면 digest도 버려질 수 있으며, 인식되지 않는 계층이 message를 불멸로 만들지 않고, compaction이 최근 turn을 원문 그대로 남기고 대체한 turn들보다 결코 비싸지 않으며, 목표치를 받은 digest가 그 목표에 맞고, 포인터가 노트 이름과 크기와 그것을 읽는 tool을 함께 말하며, scratchpad가 쓰기와 읽기 왕복을 견디고 디렉터리를 벗어나는 이름을 거부하며, `build_context`가 한도 안의 리스트를 반환하면서 노트 본문을 window 밖에 두고 이미 맞는 history를 압축하지 않으며, 기록용 필드가 API에 닿지 않고, 같은 role이 연속되면 병합되고 앞머리의 assistant turn이 제거되며, 잘못된 노트 이름이 실제 선택지를 알려주는 에러로 돌아오고, 모델이 window에 없던 세부까지 포인터를 따라 닿을 수 있으며, 빈 답변이 나쁜 답변으로 취급되지 않고 자신의 `stop_reason`을 보고한다는 뜻입니다.

`main` 실행은 마지막 비교에서만 키가 필요하고 키가 없으면 명확한 건너뛰기 메시지를 출력하므로, 이 lab의 budgeting 절반은 오프라인으로 계속 실행할 수 있습니다.

## 더 나아가기

- 긴 대화에서 버리기와 compaction을 비교하고, 각 전략이 어떤 질문에 답할 수 없게 만드는지 기록하세요.
- demo에서 어떤 turn이 원문 그대로 살아남는지 보세요. 최신성은 관련성의 값싼 대리 지표이고, 결정이 압축되는 동안 잡담이 살아남는 것이 그 근사의 대가입니다. 제대로 고치려면 모델이 중요도를 판단하게 해야 하는데, 그러면 budgeter 안에 모델 호출이 들어갑니다.
- 모델이 스스로 scratchpad 노트를 쓰게 하고, 그 노트가 실제로 이후 단계에서 필요했던 것인지 확인하세요.
- 여러분의 문자 기반 추정치를 API의 실제 token 수와 비교하고, 여러분이 다루는 종류의 텍스트에서의 오차를 기록하세요. 그리고 그 추정치가 아예 무시하는 것도 짚어 보세요. tool 정의, system prompt, 이미지가 모두 같은 window를 차지합니다.
- demo의 naive 자르기에 digest 형태의 서두를 붙여 보세요. 모델이 잘린 context를 거부했는데 공백을 선언한 순간 같은 내용을 받아들인다면, "더 작아진 context"와 "위조처럼 보이는 context"의 차이를 찾은 것입니다.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: effective context engineering: token 예산 관리, compaction, 세부 내용을 window 밖에 두기.
- **Databricks Generative AI Engineer Associate**: LLM chain을 포함한 application development, governance.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, software development, data preprocessing and feature engineering.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
