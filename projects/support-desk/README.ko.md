# Support desk

[system-design case 06](../../system-design/06-tool-agent-user-support/README.ko.md)의
worked example입니다. 비싼 실패가 틀린 *답*이 아니라 틀린 *행동*인
**tool-agent-user** support desk입니다.

엄밀히 말하면 순수 agent가 아닙니다. **계정 변경 가지에서만 제한된 agent
loop를 여는 workflow**입니다. routing, FAQ 경로, HITL, tool 사전조건, eval,
packaging은 미리 짜 둔 코드입니다. 모델이 다음 tool을 고르는 구간은
`agent/loop.py` 안뿐입니다.

agent-lab 과정을 마친 뒤 실무 감각을 위한 실행 가능한 미니 제품입니다.

## Pipeline

```text
                         packaging (CLI / HTTP)
                                   |
                                   v
                         +------------------+
                         | input guardrail  |   workflow
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | route()          |   workflow
                         | FAQ | account    |
                         +---+------+-------+
                             |      |
              workflow       |      |      agent segment
              +--------------v      v------------------+
              |  FAQ path           account path       |
              |  retrieve policy    while budget left: |
              |  one model call     model + tools      |
              |  no side-effect     |                  |
              |  tools              v                  |
              |               tools_gate               |
              |               auto | confirm | forbid  |
              |               tool preconditions       |
              |               SQLite account state     |
              +--------------+------+------------------+
                             |      |
                             v      v
                         +------------------+
                         | evaluation       |   workflow
                         | audits + DB      |   (oracle = actions)
                         +------------------+
```

| 구간 | 종류 | 다음 단계를 정하는 것 |
| --- | --- | --- |
| Input guardrail | workflow | 코드 (`check_input`) |
| `route()` | workflow | 코드 (키워드 / order id) |
| FAQ path | workflow | 고정: retrieve 후 completion 1회 |
| Account path | **agent** | 루프 안에서 모델이 tool 선택 |
| `tools_gate` | workflow 울타리 | HITL 맵 + tool 사전조건 (모델이 못 overturn) |
| 예산 / `stop_reason` | workflow 울타리 | agent를 감싸는 코드 한도 |
| Evaluation | workflow | audit·DB에 대한 결정적 검사 |
| Packaging | workflow | 어댑터; `/health`는 모델을 호출하지 않음 |

system-design case 07 (`workflow-not-agent`)도 참고하세요. account 가지를
순수 상태머신으로 짤 수도 있습니다. 이 프로젝트가 루프를 둔 이유는 대화가
열려 있다는 case 06 가정 때문입니다.

## 여기서 만져 보는 것

- Policy markdown은 참고용으로 검색됩니다. 허가는 tool 사전조건과 HITL 맵에
  컴파일되어 있습니다. 둘은 다른 층입니다.
- 계정 상태는 SQLite에 있고 대화에 캐시하지 않으며 tool로 다시 읽습니다.
- FAQ 경로는 환불·취소 tool을 노출하지 않습니다. routing이 capability를
  고릅니다.
- Eval은 답변 문장이 아니라 올바른 tool이 성공했는지를 채점합니다.
- Smoke와 `/health`는 모델 호출 없이 프로세스 생존만 증명합니다.

## 설정

```bash
cd projects/support-desk
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ../../agent-lab   # common이 안 보이면
cp .env.example .env             # live ask용 ANTHROPIC_API_KEY
```

## 실행

```bash
python -c "from support_desk.evaluation.runner import run_suite_offline; \
import json; print(json.dumps(run_suite_offline(), indent=2))"

pytest -q
python -m support_desk smoke

python -m support_desk ask "How many days do I have to return an item?" --report
python -m support_desk ask "Refund ORD-100 in full." --approve --report

python -m support_desk.packaging.mcp_order_server
```

## 시드 세계

| Order | Status | Notes |
| --- | --- | --- |
| ORD-100 | delivered, 5일 전, $49.99 | 환불 가능 |
| ORD-200 | delivered, 45일 전, $120 | 기간 만료 |
| ORD-300 | shipped, $80 | 취소 불가 |
| ORD-400 | processing, $25 | 취소 가능 |

## 구조

폴더는 파이프라인 층을 따릅니다. 대부분은 workflow이고, `agent/`만 agent
segment입니다.

```text
src/support_desk/
  packaging/      # 어댑터: config, CLI, HTTP, smoke, MCP
  routing/        # workflow: FAQ vs account
  tools_gate/     # workflow 울타리: tools, HITL, DB, policy RAG, guardrails
  agent/          # agent segment: loop.py (budgets, stop_reason)
  evaluation/     # workflow: 행동 단위 suite + reports
  paths.py
tests/
  packaging/  routing/  tools_gate/  evaluation/
data/
  policy/     # 작성된 policy corpus (참고, 허가가 아님)
  seed.sql
  eval/       # 행동·DB 상태로 채점하는 케이스
```

## 관련

- System design: `06-tool-agent-user-support`, `07-workflow-not-agent`
- Labs: 03, 07, 08, 10, 12, 14, 15, 16, 17, 18
- Cloud 대응표: `agent-lab/docs/from-lab-to-cloud.ko.md`
