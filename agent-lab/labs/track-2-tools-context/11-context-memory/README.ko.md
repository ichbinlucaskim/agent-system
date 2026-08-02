# Lab 11 - Context and memory

## 목표

이 lab을 마치면 context window를 여러분이 관리하는 예산으로 다룰 수 있습니다. token 비용을 추정하고, 한도 아래에서 anchor를 보호하며 history를 버리거나 compaction하고, 대량의 세부 내용을 scratchpad 파일로 옮기고, 무엇을 window 안에 두고 무엇을 밖에 둘지 의도적으로 결정할 수 있습니다.

## 사전 준비

Lab 00부터 08까지, 특히 lab 01의 memory. 개념: token 세기, 그리고 모델이 필요로 하는 것과 단지 쓸 수 있을 뿐인 것의 차이.

## 예상 소요 시간

45분에서 60분

## 배경

context engineering은 각 단계에서 window를 무엇이 차지할지 결정하는 일입니다. window가 크면 이 일이 불필요해 보이는데, 그것이 함정입니다. 여유가 있다고 window를 채우면 매 turn 비용이 들고, 실제로 중요한 자료가 어쩌면 쓸모 있을지 모르는 자료로 희석됩니다.

쓸모 있는 context는 세 계층으로 나뉩니다. 지금 당장 모델이 그 위에서 추론하므로 window에 원문 그대로 있어야 하는 것. 요지만으로 충분하므로 요약으로 압축할 수 있는 것. 그리고 window 안에는 포인터만 두고 완전히 파일로 빠져야 하는 것입니다. 장시간 실행되는 agent context의 대부분은 세 번째 계층에 속하는데 실수로 첫 번째 계층에 들어가 있곤 합니다.

예산을 짜려면 비용을 알아야 합니다. 이 lab은 문자 수 기반의 대략적인 token 추정을 사용하는데, 버릴지 남길지 결정하는 데는 충분하지만 청구에는 부적합합니다. 정확한 숫자가 필요할 때는 추정하지 말고 API로 token을 세세요.

context의 일부는 anchor이며 절대 버려서는 안 됩니다. system prompt, 작업 서술, 그리고 모델이 지켜야 하는 제약이 그렇습니다. 오래된 순서로만 잘라내는 budgeter는 결국 그 일이 무엇인지 정의하는 지시를 버리게 되고, 그 실패는 모델이 이유 없이 나빠지는 것처럼 보입니다.

compaction은 의도적으로 손실이 있습니다. 열 개의 turn을 요약으로 대체하는 것은 그 turn들에서 무엇이 핵심인지 결정했을 때만 안전하며, 그것은 대개 산문이 아니라 식별자, 결정, 제약입니다. 좋은 compaction은 이후 단계가 다시 물어봐야 했을 내용을 남깁니다.

scratchpad는 세 번째 계층을 구체화한 것입니다. agent가 발견한 내용을 파일에 쓰고, window에는 한 줄짜리 포인터만 두고, 세부가 필요할 때만 파일을 다시 읽습니다. 이것이 하나의 실행이 window가 한 번에 담을 수 있는 것보다 훨씬 많은 지식을 축적하는 방법입니다.

## 단계

1. `estimate_tokens`를 구현하세요. 문자 수 기반의 대략적인 추정이며, docstring에 청구용 숫자가 아니라 추정치임을 명시합니다.
2. `budget_messages`를 구현하세요. anchor로 표시된 message는 절대 버리지 않으면서, 추정치가 한도에 맞을 때까지 오래된 것부터 버립니다.
3. `compact`를 구현하세요. 최근 몇 개 turn보다 오래된 모든 것을 식별자, 결정, 제약을 보존하는 요약으로 대체합니다.
4. `Scratchpad`를 구현하세요. `data/` 아래에 노트를 쓰고 읽고 나열하며, window에는 노트 본문이 아니라 포인터만 둡니다.
5. `build_context`를 구현하세요. anchor, 압축된 요약, 최근 turn, scratchpad 포인터를 한도에 맞는 최종 message 리스트로 조립합니다.
6. 같은 대화를 budgeting 적용 전후로 실행하고, 총 token과 답변 품질을 비교하세요.

## 검증

```bash
pytest labs/track-2-tools-context/11-context-memory/tests -v
```

budgeting 로직 전체가 오프라인으로 실행됩니다. 통과했다면 한도를 초과하게 되더라도 budgeter가 anchor를 절대 버리지 않고, anchor가 아닌 것 중 오래된 것부터 버려지며, compaction이 최근 turn을 원문 그대로 남기고, scratchpad가 쓰기와 읽기 왕복을 견디며, 가능한 경우 `build_context`가 한도 안의 message 리스트를 반환한다는 뜻입니다.

## 더 나아가기

- 긴 대화에서 버리기와 compaction을 비교하고, 각 전략이 어떤 질문에 답할 수 없게 만드는지 기록하세요.
- 모델이 스스로 scratchpad 노트를 쓰게 하고, 그 노트가 실제로 이후 단계에서 필요했던 것인지 확인하세요.
- 여러분의 문자 기반 추정치를 API의 실제 token 수와 비교하고, 여러분이 다루는 종류의 텍스트에서의 오차를 기록하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: effective context engineering: token 예산 관리, compaction, 세부 내용을 window 밖에 두기.
- **Databricks Generative AI Engineer Associate**: LLM chain을 포함한 application development, governance.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, software development, data preprocessing and feature engineering.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
