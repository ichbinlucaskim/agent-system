# Lab 10 - An MCP-style server

## 목표

이 lab을 마치면 표준 라이브러리만으로 stdio 위에 tool 두 개를 노출하는 최소한의 MCP server를 만들고, 그 tool들을 런타임에 discovery하는 client로 구동하고, agent와 tool 사이의 프로토콜 경계가 그 오버헤드를 감수할 만한 이유를 설명할 수 있습니다.

## 사전 준비

Lab 00, 01, 07. 개념: JSON-RPC 요청과 응답의 형태, `subprocess`, 줄 단위 stdio.

## 예상 소요 시간

60분에서 90분

## 배경

지금까지의 모든 tool은 agent와 같은 프로세스 안의 Python 함수였습니다. 동작하는 가장 단순한 방식이며, 그 과정에서 네 가지를 조용히 결합시킵니다. agent, tool 구현, tool의 의존성, 그리고 tool의 권한입니다.

프로토콜 경계는 그것들을 분리합니다. tool은 자체 프로세스로 실행되고, 문서화된 메시지 형식으로 stdio를 통해 대화하며, 어떤 언어로든 작성될 수 있고, 독립적으로 배포되며, agent보다 좁은 권한 집합을 부여받을 수 있습니다. 그러면 같은 server가 한 agent의 코드베이스가 아니라 그 프로토콜을 쓰는 모든 client에게 서비스합니다.

이 lab은 `2026-07-28` MCP 명세의 형태와 규칙을 따르되 SDK 없이 표준 라이브러리만 씁니다. client 객체 뒤에 숨는 대신 wire format이 눈에 보이게 하기 위해서입니다. 프로토콜의 핵심을 구현하고 나머지는 남겨 두는데, 무엇을 보고 무엇을 보지 않았는지 알 수 있도록 생략한 것들은 맨 끝에 나열해 두었습니다.

메시지 형태는 JSON-RPC입니다. 한 줄에 JSON 객체 하나이며, 각 요청은 id와 method와 params를 담고, 각 응답은 그 id를 그대로 담아 result 또는 error를 반환합니다. stdio 위의 줄 단위 JSON은 HTTP server도 포트도 네트워크 권한도 필요 없으며, 그래서 로컬 tool server의 좋은 기본값입니다.

이 프로토콜은 **상태를 갖지 않으며(stateless)**, 이것이 이해할 가치가 있는 설계 결정입니다. handshake가 없습니다. 이전 버전들은 모든 연결을 `initialize` 호출로 열어 프로토콜 버전과 capability를 한 번 합의하고 그 뒤로는 양쪽이 그것을 가정했지만, 그 method는 사라졌습니다. 대신 모든 요청이 자신의 프로토콜 버전과 capability를 `_meta` 블록에 담아 나릅니다. 즉 요청이 자기완결적이라는 뜻이며, 그래서 어떤 요청이든 어떤 server 인스턴스에 도착해도 되고 server는 누가 호출하는지에 대해 아무것도 들고 있지 않습니다. `server/discover`는 server가 어떤 버전을 쓰는지 물어보기 위해 존재하지만 선택 사항입니다. 이미 아는 client는 곧바로 `tools/list`로 갈 수 있습니다. handshake를 버린 대가는 버전 확인이 이제 매 호출마다 일어난다는 것이며, 그래서 server는 method를 보기 전에 `_meta`부터 검증합니다.

discovery는 이 경계가 값을 하게 만드는 부분입니다. client는 server에 어떤 tool이 있는지 물어보고 이름, description, schema를 빌드 시점이 아니라 런타임에 받습니다. server에 tool을 추가하면 어떤 client도 재배포하지 않고 모든 client가 그 tool을 쓸 수 있게 됩니다. 목록이 컴파일에 박히는 대신 가져오는 것이 되었기 때문에, server는 그것이 얼마나 오래 유효한지도 함께 말해 줍니다. `tools/list`가 `ttlMs`와 `cacheScope`를 반환하므로 client는 매 턴 다시 가져오기와 추측하기 사이에서 고르지 않고 재사용할 수 있습니다. 이것은 server가 tool을 결정적인(deterministic) 순서로 반환할 때만 성립하며, 그 순서는 모델의 prompt cache를 따뜻하게 유지하는 것과도 같은 조건입니다. 그 정의들이 context window에 그대로 들어가기 때문입니다.

경계에는 번역기도 필요한데, 여기서 많이 걸려 넘어집니다. MCP tool 정의와 Messages API tool 정의는 서로 바꿔 쓸 수 있어 보이지만 아닙니다. MCP는 `inputSchema`라고 하는데 모델 API는 `input_schema`라고 하고, MCP는 모델 API가 거부할 `title`이나 `annotations` 같은 필드를 함께 나릅니다. tool result도 같은 문제를 갖는데, MCP는 content 블록의 리스트와 `isError` 플래그를 반환하고 모델 API는 텍스트와 `is_error`를 원합니다. 어느 쪽이든 손대지 않고 그대로 전달하면 버그이고, 그래서 모든 실제 client에는 이런 adapter가 있으며, 그 adapter를 쓰는 것이 요점입니다. 프로토콜은 공유하는 자료 구조가 아니라 따로 설계된 두 시스템 사이의 계약입니다.

에러 처리도 프로토콜의 일부이며, 하나로 뭉개기 쉬운 두 층이 있습니다. 알 수 없는 method, 또는 필수 메타데이터가 빠진 요청은 정의된 코드를 가진 JSON-RPC error 객체입니다. 호출하는 코드의 버그이므로 재시도로는 절대 해결되지 않기 때문입니다. 실행됐다가 실패한 tool은 그 반대로, `isError`로 표시된 평범한 result를 반환합니다. 보통 모델의 실수이고 모델이 그 메시지를 읽고 다시 시도할 수 있기 때문입니다. 이 둘을 뭉개면 모델은 자신이 복구할 수 있었던 유일한 실패를 잃습니다.

세 가지 실패가 더 있는데, 이것들은 어느 한쪽 프로그램이 아니라 경계 자체에 속합니다. stdout은 프로토콜 메시지만 실어야 하므로, server에 `print` 한 줄이 잘못 들어가면 server는 계속 잘 동작하는데 client가 인사말을 디코딩하다 죽습니다. 진단 출력은 stderr로 보내세요. 응답의 id는 장식이 아닙니다. 다음에 도착한 줄을 그냥 돌려주는 client는 뒤처진 응답을 정답인 것처럼 호출자에게 넘기게 되며, 틀린 결과는 발생한 에러보다 훨씬 비쌉니다. 그리고 result는 이제 `resultType`으로 자기 종류를 스스로 밝힙니다. server가 끝내기 전에 추가 입력이 필요하다고 답할 수 있기 때문입니다. 그런 응답을 완료된 result로 읽는 client는 데이터를 지어내는 셈이므로, 알아볼 수 없는 종류는 가정하지 말고 거부해야 합니다.

## 단계

1. `list_tools`를 구현하세요. tool 정의 두 개를 MCP 형태로, `input_schema`가 아니라 `inputSchema`로 반환하며, 목록이 캐시될 수 있도록 결정적인 순서로 반환합니다.
2. `call_tool`을 구현하세요. 이름으로 dispatch하고 인자를 schema에 대해 검증하며, content 블록의 리스트와 `isError` 플래그를 반환합니다. 실패한 호출은 예외를 던지는 대신 에러 result로 표시합니다.
3. `check_request_meta`를 구현하세요. `protocolVersion` 또는 `clientCapabilities`가 빠진 요청은 코드 -32602로 거부하고, 쓰지 않는 버전을 요구하는 요청은 코드 -32022로 거부하면서 client가 다시 시도할 수 있도록 지원하는 버전들을 알려 줍니다.
4. `handle_request`를 구현하세요. 메타데이터를 먼저 검증한 다음 `server/discover`, `tools/list`, `tools/call`을 method로 라우팅하고, 요청 id를 그대로 돌려주며, 모든 result에 `resultType`과 `serverInfo`를 붙이고, `tools/list`에는 캐시 힌트를 붙이며, 알 수 없는 method에는 코드 -32601을 반환합니다. `initialize`는 없습니다.
5. `serve`를 구현하세요. stdin에서 줄 단위 JSON을 읽고 stdout에 한 줄당 하나의 JSON 응답을 쓰며, 프로토콜 메시지가 아닌 것은 stdout에 절대 쓰지 않습니다.
6. `MCPClient`를 구현하세요. `subprocess`로 server를 시작하고, 모든 요청에 프로토콜 메타데이터를 붙이고, 각 응답의 id가 그 요청과 일치하는지 확인하고, 읽을 수 없는 `resultType`은 거부하고, tool 목록을 server가 알려 준 `ttlMs` 동안 캐시하고, 죽은 server는 파이프 에러 원문이 아니라 종료 코드로 보고하며, server가 이미 종료된 경우에도 깔끔하게 종료합니다.
7. `to_messages_api_tools`와 `answer_with_discovered_tools`를 구현하세요. discovery로 받은 정의를 모델 API가 받는 형태로 번역한 뒤 각 `tool_use` 블록을 `tools/call`로 실행하고 그 결과를 다시 번역하며, 이 함수 안에서 tool 이름을 하나도 적지 않습니다. 1~6단계는 파이프가 동작한다는 것만 보여 줍니다. 파이프가 값을 한다는 것을 보여 주는 단계가 이것이므로 여기까지 오기 전에 멈추지 마세요.

## 검증

```bash
pytest labs/track-2-tools-context/10-mcp-server/tests -v
```

프로토콜은 실제 subprocess 왕복을 포함해 오프라인으로 end-to-end 테스트됩니다. 어느 부분도 모델을 필요로 하지 않기 때문입니다. 7단계도 모델을 stub으로 두고 오프라인에서 테스트합니다. 검사 대상은 모델에 건네진 정의가 파이프에서 와서 번역되었는지와 되돌려 보낸 `tool_result`가 server가 실제로 반환한 값인지이며, 둘 다 진짜 completion이 필요하지 않기 때문입니다.

통과했다면 discovery가 유효한 schema와 함께 tool 두 개를 안정된 순서로 반환하고, handshake 없이 `tools/call`이 첫 요청으로 바로 동작하는 반면 `initialize`는 이제 그냥 알 수 없는 method이며, 프로토콜 메타데이터가 빠진 요청은 -32602로 거부되고 지원하지 않는 버전을 말하는 요청은 대안과 함께 -32022로 거부되며, 모든 result가 자기 종류와 자기 server를 밝히고, tool 목록이 캐시 힌트를 실어 보내고 client가 그것을 실제로 지키며, 실패한 tool이 유효한 입력을 알려 주는 에러 result로 돌아오고, MCP 정의가 그대로 전달되지 않고 번역되며, 알 수 없는 method가 크래시 대신 -32601을 반환하고, 잘못된 형식의 줄이 server를 죽이지 않으며, server가 stdout에 쓰는 모든 줄이 JSON으로 파싱되고, id가 일치하지 않는 응답은 반환되지 않고 거부되며, 읽을 수 없는 `resultType`이 완료로 가정되지 않고 거부되고, 죽은 server가 종료 코드로 보고되며, 프로세스가 이미 사라진 경우에도 client가 깔끔하게 종료한다는 뜻입니다.

`main` 실행은 마지막 절에서만 키가 필요하고 키가 없으면 명확한 건너뛰기 메시지를 출력하므로, 이 lab의 프로토콜 절반은 오프라인으로 계속 실행할 수 있습니다.

## 더 나아가기

- agent 프로세스가 읽을 수 없는 디렉터리에서 server를 실행하고 tool이 여전히 동작하는지 확인하세요. 격리에 대한 논거를 구체적으로 확인하는 것입니다.
- client는 건드리지 않고 server에 세 번째 tool을 추가하고, discovery를 통해 그것이 나타나는지 보세요.
- client의 `resultType` 검사를 지우고 `input_required` 응답을 먹여 보세요. client는 에러가 아니라 tool이 0개라고 보고할 것이고, 그것이 "result 형태를 추측하면 데이터를 지어낸다"가 실제로 어떤 모습인지입니다.
- 명세는 예기치 않게 종료된 server를 client가 재시작해야 하고, 다시 세울 세션이 없으므로 진행 중이던 요청은 새 프로세스에 그냥 재시도하면 된다고 말합니다. 그것을 구현해 보고, 한 줄짜리 재시도가 옳은 이유가 바로 statelessness라는 점을 확인하세요.
- 이 lab이 생략한 것들. 만든 것의 경계를 알아 두기 위해서입니다. 긴 tool 목록을 위한 `nextCursor` 페이지네이션, 기계가 읽을 수 있는 result를 위한 `outputSchema`와 `structuredContent`, 진행 중인 호출을 포기하기 위한 `notifications/cancelled`, tool 목록이 바뀔 때 server가 밀어 주는 `subscriptions/listen`, 호출 도중 사용자에게 무언가를 물어야 하는 tool을 위한 multi round-trip request, 그리고 같은 `_meta` 필드를 HTTP 헤더로 나르는 Streamable HTTP transport입니다.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: 프로토콜 경계를 넘는 agent-computer interface 설계, 런타임 tool discovery.
- **Databricks Generative AI Engineer Associate**: MCP server를 포함한 tool and agent framework.
- **NVIDIA NCA Generative AI LLMs**: software development, LLM integration and deployment.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
