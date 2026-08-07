# Lab 16 - Observability

## 목표

이 lab을 마치면 실행의 모든 step에 대해 구조화된 trace를 기록하고, 비용과 지연을 실행 전체가 아니라 개별 step에 귀속시키고, 실행이 예산을 어디에 썼는지 보여 주는 텍스트 리포트를 렌더링할 수 있습니다.

## 사전 준비

Lab 12, 15, 그리고 `common/tracing.py`와 `common/cost.py`. 개념: 비용의 단위로서의 token usage.

## 예상 소요 시간

45분에서 60분

## 배경

이 lab은 선택 사항으로 표시되어 있습니다. 앞선 lab들이 이것 없이도 동작하기 때문입니다. 하지만 누군가 왜 이 실행이 이 비용이 들었는지 묻는 순간 선택 사항이 아니게 됩니다. 실행 총계로는 답할 수 없고 step별 trace로는 답할 수 있기 때문입니다.

step마다 기록 하나이며, 그 기록은 로그 한 줄이 아니라 구조화된 데이터입니다. step 이름, 입력, 출력, 소요 시간, token usage, 에러입니다. 구조화된 기록은 합산하고 정렬하고 그룹화할 수 있지만, 로그 줄은 그 시각에 당직인 사람이 파싱해야 합니다.

step 단위로 귀속시키세요. 그것이 조치를 취할 수 있는 수준이기 때문입니다. 예상보다 세 배 비쌌던 실행으로는 아무것도 할 수 없습니다. synthesis step이 모든 worker의 전체 출력을 받아 input token의 80퍼센트를 차지했다는 사실로는 즉시 조치할 수 있습니다.

지연과 비용은 서로 다른 질문이며 답도 다른 경우가 많습니다. 가장 느린 step이 가장 비싼 step이 아닌 경우가 흔하고, 엉뚱한 쪽을 최적화하는 것은 일주일을 헛되이 쓰는 흔한 방법입니다. 둘 다 step별로 나란히 보고하세요.

실패도 성공만큼 정성껏 기록하세요. 에러가 난 step도 token과 시간을 소비했으며, 성공한 step만 담긴 trace는 재시도 중인 시스템의 비용을 체계적으로 과소 보고하게 됩니다.

리포트는 평문으로 유지하세요. 터미널에서도, CI 출력에서도, pull request 댓글에서도 동작하며, 실행할 서비스도 추가할 의존성도 없습니다. 나중에 호스팅 tracing 제품으로 옮길 때, 여기서 설계한 기록이 그대로 대응됩니다.

## 단계

1. `common/tracing.py`의 `StepRecord`와 `Trace`를 구조화된 기록으로 쓰세요. 실행에 필드가 더 필요하면 추가하되, 모든 필드가 합산 또는 정렬 가능하도록 유지하세요.
2. `trace_step`을 구현하세요. 임의의 callable을 감싸서 호출 지점마다 기록 코드를 쓰지 않고도 이름, 소요 시간, usage, 에러를 기록하게 합니다.
3. `attribute_cost`를 구현하세요. `common/cost.py`로 step별 usage를 step별 금액으로 변환하고, 같은 이름 step은 합산하며, 부분의 합이 전체와 같은지 검증합니다.
4. `slowest_steps`와 `costliest_steps`를 구현하세요. 각 기준의 상위 n개를 반환하며, 보통 서로 다른 step입니다.
5. `render_report`를 구현하세요. step마다 한 줄로 소요 시간, token, 비용, 에러 노트를 보여 주고, 그다음 합계, 그다음 두 개의 상위 n 목록을 출력합니다.
6. orchestrator 형태 실행을 trace 아래에서 시뮬레이트하세요(plan, workers, synthesize, 실패 하나). 리포트를 출력하고 비용을 지배하는 단일 step을 찾아내세요. 같은 wrapper를 실제 lab 05 orchestrator에 감싸면 됩니다.

## 검증

```bash
pytest labs/track-4-production/16-observability/tests -v
```

tracing과 귀속은 순수한 기록 작업이며 오프라인으로 테스트됩니다. 통과했다면 각 step이 응답에서 복사한 token usage와 함께 정확히 한 번 기록되고, 예외가 발생한 step도 에러와 함께 기록되며(그 에러가 리포트에도 나타나고), step별 비용의 합이 실행 총계와 같으며(같은 이름 step 합산 포함), 가장 느린 step과 가장 비싼 step이 다를 수 있고, 리포트가 모든 step 이름과 두 상위 n 섹션을 담아 조용히 빠진 것이 없다는 뜻입니다.

## 더 나아가기

- 같은 작업의 캐시 적용 실행과 미적용 실행을 비교하고, 실제 소요 시간이 아니라 cache read token에서 그 차이를 읽어 내세요.
- 한 step이 실행 총계에서 일정 비율을 넘으면 발동하는 step 예산 경고를 추가하고, 그 비율을 의도적으로 정하세요.
- 같은 기록을 JSON lines로 내보내고, 텍스트 리포트가 보여 주는 모든 것이 거기서 다시 계산될 수 있는지 확인하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: agent 실행을 위한 observability, step별 context와 비용 측정.
- **Databricks Generative AI Engineer Associate**: MLflow tracing을 포함한 evaluation and monitoring, assembling and deploying applications.
- **NVIDIA NCA Generative AI LLMs**: data analysis and visualization, software development, experimentation.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
