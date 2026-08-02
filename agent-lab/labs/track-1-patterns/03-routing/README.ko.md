# Lab 03 - Routing

## 목표

이 lab을 마치면 들어오는 요청을 classify해서 여러 특화 prompt나 model 중 하나로 dispatch하고, 안전한 fallback 경로를 두고, 라벨링된 집합에서 misroute rate를 측정할 수 있습니다.

## 사전 준비

Lab 00부터 02까지. 개념: classification prompt, 그리고 요청 유형이 다르면 처리 방식도 달라야 한다는 발상.

## 예상 소요 시간

30분에서 45분

## 배경

routing은 입력 흐름을 종류별로 나누고 각 종류를 그에 맞게 만들어진 handler로 보냅니다. 환불 문의, 기술적 문제 해결 질문, 마케팅 문구 작성 요청은 공통점이 거의 없으며, 셋을 모두 처리하려는 하나의 prompt는 결국 어느 것도 잘 처리하지 못합니다.

classifier 자체도 모델 호출이며 보통은 작은 호출입니다. 요청을 읽고 닫힌 집합에서 라벨 하나를 반환합니다. 출력 공간이 매우 작기 때문에 자신이 공급하는 handler보다 낮은 effort 설정이나 더 저렴한 model에서 실행할 수 있습니다.

routing은 비용을 난이도에 맞추는 수단이기도 합니다. 단순하고 양이 많은 요청은 빠른 model로 보내고, 어려운 경로만 비싼 model 비용을 치르게 할 수 있습니다. 이는 프로덕션 시스템에서 단일 항목으로는 가장 큰 비용 절감 지렛대인 경우가 많으며, handler 자체는 손댈 필요가 없습니다.

모든 router에는 fallback이 필요합니다. 반드시 선택해야 하는 classifier는 어떤 경로에도 맞지 않는 입력에 대해서도 결국 무언가를 고릅니다. 따라서 명시적인 `other` 라벨을 주고 그 경우에 무엇을 할지 정하세요. 일반 handler, 되묻는 질문, 또는 거절입니다. 조용한 misroute는 정직한 fallback보다 나쁩니다.

misroute rate는 라벨링된 데이터가 있어야만 의미가 있습니다. 요청 서른 개 정도와 각각이 가야 할 경로를 적어 두고, classifier를 그 위에 돌려 불일치를 세세요. 그 수치가 기준선입니다. 기준선이 없으면 classification prompt의 변경은 추측일 뿐이고, 무언가 나아졌는지조차 알 수 없습니다.

## 단계

1. `ROUTES`를 정의하세요. 각 경로 이름을 그 경로를 처리하는 특화 system prompt에 대응시키는 dict이며, `other` fallback을 포함합니다.
2. `classify`를 구현하세요. 정확히 하나의 경로 이름을 반환하는 모델 호출입니다. 반환된 라벨을 `ROUTES`에 대해 검증하고 일치하지 않으면 `other`로 되돌립니다.
3. `handle`을 구현하세요. 선택된 경로의 system prompt로 dispatch하고 답변을 반환합니다.
4. `route_and_answer`를 구현하세요. classify하고 dispatch한 뒤 답변과 선택된 경로를 함께 반환해서 호출자와 로그에 그 결정이 드러나게 합니다.
5. `misroute_rate`를 구현하세요. `(question, expected_route)` 쌍의 라벨링된 리스트에 `classify`를 돌리고 불일치 비율을 반환합니다.
6. `LABELLED_SET`을 `other`를 포함한 모든 경로를 다루는 예시 열두 개 이상으로 채우고, 기준 misroute rate를 주석으로 기록하세요.

## 검증

```bash
pytest labs/track-1-patterns/03-routing/tests -v
```

경로 검증과 misroute 산술은 오프라인으로 실행됩니다. 통과했다면 알 수 없는 라벨이 그대로 전파되지 않고 `other`로 되돌아가고, `route_and_answer`가 선택한 경로를 보고하며, `misroute_rate`가 손으로 센 예시와 일치하는 0에서 1 사이 값을 반환한다는 뜻입니다.

## 더 나아가기

- prompt뿐 아니라 model로도 routing하세요. 가장 단순한 경로를 더 작은 model로 보내고 라벨링된 집합 전체에서 비용 차이를 측정합니다.
- classifier가 라벨과 함께 confidence를 반환하게 하고 임계값 미만은 `other`로 보내세요. misroute rate가 개선되는지 확인합니다.
- 모든 misroute를 손으로 살펴보세요. classifier 실패의 대부분은 model의 실패가 아니라 모호한 경로 정의 때문입니다.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: routing: 입력을 classify해서 특화된 후속 호출로 dispatch하기.
- **Databricks Generative AI Engineer Associate**: problem decomposition and solution design, evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: prompt engineering, experimentation, data analysis and visualization.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
