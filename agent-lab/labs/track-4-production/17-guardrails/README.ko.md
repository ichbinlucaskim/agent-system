# Lab 17 - Guardrails

## 목표

이 lab을 마치면 agent를 그 경계에서 방어할 수 있습니다. 들어오는 것을 걸러 내고, 나가는 것을 schema에 대해 검증하고, tool 결과를 지시가 아니라 신뢰할 수 없는 데이터로 다루고, 범위를 벗어난 요청을 모델에게 정중히 부탁하는 대신 코드로 거절할 수 있습니다.

## 사전 준비

Lab 01, 07, 12, 14. 개념: tool 루프, 그리고 신뢰할 수 없는 콘텐츠가 시스템에 들어오는 지점.

## 예상 소요 시간

45분에서 60분

## 배경

guardrail은 모델이 협조하든 하지 않든 실행되는 코드입니다. system prompt의 지시는 강한 선호일 뿐 그 이상이 아니며, 이 lab의 모든 내용은 선호가 통제가 아니기 때문에 존재합니다.

input filtering은 값싼 계층입니다. 길이를 제한하고, 처리하지 않는 콘텐츠 유형을 거부하고, 명백히 범위를 벗어난 요청을 호출 비용이 발생하기 전에 막습니다. 사고와 물량은 잡아내지만 작정한 공격자는 막지 못하며, 그래서 첫 번째 계층일 뿐입니다.

output validation은 여러분의 시스템이 무엇을 내보내도 되는지 결정하는 지점입니다. 하류 소비자가 세 개의 필드를 가진 객체를 기대한다면, schema로 검증하고 불일치 시 크게 실패해야 합니다. 두 서비스 건너에서 무언가를 망가뜨릴 형태를 그냥 흘려보내서는 안 됩니다.

위험한 입력은 대개 사용자의 message가 아닙니다. tool 결과입니다. 웹 페이지, 데이터베이스 행, 파일, 이메일 같은 것들입니다. 그중 어느 것이든 모델을 겨냥한 텍스트를 담을 수 있으며, 여러분의 prompt가 데이터와 지시를 구분하지 않는다면 모델도 구분할 방법이 없습니다.

완화책은 구조적입니다. 신뢰할 수 없는 콘텐츠를 출처를 명시하고 그 내용이 지시가 아니라 데이터임을 밝히는 명확한 라벨의 블록으로 감싸고, 그것을 들고 있는 동안 agent가 할 수 있는 일을 제한하세요 — 이 lab에서 부모는 `write_note`를 가질 수 있지만 읽기 context는 아무 tool도 노출하지 않습니다. 이전 지시를 무시하라 같은 문구를 훑는 탐지 휴리스틱은 추가할 가치가 있지만, 그것은 벽이 아니라 감지선입니다. 경고는 하되, 그것만으로 막으려 하지 마세요.

범위 거절에는 두 부분이 모두 필요합니다. 모델에게 무엇을 다루지 않는지 알려 주고, 코드로도 검사하세요. 물어봐야만 얻을 수 있는 거절은 injection이 앗아갈 수 있는 거절입니다.

## 단계

1. `check_input`을 구현하세요. 길이 상한과 허용 주제 검사를 적용하고, 거절을 호출자에게 설명할 수 있도록 `(ok, reason)`을 반환합니다.
2. `validate_output`을 구현하세요. 파싱된 payload를 작은 schema에 대해 검사하고 첫 번째 위반만이 아니라 모든 위반을 반환합니다.
3. `wrap_untrusted`를 구현하세요. tool 결과를 출처를 명시하고 그 내용이 지시가 아니라 데이터임을 밝히는 라벨 블록 안에 넣습니다.
4. `detect_injection`을 구현하세요. tool 결과에서 알려진 지시형 패턴을 표시하고, docstring에 이것이 방어가 아니라 감지선임을 명시합니다.
5. `guarded_answer`를 구현하세요. input filter를 실행하고, 문서가 context에 있는 동안 `tools_while_reading_untrusted()`(쓰기 없음)만 노출하며, tool 결과를 감싸고, tripwire 발견은 기록하되 호출을 중단하지 않고, 모델 호출(테스트용으로 주입 가능)을 한 뒤 출력을 검증하고, 답변과 함께 모든 guardrail 결정을 반환합니다.
6. 삽입된 지시(그리고 쓰기 요청)가 들어 있는 문서를 넣으세요. tripwire가 FLAG하고, wrap된 데이터로 호출은 계속되며, 읽기 tool 집합에는 `write_note`가 없음을 확인하세요 — 막는 것은 prompt가 아니라 그 제한입니다.

## 검증

```bash
pytest labs/track-4-production/17-guardrails/tests -v
```

여기의 모든 guardrail은 결정적이며 오프라인으로 테스트됩니다. 그것이 핵심입니다. 테스트할 수 없는 guardrail은 희망일 뿐입니다. 통과했다면 빈 입력·크기 초과·범위 벗어난 입력이 사유와 함께 거절되고, schema 검증이 모든 위반을 한 번에 보고하며(bool을 number로 받는 경우 포함), 신뢰할 수 없는 콘텐츠에 출처 라벨이 붙고, 알려진 injection 문구가 호출을 중단하지 않는 tripwire로 표시되며, 신뢰 불가 콘텐츠를 읽는 동안 쓰기가 없고, 잘못된 모델 출력은 보류되며, 결과가 답변과 함께 guardrail 결정을 담는다는 뜻입니다.

## 더 나아가기

- 탐지기가 놓치는 injection 시도 다섯 개를 작성한 뒤, 그중 어떤 것이 어차피 tool 제한으로 막히는지 판단하세요.
- schema 검사를 최종 출력뿐 아니라 tool 결과에도 적용하고, 그것이 어떤 실패를 더 일찍 잡아내는지 기록하세요.
- 정상적인 요청이 input filter에 얼마나 자주 걸리는지 측정하세요. false positive 비율이 높은 guardrail은 누군가에 의해 꺼지게 됩니다.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: agent-computer interface에서의 guardrail, tool 결과를 신뢰할 수 없는 데이터로 다루기.
- **Databricks Generative AI Engineer Associate**: governance, RAG 및 LLM chain을 포함한 application development.
- **NVIDIA NCA Generative AI LLMs**: alignment, prompt engineering, software development.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
