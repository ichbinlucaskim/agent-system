# Lab 08 - RAG basics

## 목표

이 lab을 마치면 retrieval pipeline을 처음부터 끝까지 만들 수 있습니다. 문서를 chunk로 나누고, 결정적인 로컬 stub으로 embedding하고, cosine similarity로 검색하고, 검색된 구절에 근거하며 그것을 인용하는 답변을 생성할 수 있습니다.

## 사전 준비

Lab 00, 01, 07. 개념: vector와 cosine similarity, 그리고 `common/vectorstore.py`.

## 예상 소요 시간

60분에서 90분

## 배경

retrieval은 요청 시점에 올바른 사실을 모델 앞에 놓아 주는 일입니다. 모델이 갖고 있지 않은 지식을 주는 가장 저렴한 방법이고, 원본이 갱신되는 순간 함께 갱신되며, fine tuning과 달리 감사 추적을 남깁니다. 답변이 어느 구절에서 나왔는지 가리킬 수 있기 때문입니다.

chunking은 첫 번째 실질적인 설계 결정입니다. chunk가 너무 작으면 구절을 의미 있게 만드는 맥락을 잃고, 너무 크면 신호가 희석되고 아무도 요청하지 않은 텍스트에 token을 낭비합니다. 인접 chunk 사이의 overlap은 경계에 걸친 문장이 검색 불가능해지는 것을 막아 줍니다. lab 09에서는 이를 추측이 아니라 측정된 sweep으로 바꿉니다.

이 lab은 embedding API 대신 결정적인 hash 기반 embedding stub을 사용합니다. 의미적으로 강력하지 않으며 그것은 의도된 선택입니다. 계정도 네트워크도 key도 필요 없고, 같은 텍스트에 대해 항상 같은 vector를 반환하며, pipeline의 동작을 테스트 가능하게 만듭니다. pipeline의 나머지 부분은 실제 embedding model을 상대로 만들 때와 정확히 같습니다.

similarity search는 저장된 vector에 대한 cosine similarity이며, `common/vectorstore.py`가 numpy로 구현해 둔 것입니다. cosine은 크기가 아니라 방향을 비교하는데, 문서 길이가 제각각일 때 바라는 성질이 바로 그것입니다. 영속화는 표준 라이브러리의 sqlite3 파일 하나입니다.

grounding은 사람들이 건너뛰는 부분입니다. prompt에서 강제되지 않는 retrieval은 구절을 읽고도 결국 기억에서 답하는 모델을 만들어 냅니다. 제공된 구절로만 답하고, 각 주장마다 chunk id를 인용하고, 구절이 질문을 다루지 않으면 모른다고 말하도록 지시하세요.

인용은 확인할 수 있어야 가치가 있습니다. 답변과 함께 검색된 chunk id를 반환해서 호출자나 테스트나 검토자가 인용된 구절이 실제로 답변이 주장하는 내용을 담고 있는지 확인할 수 있게 하세요.

## 단계

1. `chunk`를 구현하세요. 텍스트를 목표 크기의 겹치는 윈도로 나누되, 단어 중간을 자르기보다 문장이나 문단 경계를 선호합니다.
2. `embed`를 구현하세요. 결정적인 hash 기반 vector입니다. 각 token을 정해진 차원 수로 hash해 누적하고 정규화합니다. 같은 텍스트는 항상 같은 vector를 만들어야 합니다.
3. `build_store`를 구현하세요. 모든 문서를 chunk로 나누고 각 chunk를 embedding한 뒤, 원본 문서와 chunk 인덱스를 함께 식별하는 id로 `VectorStore`에 추가합니다.
4. `search`를 구현하세요. 질의를 embedding하고 점수와 함께 상위 k개 결과를 반환합니다.
5. `answer`를 구현하세요. 검색 결과로 system prompt를 만들고, chunk id를 인용하며 근거가 없으면 거절하도록 지시하고, 답변과 검색된 id를 함께 반환합니다.
6. store를 `data/` 아래 sqlite3로 영속화하고, 새 프로세스에서 다시 불러와 검색 결과가 동일한지 확인하세요.

## 검증

```bash
pytest labs/track-2-tools-context/08-rag-basics/tests -v
```

최종 생성을 제외한 pipeline 전체는 결정적이며 오프라인으로 실행됩니다. 통과했다면 chunk가 크기와 overlap 설정을 지키고, 같은 텍스트가 항상 같은 vector로 embedding되며, 질의가 실제로 답을 담은 chunk를 검색해 오고, store가 저장과 로드 왕복을 거쳐도 변하지 않으며, **별도 프로세스**에서 다시 불러와도 순위가 같다는 뜻입니다. 마지막 항목은 프로세스 경계를 실제로 넘어야만 검사됩니다. 같은 프로세스 안에서는 프로세스마다 salt가 달라지는 builtin `hash()`로도 왕복이 통과하기 때문입니다.

## 더 나아가기

- corpus가 답할 수 없는 질문을 던지고 모델이 인용을 지어내지 않고 거절하는지 확인하세요. 사실과 어긋나는 인용은 인용이 없느니만 못합니다.
- hash embedding을 lab 01의 token 겹침 점수로 바꾸고 같은 질의에서 어느 쪽이 더 잘 검색하는지 비교하세요.
- 첫 번째 문서와 모순되는 두 번째 문서를 추가하고, 둘 다 검색됐을 때 모델이 어떻게 하는지 관찰하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: augmented LLM building block의 retrieval 부분, grounding과 인용.
- **Databricks Generative AI Engineer Associate**: data preparation and chunking, RAG를 포함한 application development.
- **NVIDIA NCA Generative AI LLMs**: data preprocessing and feature engineering, Python libraries for LLMs.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
