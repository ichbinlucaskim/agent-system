# Lab 09 - Retrieval quality

## 목표

이 lab을 마치면 retrieval을 추측하지 않고 측정할 수 있습니다. 라벨링된 집합에 대해 recall@k를 계산하고, chunk 크기를 sweep하고, keyword와 vector 점수를 hybrid ranking으로 결합하고, reranking 단계를 추가할 수 있습니다.

## 사전 준비

Lab 08. 개념: recall@k, 그리고 지표 없는 retrieval 변경은 동전 던지기라는 발상.

## 예상 소요 시간

60분에서 90분

## 배경

이 lab은 선택 사항으로 표시되어 있습니다. lab 08의 pipeline이 이미 동작하기 때문입니다. 그러나 이 lab은 그 pipeline이 잘 동작하는지를 결정하는 lab이며, 실제 시스템에서는 품질의 대부분이 보통 여기서 나옵니다.

recall@k는 좁고 답할 수 있는 질문을 던집니다. 검색됐어야 할 구절 중 몇 개가 상위 k개 안에 나타났는가입니다. 라벨링된 집합이 필요하며, 작은 corpus라면 질의 스무 개와 각각을 답하는 chunk를 적어 두는 정도입니다. 그 반나절의 라벨링이 이후의 모든 변경을 의견에서 측정으로 바꿔 줍니다.

chunk 크기에는 보편적인 정답이 없고, 그래서 sweep을 합니다. 질의와 라벨을 고정한 채 여러 크기로 store를 다시 만들고 크기 대비 recall을 그려 보세요. 곡선에는 대개 넓은 평탄 구간이 있으며, 단일 최적점을 찾는 것보다 그 평탄 구간이 어디서 시작되는지 아는 것이 더 중요합니다.

keyword 검색과 vector 검색은 서로 다른 방향으로 실패합니다. vector 검색은 다른 단어로 같은 뜻을 담은 구절을 찾아냅니다. keyword 검색은 embedding이 이웃과 뭉개 버리는 정확한 식별자, 에러 코드, 제품명을 찾아냅니다. hybrid scoring은 둘의 가중합을 취하며, 가중치는 어디선가 베껴 오는 상수가 아니라 라벨링된 집합에서 조정하는 손잡이입니다.

reranking은 후보 목록에 대한 두 번째이자 더 비싼 단계입니다. 저렴하게 스무 개를 검색한 뒤 그 스무 개를 정밀하게 점수화해 상위 세 개만 남깁니다. 스무 개 후보를 정밀하게 순위 매기는 것은 감당할 수 있지만 corpus 전체를 그렇게 하는 것은 불가능하기 때문에 동작하며, 보통 chunk 크기를 한 번 더 조정하는 것보다 큰 이득을 줍니다.

## 단계

1. `LABELLED_QUERIES`를 작성하세요. lab 08 corpus에 대한 `(query, relevant_chunk_ids)` 쌍을 최소 열다섯 개 만듭니다. 이 lab의 나머지 전부가 이 리스트의 정직함에 달려 있습니다.
2. `recall_at_k`를 구현하세요. 검색된 id와 관련 id가 주어지면, 관련 id 중 상위 k개 안에 나타난 비율을 반환합니다.
3. `sweep_chunk_sizes`를 구현하세요. 여러 chunk 크기로 store를 다시 만들고 각각의 recall@k를 반환해서 절충 관계가 표로 드러나게 합니다.
4. `hybrid_score`를 구현하세요. 정규화된 keyword 점수와 정규화된 vector 점수를 가중치 alpha로 결합하고, alpha가 0과 1일 때 각각 순수 전략이 재현되는지 확인합니다.
5. `rerank`를 구현하세요. 후보 목록을 받아 더 정밀한 점수화 단계로 재정렬하며, 동일한 결과 집합을 새로운 순서로 반환합니다.
6. `evaluate`를 구현하세요. 같은 라벨링된 집합에서 vector, keyword, hybrid, rerank 전략의 recall@k를 하나의 표로 보고합니다.

## 검증

```bash
pytest labs/track-2-tools-context/09-retrieval-quality/tests -v
```

이 lab의 모든 지표는 산술이며 오프라인으로 실행됩니다. 통과했다면 recall@k가 경계 사례를 포함해 손으로 센 예시와 일치하고, sweep이 chunk 크기마다 하나씩 항목을 반환하며, hybrid scoring이 alpha의 양 극단에서 순수 전략으로 환원되고, reranking이 후보를 조용히 버리지 않고 입력의 순열을 반환한다는 뜻입니다.

## 더 나아가기

- corpus에 한 번도 등장하지 않는 동의어를 쓰는 질의를 추가하고, hybrid scoring이 그 격차를 얼마나 메우는지 보세요.
- 같은 전략들에 대해 recall@1, recall@3, recall@10을 측정하세요. 10에서는 이기고 1에서는 지는 전략은 reranking의 기회입니다.
- reranking 단계의 소요 시간을 재고, 그것이 사 오는 recall이 대화형 애플리케이션의 지연을 감수할 만한지 판단하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: context engineering의 일부로서의 retrieval 품질: 올바른 token을 window에 넣기.
- **Databricks Generative AI Engineer Associate**: data preparation and chunking, custom scorer를 포함한 evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: data analysis and visualization, experimentation, data preprocessing and feature engineering.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
