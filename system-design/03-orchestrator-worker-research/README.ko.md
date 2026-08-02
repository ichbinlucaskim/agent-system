# 03 - Orchestrator-worker research system

## Representative system

Anthropic Research. engineering post "How we built our multi-agent research
system"에 기술된 내용을 따릅니다.

## 이 archetype이 존재하는 이유

작업이 하나의 context window에 들어가지 않고, 들어가게 만들 수도 없는 case입니다.
case 01은 permission과 전문화를 위해 위임하고, case 04는 단일 agent가 돌아다닐 수
있는 저장소 안에서 일합니다. 여기서는 입력이 열린 web이고, 읽을 수 있는 자료의 양에
상한이 없으며, 출력은 내부적으로 일관되어야 하는 하나의 문서입니다.

이 case가 다루고 다른 어떤 case도 다루지 않는 지점은 **context 전략으로서의
위임**입니다. 다른 모든 case는 subagent를 쓰더라도 그것을 병렬화의 수단이나 능력을
제한하는 수단으로 다룹니다. 이 case는 새 context window 자체가 목적일 때 무슨 일이
일어나는지, 그리고 조정하는 agent가 결국 worker들이 읽은 것의 요약만 들고 있게 될 때
그 아래에서 무엇이 무너지는지를 보여 줍니다.

## 열두 개의 dimension

### 1. Problem and success criteria

주장이 출처에 귀속되는 보고서를 만들어 내는 열린 연구 작업입니다.

[T1] 이 post는 multi-agent system을 여러 agent, 즉 루프 안에서 자율적으로 tool을
사용하는 LLM들이 함께 일하는 것으로 정의합니다. [T1] 이 접근은 병렬적인 갈래로
나뉘는 문제에 적합하며 coding처럼 서로 강하게 얽힌 작업에는 덜 효과적이라고
명시합니다.

기계가 검사할 수 있는 oracle이 없습니다. [T1] 평가는 LLM judging과 사람의 검토를
결합했으며, 이것이 oracle 없는 문제가 강제하는 형태입니다. test suite가 판정하는 case
04와 이 라이브러리에서 가장 날카롭게 대비되는 지점입니다.

### 2. Autonomy level

모델이 주도하는 쪽 끝의 agent입니다. [T1] lead agent가 조정하면서 전문화된 작업을
병렬로 동작하는 subagent들에게 위임하는 orchestrator-worker 패턴입니다. [T1] lead
agent가 추가 연구가 필요한지 판단하고 다음 wave를 띄우거나 전략을 다듬을 수 있으므로,
step 수도 worker 수도 미리 정해져 있지 않습니다.

### 3. Observation space

[T1] subagent들은 각자 자신의 context window를 가지고 독립적으로 검색하며 정제된
findings를 반환합니다.

[T3] 우리의 해석은 lead agent와 worker들의 observation space가 서로 다르며 이것이
우연이 아니라 의도라는 것입니다. worker는 원본 출처를 봅니다. lead는 worker의 요약을
봅니다. lead가 초안을 쓸 시점에 그것은 보고서가 딛고 선 자료의 대부분을 한 번도 본 적이
없습니다.

### 4. Action space

외부에 대해서는 read-only입니다. [T1] 문서화된 행동은 검색, findings 반환, 추가 작업
생성, 그리고 보고서 산출입니다. [T1] lead는 자신의 plan을 Memory에 씁니다.

[T3] 우리의 해석은 되돌릴 수 없는 외부 부작용이 없다는 점이 이 case가 permission에
설계 예산을 거의 쓰지 않는 이유이며, case 01이 예산의 대부분을 거기에 쓰는 이유라는
것입니다. 두 시스템 모두 모델이 control flow를 주도하는 agent이고, 다른 어떤
dimension보다 이 dimension에서 갈라집니다.

### 5. Tools and agent-computer interface

[T1] subagent가 주된 위임 장치이며, 별도의 CitationAgent가 출처 문서와 연구 보고서를
처리해 citation이 들어갈 자리를 식별함으로써 주장이 귀속되도록 합니다.

[T3] 우리의 해석은 CitationAgent가 이 architecture에서 가장 흥미로운 대상이며 그것이
dimension 3의 결과로 존재한다는 것입니다. lead agent는 초안을 쓸 시점에 요약의 요약을
가지고 작업하고 있으며, 자신이 여전히 들고 있는 그 무엇과도 귀속을 대조할 수 없습니다.
따라서 귀속은 원본 문서로 되돌아가는 별도의 pass가 재구성해야 합니다. citation 문제는
context 전략이 만들어 내고, 그다음 또 다른 agent가 해결합니다.

### 6. Context strategy

이 case가 존재하는 이유인 dimension입니다.

[T1] subagent들은 각자 자신의 context window를 가지고 독립적으로 검색하며 정제된
findings를 반환합니다. [T1] LeadResearcher는 접근 방식을 숙고한 뒤 context를
지속시키기 위해 자신의 plan을 Memory에 저장합니다. context window가 200,000 token을
넘으면 잘려 나가기 때문에 plan이 살아남아야 하기 때문입니다.

[T3] 우리의 해석이자 이 case의 분석적 요점은 이것입니다. 여기서 subagent는 병렬화
장치이기 이전에 context 관리 장치입니다. 병렬성은 이득이지만, 같은 subagent들을 하나씩
차례로 돌리는 시스템이라도 여전히 그것들이 필요합니다. 대안은 모든 worker가 읽은 것을
전부 하나의 window가 담는 것이기 때문입니다. 저장된 plan은 같은 발상을 lead 자신에게
적용한 것이며, 자기 context를 신뢰할 수 없는 저장소로 다루는 것입니다.

### 7. Memory and state

[T1] Memory는 truncation 경계를 넘어 lead agent의 plan을 보존합니다. [T1]
checkpointing이 production 관심사 중 하나로 언급됩니다.

[T3] 우리의 해석은 이들이 서로 다른 두 지속성 문제를 각각 해결한다는 것입니다.
Memory는 실행 안에서 특정 산출물을 context truncation으로부터 보호하고, checkpointing은
실행 자체를 프로세스 실패로부터 보호합니다. 이 둘을 뭉뚱그린 설계는 대개 장애 상황에서
그 차이를 발견하게 됩니다.

### 8. Control flow

모델이 주도하며 wave 단위로 진행됩니다. [T1] lead agent가 추가 연구가 필요한지
판단하고 다음 wave를 띄우거나 전략을 다듬을 수 있습니다.

[T1] 초기 agent들은 단순한 질의에 subagent를 50개 띄웠으며, 이런 종류의 동작을 고치는
주된 수단은 prompt engineering이었습니다.

[T3] 우리의 해석은 이것이 익숙한 절충의 정직한 버전이라는 것입니다. 모델 주도 fan-out은
시스템이 질문에 맞춰 스스로 노력의 크기를 정할 수 있게 해 주는 바로 그 요소이며, 동시에
그 크기를 두 자릿수만큼 틀리게 정할 수 있게 하는 요소이기도 합니다. 보고된 해법은 하드
캡이 아니라 prompting이었는데, 이는 case 01이 `maxTurns`로 내리는 선택과는 다른
선택입니다.

### 9. Error handling and recovery

[T1] post가 언급한 production 관심사에는 checkpointing, retry logic, rainbow
deployment가 포함됩니다.

[T3] 우리의 해석은 이 목록이 request-response 시스템이 아니라 오래 도는 stateful
시스템을 기술한다는 것입니다. 특히 rainbow deployment는 배포보다 오래 사는 실행에 대한
대응이며, 이는 case 02에는 없고 case 01에는 다른 형태로 있는 문제입니다.

### 10. Human involvement and permissions

실행 루프 안에 사람이 있다는 기록은 없습니다. [T1] 사람의 검토는 평가 단계에
등장하며, 검토자들은 SEO에 최적화된 출처에 과도하게 의존하는 문제 등을 잡아냈습니다.

[T3] 우리의 해석은 read-only action space가 사람 없는 루프를 받아들일 만하게 만든다는
것입니다. 시스템이 하는 어떤 일도 되돌리기 어렵지 않으므로 사람이 승인해야 할 행동이
없습니다. 설계상 루프 안에 사용자가 있는 case 06, 그리고 행동이 실제로 무는 탓에 루프를
gating해야 하는 case 01과 비교해 보세요.

### 11. Evaluation

[T1] 평가는 LLM judging과 사람의 검토를 결합했습니다. [T1] 사람 검토자들은 SEO에
최적화된 출처에 과도하게 의존하는 문제 등을 잡아냈습니다. [T1] lead agent로 Claude
Opus 4를, subagent로 Claude Sonnet 4를 사용한 multi-agent system은 내부 research
eval에서 단일 agent Claude Opus 4보다 90.2% 더 나은 성과를 냈습니다.

[T3] SEO 관련 발견에 대한 우리의 해석은, 그것이 evaluation을 만드는 사람에게 이
post에서 가장 유용한 문장이라는 것입니다. 이는 LLM judge가 잡아내기 어려운 실패입니다.
judge가 시스템이 본 것과 같은 잘 정돈된 출처를 보기 때문이며, 그것은 출력이 아니라
입력을 들여다본 사람이 찾아냈습니다.

### 12. Cost and latency budget

[T1] multi-agent system은 chat 상호작용보다 대략 15배 많은 token을 사용합니다. [T1]
보고된 구성은 lead agent로 Claude Opus 4를, subagent로 Claude Sonnet 4를 사용했습니다.

[T3] 우리의 해석은 이 model 분리가 dimension 6에 대한 직접적인 비용 대응이라는
것입니다. worker는 자기 window 안에서 범위가 정해지고 잘 명세된 읽기를 수행하는데, 이는
더 작은 model에 가장 잘 맞는 부분이며, 그동안 lead는 전략을 들고 있습니다. 15배라는
수치가 그 분리를 세부 사항이 아니라 공들여 설계할 가치가 있는 일로 만듭니다.

## Failure modes

앞의 세 가지는 [T1]이며, 우리가 추론한 것이 아니라 초기 버전의 동작으로 post에 보고된
것입니다.

- **아무 근거 없이 정해지는 fan-out 크기.** [T1] 초기 agent들은 단순한 질의에
  subagent를 50개 띄웠습니다.
- **존재하지 않는 출처를 찾아 헤매기.** [T1] 초기 agent들은 존재하지 않는 출처를 찾아
  web을 끝없이 뒤졌습니다.
- **worker들이 서로를 방해하기.** [T1] 초기 agent들은 과도한 업데이트로 서로를
  산만하게 만들었습니다.
- **얽힌 작업에서의 적합성 실패.** [T1] 이 접근은 coding처럼 서로 강하게 얽힌 작업에는
  덜 효과적입니다. [T3] 우리의 해석은 이것이 dimension 6과 같은 속성을 반대편에서 본
  것이라는 점입니다. 독립적인 context window는 하위 작업이 독립적일 때 정확히 이점이
  되고, worker들이 서로가 무엇을 찾았는지 알아야 할 때 부담이 됩니다.
- **귀속의 표류.** [T3] 보고된 사건이 아니라 CitationAgent의 존재로부터 나온 우리의
  해석입니다. 정제된 findings로 작업하는 초안 agent는 추적할 수 없는 주장을 만들어 낼 수
  있으며, 확신에 찬 문장과 귀속 가능한 문장이 똑같아 보이기 때문에 그 실패는 초안에서
  드러나지 않습니다.

[T1] post는 앞의 세 가지를 고치는 주된 수단이 prompt engineering이었다고 보고합니다.

## 훔쳐 올 것 하나

CitationAgent의 형태입니다. 초안 작성 중이 아니라 그 이후에, 원본 출처로 되돌아가 귀속을
붙이는 별도의 pass입니다.

[T3] 이것이 일반화되는 이유에 대한 우리의 해석은 이렇습니다. 들어오는 길에 요약을 하는
시스템이라면 어디든, 더 이상 볼 수 없는 자료로 초안을 쓰는 agent가 생깁니다. 그 agent에게
citation까지 정확히 달라고 요구하는 것은 자신이 들고 있지 않은 것과 대조하라고 요구하는
일입니다. 귀속을 원본에 접근할 수 있는 자기만의 pass로 분리하는 것이 구조적인 해법이며,
multi-agent인지 여부와 무관하게 요약 단계가 있는 모든 pipeline에 적용됩니다.

## 따라 하지 말 것 하나

서로 강하게 얽힌 작업에 대한 fan-out 자체입니다. [T1] post는 이 접근이 병렬적인 갈래로
나뉘는 문제에 적합하며 coding처럼 얽힌 작업에는 덜 효과적이라고 명시하고, [T1] 그것이
chat 상호작용의 대략 15배에 달하는 token을 쓴다고 밝힙니다.

[T3] 우리의 해석은 이 두 사실을 별개의 단서가 아니라 하나의 조건으로 함께 읽어야 한다는
것입니다. token 배수는 독립적인 갈래들을 병렬로 훑는 것을 사 줍니다. 갈래들이 독립적이지
않을 때에도 그 배수는 그대로 청구되고, 그것이 사려던 것은 배달되지 않습니다. case 07이
이 라이브러리에 존재하는 이유가 그 점검에 자리를 마련해 주기 위해서입니다.

## 관련 자료

**Lab exercises:** `05-orchestrator-workers`, `13-subagents`,
`04-parallelization`, `11-context-memory`, `15-evaluation`.

**Paper topics:** `05-multi-agent`, `04-memory-and-retrieval`, `07-evaluation`.

**다른 case:** `07-workflow-not-agent`가 이 case에 대한 의도된 반론입니다.
`01-terminal-coding-agent`는 다른 이유로 subagent를 사용합니다.
