# Lab에서 cloud와 library로

lab이 가르치는 것은 메커니즘입니다. cloud 서비스와 library는 그 메커니즘이
무엇이 지켜져야 하는지 알게 된 뒤에 붙이는 배관과 부품입니다. 이 문서는
배포 가이드가 아니라 대응표입니다. 과정을 끝내는 데 필수는 아닙니다.

## 층별 한 줄

| lab이 가르치는 것 | 프로덕션에서 보통 앉는 자리 |
| --- | --- |
| Messages API와 tool loop | 모델 SDK (Anthropic, Bedrock)와 agent runtime |
| RAG와 vector | OpenSearch, PGVector, 또는 S3와 embedding 경로 |
| MCP / tool server | Lambda, ECS 서비스, 또는 API Gateway 뒤 worker |
| Agent loop와 예산 | 앱 코드, 필요하면 Step Functions나 queue로 hard limit |
| Subagent | 별도 task나 container, 종종 SQS로 fan-out |
| Human in the loop | 승인 UI와 내구성 있는 상태 (DynamoDB, EventBridge, Step Functions Wait) |
| Evaluation | 케이스와 리포트를 object storage에 쓰는 batch job |
| Observability | CloudWatch, X-Ray, 또는 OpenTelemetry exporter |
| Guardrail | 앱 코드가 먼저, 선택적으로 managed guardrail 제품 |
| Packaging (CLI와 HTTP) | FastAPI 등 + Lambda, ECS, 또는 App Runner |

lab 18이 이미 말한 형태입니다. core (`answer()` / `agent_loop()`)는 하나이고
바깥 adapter만 바꿉니다.

## 전형적인 AWS 스케치

```text
User
  -> API Gateway / ALB
  -> Lambda or ECS (HTTP adapter)     # lab 18
       -> answer() / agent_loop()     # labs 01 through 14
            -> Bedrock or Anthropic API
            -> S3 / DynamoDB / OpenSearch (tools and documents)
            -> SQS workers (subagents)
  -> CloudWatch and X-Ray             # lab 16
  -> (batch) Eval job on Fargate      # lab 15
```

역할 힌트:

- **Compute.** 짧은 request/response는 Lambda, agent loop나 MCP server가
  function timeout보다 길 수 있으면 ECS 또는 Fargate.
- **Model.** Bedrock, 또는 공개 Anthropic API와 Secrets Manager에 둔 key.
- **State와 memory.** DynamoDB, ElastiCache, 또는 scratchpad·transcript용 S3
  (lab 11).
- **Retrieval.** OpenSearch Serverless 또는 Aurora PGVector (lab 08, 09).
- **비동기와 hard limit.** fan-out, 승인, wall-clock 한도에는 SQS와 Step
  Functions. lab 12의 프로세스 안 예산(`max_steps`, `max_usd`, `max_seconds`)과
  나란히 둡니다.
- **Config.** 체크인된 `.env` 대신 SSM Parameter Store 또는 Secrets Manager
  (lab 18).
- **Observability.** CloudWatch metrics와 logs, X-Ray 또는 OpenTelemetry로
  metrics backend (lab 16).

코드 예산과 플랫폼 limit은 겹칩니다. lab 12가 loop를 멈추고, 그 바깥에는
동시성 cap, timeout, 계정 quota가 그대로 있습니다.

## 흔한 library가 앉는 자리

| 층 | 흔한 선택 | lab과의 관계 |
| --- | --- | --- |
| Model SDK | `anthropic`, `boto3` (Bedrock) | `common.client`를 대체하거나 감쌈 |
| HTTP | FastAPI, Starlette | lab 18의 stdlib HTTP adapter 대체 |
| Agent framework | LangGraph, CrewAI, Claude Agent SDK 등 | lab 12~14의 loop를 대신 구현하기도 함 |
| RAG | LlamaIndex, 또는 vector client 직접 | DIY store 없이 lab 08, 09 |
| Observability | OpenTelemetry, LangSmith, Braintrust | lab 16이 기록한 것을 export |
| Validation | Pydantic | lab 17의 `validate_output`과 같은 일 |
| Infra | Terraform 또는 CDK, Docker | lab packaging 표면의 바깥 |

구분이 유용합니다.

- **framework**는 loop, tool, memory wiring을 제공합니다.
- **lab**은 그 wiring이 무엇을 보장해야 하는지 가르칩니다.

많은 프로덕션 시스템은 FastAPI와 모델 SDK만으로 시작하고, workflow graph가
그 복잡도를 정당화할 때만 더 무거운 framework를 올립니다. framework가 예산,
승인 정책, guardrail을 강제하지 않으면 그것들은 여전히 여러분의 코드에
있어야 합니다.

## 한 줄 요약

lab은 무엇이 지켜져야 하는지를 정합니다. library는 그것을 어떻게 빨리
만들지를 돕습니다. cloud는 어디서 돌리고, 상태를 두고, 관측할지의 실행
환경입니다.

## Worked example

`projects/support-desk`는 system-design case 06을 작은 반품·환불 데스크로
구현합니다. routing, policy RAG, 예산 있는 agent loop, HITL, tool 계층
policy 강제, 행동 단위 eval, packaging이 한곳에 있습니다. lab을 마친 뒤
full pipeline을 한곳에서 보고 싶을 때 돌리세요.
