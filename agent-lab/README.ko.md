# Agent systems lab

agent system이 실제로 어떻게 만들어지는지 배우는 실습 중심 lab 과정입니다. lab
열아홉 개, track 네 개, capstone 하나로 구성됩니다. 짧은 README를 읽고
`starter/main.py`의 TODO를 채운 뒤 pytest로 결과를 확인합니다.

모든 것이 로컬에서 실행됩니다. 필요한 계정은 Anthropic API key 하나뿐이고,
runtime 의존성은 정확히 세 패키지입니다. `anthropic`, `pytest`, `numpy`입니다.
여기에 agent framework가 없는 것은 의도된 선택입니다. 남의 framework를 설정하는
것이 아니라 메커니즘 자체를 만들어 보는 것이 목적이기 때문입니다.

## 대상 독자

Python을 쓸 줄 알고 LLM API를 최소 한 번은 사용해 본 엔지니어, 그리고 agent
framework 밑에 깔린 패턴을 충분히 이해해서 그중 무엇을 고를지, 어떻게 디버깅할지,
언제 아예 쓰지 않을지 판단하고 싶은 엔지니어를 위한 과정입니다. 두 가지 인증
시험의 목표와도 대응되며, 자세한 내용은 `docs/cert-mapping.md`에 있습니다.

lab을 마친 뒤 AWS나 흔한 library가 어디에 붙는지 궁금하면
`docs/from-lab-to-cloud.ko.md`를 보세요. 짧은 버전: lab은 무엇이 지켜져야
하는지를 정하고, library는 구현을 빠르게 하며, cloud는 같은 core가 돌고
상태를 두고 관측되는 실행 환경입니다.

## 네 개의 track

- **Track 1, 패턴.** 조합 가능한 workflow 패턴들입니다. augmented LLM, prompt
  chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer.
- **Track 2, tool과 context.** 모델에 무엇을 주고 무엇을 하게 할 것인가입니다.
  tool 및 interface 설계, retrieval, retrieval 품질, MCP 스타일 server, context
  engineering.
- **Track 3, 자율성.** 모델에 통제권을 넘기되 그것을 제한하는 방법입니다. agent
  loop, subagent, 사람의 승인 gate.
- **Track 4, 프로덕션.** 데모와 시스템을 가르는 것들입니다. evaluation,
  observability, guardrail, packaging.

## lab 목록

| Lab | 이름 | Track | 예상 소요 시간 | 핵심 또는 선택 |
| --- | --- | --- | --- | --- |
| 00 | [Setup](labs/00-setup/README.ko.md) | 설정 | 20분에서 30분 | 핵심 |
| 01 | [The augmented LLM](labs/track-1-patterns/01-augmented-llm/README.ko.md) | Track 1, 패턴 | 30분에서 45분 | 핵심 |
| 02 | [Prompt chaining](labs/track-1-patterns/02-prompt-chaining/README.ko.md) | Track 1, 패턴 | 30분에서 45분 | 핵심 |
| 03 | [Routing](labs/track-1-patterns/03-routing/README.ko.md) | Track 1, 패턴 | 30분에서 45분 | 핵심 |
| 04 | [Parallelization](labs/track-1-patterns/04-parallelization/README.ko.md) | Track 1, 패턴 | 45분에서 60분 | 핵심 |
| 05 | [Orchestrator and workers](labs/track-1-patterns/05-orchestrator-workers/README.ko.md) | Track 1, 패턴 | 45분에서 60분 | 핵심 |
| 06 | [Evaluator and optimizer](labs/track-1-patterns/06-evaluator-optimizer/README.ko.md) | Track 1, 패턴 | 45분에서 60분 | 핵심 |
| 07 | [Tool design and the agent-computer interface](labs/track-2-tools-context/07-tool-design-aci/README.ko.md) | Track 2, tool과 context | 45분에서 60분 | 핵심 |
| 08 | [RAG basics](labs/track-2-tools-context/08-rag-basics/README.ko.md) | Track 2, tool과 context | 60분에서 90분 | 핵심 |
| 09 | [Retrieval quality](labs/track-2-tools-context/09-retrieval-quality/README.ko.md) | Track 2, tool과 context | 60분에서 90분 | 선택 |
| 10 | [An MCP-style server](labs/track-2-tools-context/10-mcp-server/README.ko.md) | Track 2, tool과 context | 60분에서 90분 | 핵심 |
| 11 | [Context and memory](labs/track-2-tools-context/11-context-memory/README.ko.md) | Track 2, tool과 context | 45분에서 60분 | 핵심 |
| 12 | [The agent loop](labs/track-3-autonomy/12-agent-loop/README.ko.md) | Track 3, 자율성 | 60분에서 90분 | 핵심 |
| 13 | [Subagents](labs/track-3-autonomy/13-subagents/README.ko.md) | Track 3, 자율성 | 45분에서 60분 | 핵심 |
| 14 | [Human in the loop](labs/track-3-autonomy/14-human-in-the-loop/README.ko.md) | Track 3, 자율성 | 45분에서 60분 | 핵심 |
| 15 | [Evaluation](labs/track-4-production/15-evaluation/README.ko.md) | Track 4, 프로덕션 | 60분에서 90분 | 핵심 |
| 16 | [Observability](labs/track-4-production/16-observability/README.ko.md) | Track 4, 프로덕션 | 45분에서 60분 | 선택 |
| 17 | [Guardrails](labs/track-4-production/17-guardrails/README.ko.md) | Track 4, 프로덕션 | 45분에서 60분 | 핵심 |
| 18 | [Packaging and deployment](labs/track-4-production/18-packaging-deploy/README.ko.md) | Track 4, 프로덕션 | 45분에서 60분 | 선택 |

lab 09, 16, 18은 선택으로 표시되어 있습니다. 프로덕션에서 덜 중요하다는 뜻이
아니라, 핵심 메커니즘을 배우는 동안에는 미뤄 둘 수 있다는 뜻입니다.

## 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

그다음 `.env`에 key를 넣고 export합니다.

```bash
export $(grep -v '^#' .env | xargs)
```

`.env`는 git에서 제외됩니다. 실제 key를 절대 commit하지 마세요.

venv 생성과 설치를 한 번에 해 주는 Makefile target도 있습니다.

```bash
make setup
```

## 테스트 실행

```bash
pytest labs -v                      # 전체
pytest labs/00-setup/tests -v       # lab 하나
make test
make test-lab LAB=labs/00-setup
```

테스트는 API key가 없어도 suite 전체가 통과하도록 작성되어 있습니다. 실제 호출이
필요한 것은 실패하지 않고 깔끔하게 skip되므로, 비용을 쓰기 전에 lab의 오프라인
부분을 먼저 진행할 수 있습니다.

## 현재 구현 상태

열아홉 개의 lab이 모두 완성되어 있습니다. 각 lab에는 두 언어로 완전히 작성된
README, 시그니처와 TODO가 있는 `starter/main.py`, 참조 `solution/main.py`,
그리고 solution의 동작을 실제로 검증하는 assertion이 담긴 테스트 파일이
있습니다. 결정적인 부분은 모두 오프라인으로 테스트되며, 실제 모델 호출이 필요한
소수의 테스트는 API key가 없으면 깔끔하게 skip됩니다.

연습 과제는 여전히 여러분의 몫입니다. `starter/main.py`에서 시작해 테스트로
구현을 확인하세요. solution은 비교를 위한 참조 답안이지 출발점이 아닙니다.

## 저장소 구조

```
lab/
├── common/     공용 helper: client, tracing, cost, vectorstore
├── labs/       track별로 묶인 열아홉 개의 lab
├── capstone/   end-to-end 프로젝트 과제
└── docs/       glossary, 인증 시험 매핑, 읽을거리 목록,
                lab-to-cloud 대응표
```

`CLAUDE.md`에는 이 저장소의 규약이 담겨 있으며, `README.md`와 `README.ko.md`를
함께 수정해야 한다는 규칙도 포함되어 있습니다.
