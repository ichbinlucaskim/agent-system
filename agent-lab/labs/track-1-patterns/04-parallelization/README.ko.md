# Lab 04 - Parallelization

## 목표

이 lab을 마치면 유용한 두 가지 형태로 모델 호출을 동시에 실행할 수 있습니다. 독립적인 하위 작업을 여러 호출로 나누는 sectioning과, 같은 작업을 여러 번 실행해 답을 집계하는 voting입니다.

## 사전 준비

Lab 00부터 03까지. 개념: 독립적인 하위 작업과 의존적인 하위 작업의 구분, 그리고 Python의 `concurrent.futures`.

## 예상 소요 시간

45분에서 60분

## 배경

parallelization은 하위 작업들이 서로 의존하지 않을 때 적용됩니다. 2단계가 1단계의 출력을 필요로 한다면 그것은 chain이며 lab 02에 속합니다. 하위 작업을 어떤 순서로든 답할 수 있다면, 동시에 실행함으로써 지연 시간의 합을 지연 시간의 최댓값으로 바꿀 수 있습니다.

sectioning은 하나의 작업을 독립적인 부분들로 나누고 부분마다 호출을 하나씩 실행한 뒤 결과를 병합합니다. 문서를 정확성, 어조, 법적 위험 관점에서 검토하는 것은 서로 다른 세 번의 읽기이며, 각각에 별도 호출을 주면 한 호출이 주의를 셋으로 나누는 대신 각자가 집중된 prompt와 온전한 주의 예산을 갖게 됩니다.

voting은 같은 작업을 여러 번 실행하고 집계합니다. 모델 출력은 실행마다 달라지므로 실행 간의 일치는 증거가 되고 불일치는 상위 확인이 필요하다는 신호가 됩니다. 안전한가, 컴파일되는가, 중복인가처럼 답의 공간이 작은 판단에 잘 맞습니다.

집계 방식은 나중에 생각할 문제가 아니라 설계 결정입니다. 다수결이 가장 뻔한 규칙이지만, false positive의 대가가 클 때는 만장일치가 맞고, 탐지 실패의 대가가 클 때는 하나라도 yes면 yes로 보는 규칙이 맞습니다. 답변과 함께 일치 수준도 보고해서 호출자가 실제로 표들이 얼마나 일치했는지 알 수 있게 하세요.

여기서 Python의 동시성 비용은 거의 없습니다. 작업이 CPU가 아니라 네트워크에 묶여 있기 때문입니다. `ThreadPoolExecutor`면 충분합니다. 정작 비용이 드는 것은 돈과 rate limit입니다. 표 N개는 token N배를 뜻하며, 넓은 fan-out은 직렬 버전이라면 걸리지 않았을 rate limit에 걸릴 수 있습니다.

## 단계

1. `section`을 구현하세요. 검토 작업을 각각 고유한 지시를 가진 독립적인 관점들의 고정 리스트로 나눕니다.
2. `run_sections`를 구현하세요. `ThreadPoolExecutor`로 section마다 호출을 하나씩 동시에 실행하고, 완료 순서와 무관하게 원래 section 순서대로 결과를 반환합니다.
3. `merge_sections`를 구현하세요. section 결과들을 하나의 리포트로 합치되, 산문으로 뒤섞지 말고 각 section에 라벨을 유지합니다.
4. `vote`를 구현하세요. 같은 질문을 n번 동시에 실행하고 답변을 모읍니다.
5. `majority`를 구현하세요. 가장 흔한 답변과 그에 동의한 표의 비율을 함께 반환하되, 동점은 결정적으로 처리해 같은 표 집합이면 항상 같은 결과가 나오게 합니다.
6. 동시 실행 상한을 추가하고, 호출 하나가 실패하면 배치 전체를 잃지 말고 해당 자리에 에러를 기록하세요.

## 검증

```bash
pytest labs/track-1-patterns/04-parallelization/tests -v
```

집계와 순서 유지는 결정적이며 오프라인으로 테스트됩니다. 통과했다면 완료 순서가 뒤바뀌어도 sectioning이 순서를 보존하고, majority가 최빈 답변과 일치 비율을 보고하며, 동점이 매번 같은 방식으로 해소되고, 호출 하나의 실패가 나머지 결과를 잃게 하지 않는다는 뜻입니다.

## 더 나아가기

- 동일한 sectioning 작업의 직렬 버전과 동시 실행 버전의 실제 소요 시간을 측정하고, 추가로 지출한 token과 견주어 보세요.
- 안전성 관련 질문에서 집계 규칙을 다수결에서 만장일치로 바꾸고, 각 규칙이 어떤 오류를 대신 감수하는지 설명하세요.
- 표 수를 셋에서 일곱으로 늘리고, 비용이 두 배 이상 늘어난 것을 정당화할 만큼 일치도가 올라가는지 확인하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: parallelization의 두 변형인 sectioning과 voting.
- **Databricks Generative AI Engineer Associate**: problem decomposition and solution design, evaluation and monitoring.
- **NVIDIA NCA Generative AI LLMs**: software development, experimentation.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
