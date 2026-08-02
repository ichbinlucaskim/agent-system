# 01 - Terminal coding agent

## Representative system

Claude Code.

## 이 archetype이 존재하는 이유

이 라이브러리에서 agent가 사용자의 컴퓨터 위에서, 사용자가 신경 쓰는 filesystem을,
결과를 검사할 oracle도 없고 일반적인 undo도 없는 상태로 변경하는 유일한 case입니다.
case 04도 코드를 수정하지만 그 수정이 옳았는지 말해 주는 test suite가 있는 sandbox
안에서 합니다. case 02는 아무것도 바꿀 수 없습니다. case 03은 문서를 만들어 냅니다.

이 case가 다루고 다른 어떤 case도 다루지 않는 지점은 **permission architecture**,
즉 어떤 행동이 묻지 않고 실행되고, 어떤 행동이 먼저 확인을 받고, 어떤 행동이 아예
거부되는지를 결정하는 장치입니다. 다른 모든 case에서 이 질문은 action space가
read-only여서 사소하거나, sandbox가 피해를 흡수해 주기 때문에 미뤄집니다. 여기서는
그것이 곧 설계입니다.

## 열두 개의 dimension

### 1. Problem and success criteria

작업은 독립적으로 완결되지 않고 프로젝트 안에 놓여 있습니다. [T1] 공식 안내는
`CLAUDE.md`를 모델이 항상 들고 있어야 하는 사실을 두는 자리로 기술하며 build
command, monorepo layout, 팀 컨벤션을 예로 듭니다. 이는 작업이 자기만의 컨벤션을
가진 기존 codebase 안에 위치함을 뜻합니다.

우리의 출처 자료는 완료 기준을 정의하지 않습니다. [T3] 우리의 해석은 일반적인
경우에 oracle이 없으며, 결과 diff를 검토하는 개발자가 판정자라는 것입니다. 설계의
나머지가 이 전제 위에 세워진 것으로 보이지만 우리는 이를 출처로 뒷받침할 수 없고,
이것이 `open-questions.md`의 첫 항목입니다.

### 2. Autonomy level

여기서 autonomy는 고정된 속성이 아니라 런타임 설정입니다. [T1] Plan mode는 tool
실행을 전면 차단하므로 모델은 분석하고 계획할 수는 있지만 변경을 만들 수 없습니다.
[T1] 반대편 끝에서 `bypassPermissions`는 permission prompt를 건너뜁니다. [T1]
subagent frontmatter의 `permissionMode` 필드가 이들 중 하나를 subagent별로
선택합니다.

[T3] 우리의 해석은 이것이 설정만으로 workflow와 agent 스펙트럼의 대부분을 가로지르는
하나의 시스템이라는 것입니다. 그래서 "이것은 얼마나 autonomous한가"는 제품에 던지면
틀린 질문이고 특정한 한 번의 실행에 던지면 옳은 질문이 됩니다.

### 3. Observation space

[T1] subagent의 `tools`와 `disallowedTools` frontmatter 필드가 어떤 tool을 갖는지
설정하고 `mcpServers`가 MCP server에 연결하므로, observation space는 subagent마다
설정으로 정의됩니다.

우리의 출처 자료는 기본 내장 tool 목록을 열거하지 않으므로, 기본 observation space가
무엇을 담고 있는지 우리는 말할 수 없습니다. [T3] root 및 home 디렉터리 삭제에 대한
문서화된 예외 조항이 존재한다는 것은 tool 집합이 그 예외가 필요할 만큼 filesystem에
폭넓게 닿는다는 뜻이지만, 이는 permission 규칙으로부터의 추론이지 tool에 대한 기술이
아닙니다.

### 4. Action space

action space는 filesystem 변경을 포함하며, 우리 자료에서 이를 가장 강하게 뒷받침하는
것은 tool 설명이 아니라 permission 규칙입니다. [T1] `bypassPermissions` 아래에서도
root 및 home 디렉터리 삭제는 여전히 확인을 요구합니다.

[T3] 우리의 해석은 이 예외 조항이 되돌릴 수 있음에 관한 진술이라는 것입니다. 설정된
mode가 아무리 관대하더라도, 되돌릴 수 없기 때문에 결코 자동 승인 대상이 될 수 없는
소수의 행동을 설계가 따로 구분해 둔 것입니다. 이는 어떤 행동에 대해 물어보는 것과는
다른 장치이며, 의도적으로 좁은 집합에만 적용됩니다.

[T1] 다른 세 범주도 `bypassPermissions`를 통과하지 못합니다. 명시적 ask 규칙, 조직이
ask로 설정한 connector tool, 그리고 `requiresUserInteraction`으로 표시된 MCP
tool입니다.

### 5. Tools and agent-computer interface

[T1] 문서화된 customization 표면은 일곱 가지 장치입니다. 항상 켜져 있는 프로젝트
context를 위한 `CLAUDE.md`, 강한 제약을 위한 rules, 재사용 가능한 절차를 위한
skills, 위임된 작업을 위한 subagents, 결정적 자동화를 위한 hooks, output styles,
그리고 나머지를 묶는 plugins입니다.

subagent interface가 자료가 가장 많은 부분입니다. [T1] subagent는 YAML frontmatter가
붙은 Markdown 파일이며 프로젝트 범위는 `.claude/agents/`에, 사용자 범위는
`~/.claude/agents/`에 저장됩니다. [T1] frontmatter 필드에는 `description`, `prompt`,
`tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`,
`maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`,
`isolation`이 포함됩니다. [T1] subagent의 이름, description, tool 목록은 session
시작 시 로드되지만 본문은 자동으로 호출되지 않습니다. Claude가 Agent tool을 통해
prompt 문자열을 전달하며 subagent를 호출합니다.

[T3] 우리의 해석은 이것이 subagent를 선택 표면과 실행 표면으로 나눈다는 것입니다.
이름과 description과 tool 목록은 모델이 놓고 고르는 대상이며 모든 session에서 context
비용을 치릅니다. 본문은 선택 이후에 실행되는 것이며 호출되기 전까지는 비용이 없습니다.
이 분할이 subagent의 description을 문서가 아니라 설계 산출물로 만드는 이유입니다.

### 6. Context strategy

[T1] 안내는 두 종류의 자료를 명시적으로 구분합니다. `CLAUDE.md`는 모델이 항상 들고
있어야 하는 사실을 위한 것이고, 절차는 대신 skills에 속합니다. [T1] subagent 본문은
session 시작 시 로드되지 않습니다.

[T3] 우리의 해석은 이들이 합쳐져 세 계층을 이룬다는 것입니다. 항상 상주하는 것
(`CLAUDE.md`), 이름과 description으로만 상주하고 사용할 때 로드되는 것(skills와
subagent 본문), 그리고 아예 별도의 context로 위임되는 것(subagent 실행)입니다.
절차를 `CLAUDE.md` 바깥에 두라는 안내는 무언가가 어느 계층에 속하는지에 관한
규칙이며, 이를 틀리면 그 비용은 실수한 순간이 아니라 모든 session의 모든 turn마다
지불됩니다.

### 7. Memory and state

[T1] subagent frontmatter에 `memory` 필드가 존재합니다. 우리의 출처 자료는 그
semantics, 범위, 수명을 기술하지 않으므로 우리도 기술하지 않습니다.
`open-questions.md`를 참고하세요.

### 8. Control flow

control은 모델이 주도하며, 그 일부를 코드로 되돌리는 문서화된 장치가 둘 있습니다.
[T1] Claude가 subagent를 호출하기로 결정하고 Agent tool을 통해 prompt 문자열을
전달하며 호출합니다. [T1] `maxTurns` 필드가 subagent를 제한합니다. [T1] 결정적
자동화를 위한 hooks가 존재합니다.

[T3] 우리의 해석은 hooks가 설계자가 모델로부터 control flow를 되찾아 오는 이음매이며,
어떤 동작에 대해서든 흥미로운 질문은 그것이 그 이음매의 어느 쪽에 있어야 하는가라는
것입니다.

### 9. Error handling and recovery

우리의 출처 자료는 tool call이 실패했을 때 무슨 일이 일어나는지, 에러가 루프 안으로
되돌아오는지, crash 이후 session을 재개할 수 있는지에 대해 아무 말도 하지 않습니다.
문서처럼 읽힐 답을 추론으로 만들어 내지 않겠습니다. `open-questions.md`를 참고하세요.

### 10. Human involvement and permissions

이 case가 존재하는 이유인 dimension이며 자료가 가장 탄탄한 부분입니다.

[T1] permission 검사는 순서대로 실행됩니다. deny 규칙이 먼저 검사되며
`bypassPermissions` mode에서도 tool을 차단합니다. [T1] hooks는 mode 검사보다 먼저
평가되며 여전히 tool을 차단할 수 있습니다. [T1] 활성 permission mode는 그 뒤에
적용됩니다.

[T1] `bypassPermissions`는 permission prompt를 건너뛰되 dimension 4에 나열한 네 가지
예외가 있습니다. [T1] 부모 session이 `bypassPermissions`나 `acceptEdits`를 사용하면
그것이 우선하며 subagent는 이를 덮어쓸 수 없습니다.

[T3] 우리의 해석이자 이 case의 분석적 요점은 이것입니다. 같은 동작을 prompt로 요청할
수도 있고 hook으로 강제할 수도 있는데, 모델이 다르게 결정할 때 살아남는 것은 둘 중
하나뿐입니다. filesystem을 변경하는 agent를 사람 없이 돌릴 수 있게 만드는 것은
prompt의 문구가 아니라 permission architecture입니다. 위의 순서가 그 주장의 구체적인
형태입니다. 모델 바깥에 있는 두 장치, 즉 deny 규칙과 hooks를, 설정이 선택한 mode보다
앞에 놓기 때문입니다.

[T3] 우선순위 규칙에 대한 두 번째 해석입니다. 관대한 부모를 자식이 조일 수 없으므로,
permission은 위임된 작업마다 협상되는 속성이 아니라 session 최상단에서 정해지는
천장입니다. subagent의 `permissionMode`는 부모가 이미 허용한 범위 안에서만 제한할 수
있습니다.

### 11. Evaluation

우리의 출처 자료에는 이 시스템이 어떻게 평가되는지에 관한 내용이 전혀 없습니다.
`open-questions.md`를 참고하세요.

### 12. Cost and latency budget

[T1] frontmatter는 `model`, `effort`, `background`, `isolation`을 subagent별 필드로
노출하며, 이는 cost와 latency 제어 표면의 형태입니다.

우리의 출처 자료에는 어떤 종류의 수치도 없습니다. token 수도, latency도, 가격도
없습니다. 우리도 제공하지 않겠습니다. 말할 수 있는 것은 구조적인 사실입니다. [T3]
subagent별 model 및 effort 선택이 존재한다는 것은 비용이 session 단위가 아니라 위임된
작업 단위로 조정되도록 의도되었음을 시사합니다.

## Failure modes

아래는 모두 [T3]이며, 관찰되거나 보고된 것이 아니라 위의 T1 사실들로부터 추론한
것입니다. 어느 것도 사건 보고가 아닙니다.

- **관대한 부모가 모든 자식을 조용히 넓힙니다.** [T1]은 부모의 `bypassPermissions`나
  `acceptEdits`가 우선하며 subagent가 덮어쓸 수 없음을 확립합니다. 따라서 신중하게
  제한적인 `permissionMode`로 작성된 subagent라도 관대하게 시작된 session에서 호출되면
  아무런 보호를 제공하지 않습니다. subagent 파일만 따로 읽으면 안전해 보인다는 점이
  이것을 짚어 둘 가치가 있게 만듭니다.
- **잘못된 자리에 쓴 제약은 더 이상 유지되지 않습니다.** prompt 문구로 표현된 동작은
  권고입니다. 같은 동작을 deny 규칙이나 hook으로 표현하면 dimension 10의 순서에 따라
  강제됩니다. 통과하는 transcript에서는 둘이 똑같아 보이며, 정확히 중요한 순간에
  갈라집니다.
- **선택 표면이 굶습니다.** [T1]은 session 시작 시 subagent의 이름과 description과
  tool 목록만 로드되고 본문은 자동 호출되지 않음을 확립합니다. 따라서 언제 호출해야
  하는지를 말하지 않는 description을 가진 subagent는 완벽하게 작성되고도 한 번도
  실행되지 않을 수 있으며, 그 실패는 조용합니다.
- **항상 켜진 context가 제동 장치 없이 자랍니다.** [T1] 안내는 절차를 `CLAUDE.md`가
  아니라 skills에 두라고 합니다. 그럼에도 절차가 `CLAUDE.md`에 쌓이는 것을 막는 장치는
  없으며, 그 비용은 실수한 순간이 아니라 모든 session의 모든 turn마다 지불됩니다.

## 훔쳐 올 것 하나

검사 순서입니다. [T1] deny 규칙이 가장 먼저 평가되며 가장 관대한 mode에서도
유지되고, hooks는 mode 검사보다 먼저 평가됩니다. 옮겨 갈 수 있는 아이디어는 특정
mode들이 아니라, 강제 계층이 모델 바깥에 그리고 설정보다 앞에 놓여서 모델의 결정도
관대한 설정도 그것을 지나칠 수 없게 한다는 원리입니다. 변경을 가하는 action space를
가진 agent라면 어떤 형태로든 이것이 필요하며, 나중에 만드는 것은 처음부터 만드는 것보다
훨씬 어렵습니다.

## 따라 하지 말 것 하나

운영 기본값으로서의 `bypassPermissions`입니다. 그것은 존재하고 [T1] 신중하게 고른
예외 조항을 갖고 있지만 [T1], 그럼에도 나머지 전부에 대해 "물어봐야 하는가"에
"아니오"라고 답하는 mode입니다. [T3] 우리의 해석은, 컨테이너나 제한된 tool 목록처럼
다른 수단으로 action space가 이미 좁혀져 있을 때에는 옹호할 수 있으며, 그 좁힘을 함께
가져오지 않고 mode만 복사하는 것은 편의만 취하고 안전은 두고 오는 일이라는 것입니다.

함께 저항할 만한 것은 일곱 가지 customization 표면이 존재한다는 이유로 전부 채택하는
일입니다. [T3] 각각은 나중에 읽는 사람이 agent가 왜 그렇게 했는지 이해하기 위해
들여다봐야 하는 자리이며, 두 개가 필요한 프로젝트는 두 개만 쓰는 편이 낫습니다.

## 관련 자료

**Lab exercises:** `07-tool-design-aci`, `13-subagents`, `14-human-in-the-loop`,
`12-agent-loop`, `11-context-memory`, `01-augmented-llm`.

**Paper topics:** `02-acting-and-tools`, `06-environment-and-interface`.

**다른 case:** test oracle 아래에서 코드를 변경하는 `04-repo-scale-swe-agent`, 그리고
아무것도 변경할 수 없는 `02-answer-engine`과 대조해 보세요.
