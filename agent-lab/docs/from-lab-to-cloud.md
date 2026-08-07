# From lab to cloud and libraries

The labs teach the mechanisms. Cloud services and libraries are plumbing and
parts you bolt on after you know what must stay true. This note is a map, not a
deployment guide. Nothing here is required to finish the course.

## One sentence per layer

| What the labs teach | Where it usually sits in production |
| --- | --- |
| Messages API and the tool loop | Model SDK (Anthropic, Bedrock) and your agent runtime |
| RAG and vectors | OpenSearch, PGVector, or S3 plus an embedding path |
| MCP / tool servers | Lambda, ECS services, or workers behind API Gateway |
| Agent loop and budgets | Application code, optionally with Step Functions or a queue for hard limits |
| Subagents | Separate tasks or containers, often fan-out over SQS |
| Human in the loop | Approval UI plus durable state (DynamoDB, EventBridge, Step Functions Wait) |
| Evaluation | Batch jobs writing cases and reports to object storage |
| Observability | CloudWatch, X-Ray, or OpenTelemetry exporters |
| Guardrails | Application code first; optionally a managed guardrail product |
| Packaging (CLI and HTTP) | FastAPI or similar behind Lambda, ECS, or App Runner |

Lab 18 already states the shape: keep one core (`answer()` / `agent_loop()`),
swap only the outer adapters.

## A typical AWS sketch

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

Role hints:

- **Compute.** Lambda for short request/response paths; ECS or Fargate when the
  agent loop or an MCP server may run longer than a function timeout.
- **Model.** Bedrock, or Anthropic over the public API with the key in Secrets
  Manager.
- **State and memory.** DynamoDB, ElastiCache, or S3 for scratchpads and
  transcripts (lab 11).
- **Retrieval.** OpenSearch Serverless or Aurora with PGVector (labs 08 and 09).
- **Async and hard limits.** SQS and Step Functions for fan-out, approvals, and
  wall-clock ceilings that sit beside the in-process budgets from lab 12
  (`max_steps`, `max_usd`, `max_seconds`).
- **Config.** SSM Parameter Store or Secrets Manager instead of a checked-in
  `.env` (lab 18).
- **Observability.** CloudWatch metrics and logs; X-Ray or OpenTelemetry into
  your metrics backend (lab 16).

Code budgets and platform limits stack. Lab 12 stops the loop; concurrency
caps, timeouts, and account quotas still apply around it.

## Where common libraries fit

| Layer | Common choices | Relation to the labs |
| --- | --- | --- |
| Model SDK | `anthropic`, `boto3` (Bedrock) | Replaces or wraps `common.client` |
| HTTP | FastAPI, Starlette | Replaces the stdlib HTTP adapter in lab 18 |
| Agent frameworks | LangGraph, CrewAI, Claude Agent SDK, and similar | May implement the loop from labs 12 through 14 for you |
| RAG | LlamaIndex, or a vector client directly | Labs 08 and 09 without the DIY store |
| Observability | OpenTelemetry, LangSmith, Braintrust | Export what lab 16 records |
| Validation | Pydantic | Same job as `validate_output` in lab 17 |
| Infra | Terraform or CDK, Docker | Outside the lab packaging surface |

A useful distinction:

- A **framework** supplies loop, tools, and memory wiring.
- The **labs** teach what that wiring must guarantee.

Many production systems ship with FastAPI plus a model SDK and only add a
heavier framework when the workflow graph earns the complexity. If a framework
does not enforce your budgets, approval policy, or guardrails, those still
belong in your code.

## The one-line summary

Labs decide what must stay true. Libraries speed up how you build it. Cloud is
where it runs, stores state, and gets observed.
