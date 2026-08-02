# Lab 10 - An MCP-style server

## 목표

이 lab을 마치면 표준 라이브러리만으로 stdio 위에 tool 두 개를 노출하는 최소한의 MCP 스타일 server를 만들고, client 루프로 구동하고, agent와 tool 사이의 프로토콜 경계가 그 오버헤드를 감수할 만한 이유를 설명할 수 있습니다.

## 사전 준비

Lab 00, 01, 07. 개념: JSON-RPC 요청과 응답의 형태, `subprocess`, 줄 단위 stdio.

## 예상 소요 시간

60분에서 90분

## 배경

지금까지의 모든 tool은 agent와 같은 프로세스 안의 Python 함수였습니다. 동작하는 가장 단순한 방식이며, 그 과정에서 네 가지를 조용히 결합시킵니다. agent, tool 구현, tool의 의존성, 그리고 tool의 권한입니다.

프로토콜 경계는 그것들을 분리합니다. tool은 자체 프로세스로 실행되고, 문서화된 메시지 형식으로 stdio를 통해 대화하며, 어떤 언어로든 작성될 수 있고, 독립적으로 배포되며, agent보다 좁은 권한 집합을 부여받을 수 있습니다. 그러면 같은 server가 한 agent의 코드베이스가 아니라 그 프로토콜을 쓰는 모든 client에게 서비스합니다.

메시지 형태는 JSON-RPC입니다. 한 줄에 JSON 객체 하나이며, 각 요청은 id와 method와 params를 담고, 각 응답은 그 id를 그대로 담아 result 또는 error를 반환합니다. stdio 위의 줄 단위 JSON은 HTTP server도 포트도 네트워크 권한도 필요 없으며, 그래서 로컬 tool server의 좋은 기본값입니다.

discovery는 이 경계가 값을 하게 만드는 부분입니다. client는 server에 어떤 tool이 있는지 물어보고 이름, description, schema를 빌드 시점이 아니라 런타임에 받습니다. server에 tool을 추가하면 어떤 client도 재배포하지 않고 모든 client가 그 tool을 쓸 수 있게 됩니다.

비용은 실재하며 짚고 넘어갈 가치가 있습니다. 직렬화, 프로세스 수명 관리, 그리고 더 어려워진 디버깅입니다. 이제 크래시는 파이프 반대편에서 일어나기 때문입니다. 하나의 agent가 쓰는 하나의 tool이라면 평범한 함수가 옳은 선택입니다. 경계는 tool이 여러 agent에 공유되거나, 격리가 필요하거나, 다른 팀의 소유일 때 값을 합니다.

에러 처리도 프로토콜의 일부이지 나중에 붙이는 것이 아닙니다. 알 수 없는 method는 stderr의 스택 트레이스가 아니라 정의된 코드를 가진 JSON-RPC error 객체이며, 실패한 tool은 모델이 읽고 복구할 수 있도록 에러로 표시된 result를 반환합니다.

## 단계

1. `list_tools`를 구현하세요. 이름, description, input schema를 담은 tool 정의 두 개를 Messages API가 기대하는 형태 그대로 반환합니다.
2. `call_tool`을 구현하세요. 이름으로 dispatch하고 인자를 schema에 대해 검증하며, 호출이 실패하면 에러로 표시된 result를 반환합니다.
3. `handle_request`를 구현하세요. 디코딩된 JSON-RPC 객체를 method로 라우팅하고, 요청 id를 그대로 돌려주며, 알 수 없는 method에는 코드 -32601의 올바른 error 객체를 반환합니다.
4. `serve`를 구현하세요. stdin에서 줄 단위 JSON을 읽고 stdout에 한 줄당 하나의 JSON 응답을 쓰며, 프로토콜 메시지가 아닌 것은 stdout에 절대 쓰지 않습니다.
5. `MCPClient`를 구현하세요. `subprocess`로 server를 시작하고, 요청을 보내고, 응답을 읽고, server가 이미 종료된 경우에도 깔끔하게 종료합니다.
6. 발견된 tool을 lab 01의 augmented call에 연결해서, agent가 컴파일 시점에 알지 못했던 tool을 사용하게 하세요.

## 검증

```bash
pytest labs/track-2-tools-context/10-mcp-server/tests -v
```

프로토콜은 실제 subprocess 왕복을 포함해 오프라인으로 end-to-end 테스트됩니다. 어느 부분도 모델을 필요로 하지 않기 때문입니다. 통과했다면 discovery가 유효한 schema와 함께 tool 두 개를 반환하고, 호출이 실행되어 result를 반환하며, 알 수 없는 method가 크래시 대신 에러 코드 -32601을 반환하고, 잘못된 형식의 줄이 server를 죽이지 않으며, client가 프로세스를 깔끔하게 종료한다는 뜻입니다.

## 더 나아가기

- agent 프로세스가 읽을 수 없는 디렉터리에서 server를 실행하고 tool이 여전히 동작하는지 확인하세요. 격리에 대한 논거를 구체적으로 확인하는 것입니다.
- client는 건드리지 않고 server에 세 번째 tool을 추가하고, discovery를 통해 그것이 나타나는지 보세요.
- 호출 도중 server를 죽이고, client가 영원히 멈춰 있지 않고 명확한 실패를 보고하게 만드세요.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: 프로토콜 경계를 넘는 agent-computer interface 설계, 런타임 tool discovery.
- **Databricks Generative AI Engineer Associate**: MCP server를 포함한 tool and agent framework.
- **NVIDIA NCA Generative AI LLMs**: software development, LLM integration and deployment.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
