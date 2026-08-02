# Lab 18 - Packaging and deployment

## 목표

이 lab을 마치면 표준 라이브러리만으로 agent를 CLI와 얇은 HTTP handler 양쪽으로 감싸고, 설정을 전적으로 environment로 주입하고, smoke test로 그것이 기동하고 응답한다는 것을 증명할 수 있습니다.

## 사전 준비

Lab 12, 15, 16, 17. 개념: environment 기반 설정, `argparse`, `http.server`.

## 예상 소요 시간

45분에서 60분

## 배경

이 lab은 선택 사항으로 표시되어 있습니다. agent 설계가 아니라 packaging을 가르치기 때문입니다. 여기가 agent가 내 컴퓨터에서만 동작하는 스크립트이기를 그만두는 지점이며, 작업의 대부분은 결국 모델이 아니라 설정과 실패에 관한 것으로 드러납니다.

진입점은 둘, 핵심은 하나입니다. CLI와 HTTP handler는 모두 같은 함수 위의 얇은 어댑터여야 합니다. 그렇지 않으면 둘은 갈라지고, 한쪽에서 고친 버그가 한 달 뒤 다른 쪽을 통해 돌아옵니다.

설정은 environment에서 오며, 최초 사용 시점이 아니라 기동 시점에 검증됩니다. 문제없이 시작한 뒤 한 시간 후 첫 요청에서 실패하는 프로세스는, 시작을 거부하며 어떤 변수가 없는지 말해 주는 프로세스보다 훨씬 진단하기 어렵습니다.

여기의 HTTP handler는 `http.server`이며, 프로덕션 서버가 아니고 그런 척해서도 안 됩니다. 요청을 파싱하고, 핵심을 호출하고, 응답을 직렬화하고, 의미 있는 상태 코드를 반환하는 형태를 보여 주기 위해 존재합니다. 나중에 실제 서버로 교체하면 어댑터가 바뀔 뿐 agent는 바뀌지 않습니다.

health check는 모델에 의존해서는 안 됩니다. API 호출을 하는 `/health` 엔드포인트는 매 probe마다 비용이 들고, 여러분의 가용성이 아니라 제공자의 가용성을 보고합니다. 프로세스가 살아 있고 올바르게 설정되었음을 보고하고, 상위 의존성 확인은 별도의 더 깊은 probe에 맡기세요.

smoke test는 정직한 최소한의 배포 검사입니다. 기동하는가, 응답하는가, 잘못된 형식의 요청이 스택 트레이스 대신 깔끔한 에러를 내는가. 품질 평가가 아니며 그것은 lab 15의 일입니다. 둘을 혼동하면 파이프라인은 초록색인데 agent는 모든 것에 틀리게 답하는 상태가 됩니다.

## 단계

1. `Config`와 `load_config`를 정의하세요. 모든 설정을 environment에서 읽고 기본값을 적용하며, 필수 변수가 없으면 그 이름을 명시하는 명확한 에러를 발생시킵니다.
2. `answer`를 구현하세요. 두 진입점이 모두 호출하는 단일 핵심 함수이며, 질문을 받아 구조화된 결과를 반환합니다.
3. `build_parser`와 `run_cli`를 구현하세요. 인자를 파싱하고 `answer`를 호출하고 결과를 출력하며, 셸이 분기할 수 있도록 실패 시 0이 아닌 종료 코드를 반환합니다.
4. `AgentHandler`를 구현하세요. 모델을 전혀 건드리지 않는 `/health` 엔드포인트와, 잘못된 입력에는 400을, 그 외에는 JSON 본문과 함께 200을 반환하는 POST 엔드포인트를 가진 `BaseHTTPRequestHandler`입니다.
5. `smoke_test`를 구현하세요. 서버를 기동하고 `/health`를 호출하고, 잘못된 형식의 요청 하나와 유효한 요청 하나를 보낸 뒤, 단일 통과 또는 실패를 보고합니다.
6. 필요한 environment variable을 모듈 docstring에 문서화하고, 그것들이 없으면 프로세스가 기동을 거부하는지 확인하세요.

## 검증

```bash
pytest labs/track-4-production/18-packaging-deploy/tests -v
```

설정, 인자 파싱, HTTP 상태 처리는 오프라인으로 테스트됩니다. 통과했다면 필수 변수 누락이 기동 시점에 이름과 함께 보고되고, API key가 없어도 `/health`가 200을 반환하며, 잘못된 형식의 JSON이 트레이스백 대신 400을 반환하고, CLI가 실패 시 0이 아닌 종료 코드를 반환하며, 두 진입점이 같은 핵심 함수를 호출한다는 뜻입니다.

## 더 나아가기

- 모든 응답에 request id를 추가하고 lab 16의 trace에 연결해서, 로그 한 줄이 하나의 완전한 실행으로 이어지게 하세요.
- handler에 동시성 제한을 추가하고, 거부된 요청이 무엇을 받아야 할지 결정하세요. 429인지, 큐인지, 대기인지입니다.
- 일부러 잘못 설정한 environment에 smoke test를 실행하고, 실패 메시지가 어떤 변수가 잘못되었는지 말해 주는지 확인하세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: agent를 프로덕션으로 옮기기: 얇은 진입점 뒤의 하나의 핵심.
- **Databricks Generative AI Engineer Associate**: assembling and deploying applications, governance.
- **NVIDIA NCA Generative AI LLMs**: LLM integration and deployment, software development.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
