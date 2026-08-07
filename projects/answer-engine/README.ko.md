# Answer engine

[system-design case 02](../../system-design/02-answer-engine/README.ko.md)의
worked example입니다. 비싼 실패가 잘못된 부작용이 아니라 **증거를 앞지르는
유창한 답**인 **read-only answer pipeline**입니다.

엄밀히 말하면 **순수 workflow**이지 agent가 아닙니다. 모든 단계가 미리 짜인
코드입니다. 모델은 citation이 이미 prompt에 들어간 뒤에만 최종 답을 씁니다.
계정 변경 가지에서 agent loop를 여는 `projects/support-desk`(case 06)와
비교하세요.

## Pipeline

```text
                         packaging (CLI / HTTP)
                                   |
                                   v
                              question
                                   |
                                   v
                         +------------------+
                         | intent parse     |   workflow
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | hybrid retrieval |   workflow
                         | keyword + dense  |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | staged rerank    |   workflow
                         | careful score    |
                         | quality bar      |
                         | fail-safe restart|
                         +--------+---------+
                                  |
                     enough evidence? ------no----> abstain
                                  |
                                 yes
                                  v
                         +------------------+
                         | prompt assembly  |   workflow
                         | citations BEFORE |
                         | generation       |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | constrained      |   model writes here only
                         | synthesis        |
                         +--------+---------+
                                  |
                                  v
                         +------------------+
                         | evaluation       |   workflow
                         | docs + citations |
                         +------------------+
```

| 구간 | 종류 | 역할 |
| --- | --- | --- |
| Intent | workflow | retrieval 편향; 오류는 전파됨 (이후 verify loop 없음) |
| Hybrid retrieval | workflow | keyword + dense shortlist (lab 08/09) |
| Staged rerank | workflow | 소수 후보에 careful score; threshold + 1회 restart |
| Cite-before-gen | workflow | 귀속은 생성 제약이지 사후 부착이 아님 |
| Synthesis | model step | 조립된 passage만으로 답함 |
| Evaluation | workflow | 관련 doc? citation? 증거 없으면 abstain? |
| Packaging | workflow | `/health`는 모델을 호출하지 않음 |

HITL 없음. action space가 read-only라 승인할 것이 없습니다.

## 여기서 만져 보는 것

- 정확성은 사후 verification agent가 아니라 **grounding**으로 강제됩니다.
- staging이 latency 예산을 불균등하게 씁니다. 다수에는 싸게, 소수에는 조심스럽게.
- corpus 밖 질문은 지어내지 않고 abstain해야 합니다.
- offline 모드는 cited snippet을 이어 붙여 API key 없이 suite를 돌립니다.

## 설정

```bash
cd projects/answer-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ../../agent-lab
cp .env.example .env   # live ask에만 필요
```

## 실행

```bash
python -c "from answer_engine.evaluation.runner import run_suite_offline; \
import json; print(json.dumps(run_suite_offline(), indent=2))"

pytest -q
python -m answer_engine smoke

python -m answer_engine ask "What is the difference between a workflow and an agent?" --offline
python -m answer_engine ask "When should citations be embedded?" --offline --json
```

## 구조

```text
src/answer_engine/
  intent/        # parse + retrieval query bias
  retrieval/     # corpus, hybrid keyword+dense
  ranking/       # staged rerank, threshold, restart
  synthesis/     # cite-before-gen assembly + answer
  pipeline.py    # 고정 workflow 연결
  evaluation/    # grounding/citation suite
  packaging/     # config, CLI, HTTP, smoke
data/corpus/     # 작은 로컬 지식 베이스
data/eval/       # 라벨된 질문
```

## 관련

- System design: `02-answer-engine`
- 대조: `projects/support-desk` (case 06 workflow+agent)
- Labs: 02, 03, 08, 09, 18
- Cloud 대응표: `agent-lab/docs/from-lab-to-cloud.ko.md`
