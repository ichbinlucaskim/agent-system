# Lab 02 - Prompt chaining

## 목표

이 lab을 마치면 하나의 작업을 고정된 모델 호출 시퀀스로 분해해 각 호출이 이전 출력을 소비하도록 만들고, 단계 사이에 프로그램적 gate를 두고, chaining이 추가 비용과 지연을 감수할 만한 경우를 판단할 수 있습니다.

## 사전 준비

Lab 00, 01. 개념: augmented call, system prompt, 그리고 여러분이 작성하는 control flow와 모델이 선택하는 control flow의 차이.

## 예상 소요 시간

30분에서 45분

## 배경

prompt chaining은 작업을 고정된 단계 시퀀스로 분해해, 각 모델 호출이 한 단계를 담당하고 직전 단계의 출력을 소비하도록 만듭니다. 시퀀스는 모델의 판단이 아니라 여러분의 코드에 존재하므로 workflow 전체가 예측 가능하고 디버깅하기 쉬우며 테스트 비용이 낮습니다.

이 교환은 의도적입니다. 지연 시간과 token을 지불하고 정확도를 삽니다. 요구사항 추출, 명세 초안 작성, 문장 다듬기를 한 번의 호출로 요구하면 세 가지 모두 그럭저럭 해냅니다. 각각 한 가지만 하는 세 번의 호출은 대체로 각각을 더 잘 해냅니다. 각 호출이 만족시켜야 할 지시 집합과 출력 형식이 하나뿐이기 때문입니다.

gate는 chain을 단순한 pipeline 이상으로 만들어 주는 요소입니다. 두 단계 사이에서 평범한 Python으로 결정적인 검사를 수행하세요. 리스트가 비어 있지 않은지, JSON이 파싱되는지, 초안이 모든 요구사항을 언급하는지 확인합니다. 검사가 실패하면 잘못된 중간 결과를 다음 호출에 넣어 비용을 두 번 치르는 대신 중단하거나 해당 단계를 재시도하거나 다른 경로로 보냅니다.

chain에서는 오류가 곱해집니다. 각각 90퍼센트 확률로 옳은 세 단계는 전체적으로 약 73퍼센트 확률로 옳은 chain이 됩니다. gate는 그 곱셈을 멈추는 방법입니다. 포착된 실패는 오염된 최종 답변이 아니라 재시도가 되기 때문입니다.

한 번의 호출로 이미 충분하다면 chaining은 잘못된 도구입니다. 단계가 하나 늘 때마다 비용, 지연, 실패 표면이 배가됩니다. 하위 작업의 성격이 실제로 서로 다를 때, 중간에 checkpoint가 필요할 때, 또는 거대한 prompt 하나가 스스로 모순되기 시작했을 때 chain을 선택하세요.

## 단계

1. `extract_requirements`를 구현하세요. 자유 형식 brief를 짧은 요구사항 문자열의 리스트로 바꾸는 모델 호출 하나입니다.
2. `gate_requirements`를 구현하세요. `(ok, reason)`을 반환하는 결정적 검사입니다. 빈 리스트, 모호한 항목 하나뿐인 리스트, 실행 가능하지 않은 항목을 거부합니다.
3. `draft_spec`을 구현하세요. 원본 brief가 아니라 gate를 통과한 요구사항 리스트만 소비하는 두 번째 호출입니다.
4. `polish_spec`을 구현하세요. 요구사항을 추가하지 않으면서 초안을 명확하게 다시 쓰는 세 번째 호출입니다.
5. `run_chain`을 구현하세요. 세 단계를 순서대로 실행하고, 1단계 뒤에 gate를 적용하고, 실패한 단계를 `max_retries`까지 재시도하며, 실패를 검사할 수 있도록 모든 중간 출력을 반환합니다.
6. `common.tracing`의 `Trace`를 chain 전체에 연결하세요. 모델을 호출하는 각 단계를 `trace.step(...)`으로 감싸고, 그 단계가 자신의 응답에 대해 `record_usage`를 호출할 수 있도록 record를 넘긴 뒤, 리포트를 출력해 각 단계의 token과 지연 시간이 보이게 합니다.

## 검증

```bash
pytest labs/track-1-patterns/02-prompt-chaining/tests -v
```

gate 테스트는 오프라인으로 실행되며 이 lab의 핵심입니다. 결정적으로 테스트할 수 없는 gate는 gate가 아닙니다. chain 테스트는 모든 중간 출력이 반환되는지, gate 실패가 chain을 중단시키는지, 재시도가 정확히 한 번 일어나는지 확인합니다.

## 더 나아가기

- 동일한 brief 열 개에 대해 chain과 세 단계를 한꺼번에 처리하는 단일 호출을 비교하고, 비용 대비 품질을 견주어 보세요.
- gate를 평범한 Python 대신 모델 호출로 만들어 보고, 비용과 신뢰성 관점에서 그 선택에 찬성 또는 반대하는 근거를 정리하세요.
- 분기를 추가하세요. gate가 두 번 실패하면 세 번째 재시도 대신 되묻는 질문으로 경로를 바꿉니다.
- usage를 반대 방향으로 빼내 보세요. lab 00이 주장한 대로 각 단계가 값과 함께 응답 객체를 반환하도록 만들고, step record를 내려보내서 얻는 단순한 반환 타입과 견주어 보세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: prompt chaining: 프로그램적 gate를 둔 고정 시퀀스로 작업을 분해하기.
- **Databricks Generative AI Engineer Associate**: problem decomposition and solution design, LLM chain을 포함한 application development.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, software development.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
