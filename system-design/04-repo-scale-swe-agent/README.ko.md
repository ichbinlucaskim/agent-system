# 04 - Repo-scale SWE agent

## Representative system

SWE-agent, SWE-bench에서 평가됨.

> 근거 밀도에 대한 알림. 이 case는 논문 두 편에 기대고 있으며, 우리가 여기서 확보한
> 것은 해법에 대한 기술이 아니라 문제에 대한 그들의 규정입니다. 이는 archetype을
> 특징짓기에는 충분하지만 시스템 내부를 기술하기에는 충분하지 않습니다. 그래서
> dimension 5부터 8까지가 얇으며, 그 공백은 그럴듯한 세부로 메우지 않고
> `open-questions.md`에 기록해 두었습니다.

## 이 archetype이 존재하는 이유

이 라이브러리에서 성공을 기계가 검사할 수 있는 유일한 case입니다.

[T3] 우리의 해석은 이렇습니다. test suite는 oracle이며, 그 사실 하나가 여기의 다른
모든 case를 지배하는 evaluation 문제를 제거합니다. case 03은 연구 보고서가 좋은지를
자동으로 판정할 수 있는 것이 없기 때문에 LLM judge와 사람 검토자가 필요합니다. case
01은 diff를 개발자에게 넘깁니다. case 06에는 사람이 해석해야 하는 policy가 있습니다.
여기서는 "동작했는가"라는 질문에 기계가 반복해서, 낮은 비용으로 내놓을 수 있는 답이
있습니다.

거기서 따라 나오는 것이 설계의 대부분입니다. oracle은 retry 루프를 합리적으로 만들고,
evaluation을 연구 과제가 아니라 빌드 단계로 만들며, 저장소를 상대로 agent를 사람 없이
돌리는 것을 납득할 만하게 만듭니다. 끝에 있는 검사를 믿을 수 있기 때문입니다. 이 case는
그 변수를 분리해 내기 위해 존재합니다. action space 면에서 case 01과 충분히 가까워 비교가
깔끔하고, 그럼에도 거의 전적으로 oracle 때문에 갈라집니다.

## 열두 개의 dimension

### 1. Problem and success criteria

[T1] SWE-bench는 인기 있는 Python 저장소 12곳의 실제 GitHub issue와 그에 대응하는 pull
request에서 뽑아낸 소프트웨어 엔지니어링 문제 2,294개로 이루어진 evaluation
framework입니다. [T1] codebase와 issue 설명이 주어지면 모델이 issue를 해결하도록
codebase를 수정합니다.

[T3] 우리의 해석은 성공이 기계가 검사할 수 있는 것이며, 그것이 이 case 전체의
전제라는 것입니다. 여기서 근거의 한계를 분명히 해 둘 필요가 있습니다. 우리의 자료는
문제들이 issue와 그에 대응하는 pull request에서 뽑혔다고 말할 뿐, 후보 수정이 issue를
해결했는지 판정하는 메커니즘은 말하지 않습니다. 짝지어진 pull request가 검사 가능한
기준을 제공한다는 추론은 우리의 것입니다. `open-questions.md`를 참고하세요.

### 2. Autonomy level

workflow가 아니라 agent입니다. [T1] 저자들이 이 시스템을 agent로 명명했고, 작업이
execution environment와의 상호작용을 요구하는데 이는 단일 pass가 아니라 루프를
함의합니다.

우리의 자료는 루프의 구조, 제한, 정지 조건을 기술하지 않으므로 우리도 기술하지
않습니다.

### 3. Observation space

[T1] agent는 codebase와 issue 설명을 관측합니다. [T1] 이 issue들을 해결하려면 자주
execution environment와 상호작용하고 긴 context를 처리해야 합니다.

[T3] 우리의 해석은 이것이 라이브러리에서 가장 풍부한 observation space이자 가장 비싼
것이라는 점입니다. 저장소는 어떤 context window보다 크므로 여기서 observation은
필연적으로 선택 행위이며, 그 선택의 품질은 retrieval의 세부가 아니라 설계 문제입니다.

### 4. Action space

[T1] 모델이 issue를 해결하도록 codebase를 수정합니다. [T1] issue 해결에는 자주 여러
함수, class, 파일에 걸친 변경을 조율하는 일이 필요합니다.

[T3] 우리의 해석은 이 action space가 명목상으로는 case 01과 같은 파일 변경이지만
실질적으로는 매우 다르다는 것입니다. 개발자의 working tree가 아니라 evaluation harness
안의 버려도 되는 checkout을 상대로 이루어지기 때문입니다. 수정은 인스턴스를 폐기하는
것으로 되돌릴 수 있습니다. 그것이 이 case가 permission architecture에 아무것도 쓰지
않고 case 01이 예산의 대부분을 거기에 쓰는 이유이며, 그 차이가 능력이 아니라 놓인
상황에서 온다는 점을 분명히 해 둘 가치가 있습니다.

### 5. Tools and agent-computer interface

[T1] 논문 제목에 담긴 주장은 agent-computer interface가 자동화된 소프트웨어 엔지니어링을
가능하게 한다는 것입니다.

그것이 논지이고, 우리의 자료에는 그 논지를 뒷받침하는 interface 설계가 담겨 있지
않습니다. interface가 무엇으로 이루어져 있는지 재구성하지 않겠습니다. 이 주장에서 옮겨
갈 수 있는 부분은 그 형태입니다. agent에게 주어지는 interface는 모델이 이미 갖고 있는
능력을 감싸는 포장이 아니라, 그 agent가 무엇을 해낼 수 있는지를 결정하는 일차 요인이라는
것입니다. 이 case에서 가장 큰 공백으로 `open-questions.md`에 기록해 두었습니다.

### 6. Context strategy

[T1] 긴 context를 처리하는 일이 이 작업의 요구 사항 중 하나로 언급됩니다.

우리의 자료는 이 시스템이 context를 어떻게 관리하는지 기술하지 않습니다. 저장소가 어떤
window보다 크다는 점을 생각하면 여기에 전략이 있을 텐데, 우리는 그것을 출처로 뒷받침할
수 없습니다.

### 7. Memory and state

우리의 자료에 기술되어 있지 않습니다.

### 8. Control flow

dimension 2에서 말한 것 이상으로는 우리의 자료에 기술되어 있지 않습니다.

### 9. Error handling and recovery

[T1] 이 issue들을 해결하려면 자주 execution environment와 상호작용해야 합니다.

[T3] 우리의 해석은 이것이 이 case가 라이브러리의 나머지와 가장 유용하게 갈라지는
dimension이라는 것입니다. 환경이 응답해 주기 때문입니다. 테스트 실행이나 stack trace는
agent 자신의 행동이 만들어 낸 observation이며, 이는 error handling과 evaluation이 범위만
다를 뿐 같은 장치라는 뜻입니다. case 02에는 이에 상응하는 것이 없고, case 03의 worker는
검색 결과에서 이런 종류의 신호를 받지 못합니다.

### 10. Human involvement and permissions

[T3] 우리의 해석은 benchmark 실행 중에는 구조적으로 루프 안에 사람이 없다는 것입니다.
2,294개 인스턴스에 대한 evaluation은 사람이 감독하는 것이 아니기 때문입니다. 우리의
자료는 benchmark 바깥에서 이 시스템이 어떻게 사용되는지 기술하지 않으며, 우리는 주장을
그쪽으로 확장하지 않습니다.

### 11. Evaluation

이 case를 규정하는 dimension이자 우리 자료가 실제로 뒷받침하는 dimension입니다.

[T1] SWE-bench는 인기 있는 Python 저장소 12곳의 실제 GitHub issue와 그에 대응하는 pull
request에서 뽑아낸 소프트웨어 엔지니어링 문제 2,294개로 이루어진 evaluation
framework입니다. [T1] 이들을 해결하려면 자주 여러 함수, class, 파일에 걸친 변경을
조율하고, execution environment와 상호작용하고, 긴 context를 처리하고, 전통적인 code
generation을 넘어서는 추론을 해야 합니다.

[T3] 우리의 해석은 그 구성 방식 자체가 기여라는 것입니다. 이 benchmark는 이미 수행되고
이미 검토된 작업으로부터 조립되었으며, 이는 작업 분포가 저술된 것이 아니라 실제라는 뜻이고
기준이 benchmark 설계자가 작성한 것이 아니라 각 인스턴스와 함께 딸려 온다는 뜻입니다.
그것은 반복 가능한 레시피이며, 이 case에서 가져갈 가치가 있는 것입니다.

### 12. Cost and latency budget

우리의 자료에는 이 시스템의 비용이나 지연에 대한 내용이 전혀 없습니다. 여기에 어떤
수치도 제시하지 않습니다.

## Failure modes

아래는 모두 [T3]이며, 보고된 결과가 아니라 이 작업이 무엇을 요구하는지에 대한 T1의
규정으로부터 추론한 것입니다. 우리의 자료는 failure 분석을 보고하지 않습니다.

- **위치 파악 실패.** [T1]은 issue 해결에 자주 여러 함수, class, 파일에 걸친 변경을
  조율하는 일이 필요하다고 말합니다. [T3] 우리의 해석은 agent가 국소적으로는 올바른
  수정을 엉뚱한 자리에 만들어 낼 수 있으며, 이 실패는 모델이 자기 출력에 대해 돌릴 수
  있는 모든 검사는 통과하면서 oracle에서는 실패한다는 것입니다.
- **수정에 도달하기 전의 context 고갈.** [T1]은 긴 context 처리를 이 작업의 요구로
  꼽습니다. [T3] 우리의 해석은 observation이 작업 자체와 경쟁한다는 것입니다. 저장소를
  읽는 데 쓴 예산은 수정과 테스트 주기에 쓸 수 없는 예산입니다.
- **oracle에 대한 과적합.** [T3] 검사 가능한 기준을 갖는 데 따라오는 위험에 대한 우리의
  해석입니다. 테스트를 돌릴 수 있는 agent는 테스트를 만족시키는 코드를 쓸 수 있고, 그것은
  issue를 해결하는 코드와 같지 않습니다. 이 case를 다룰 만하게 만들어 주는 그 oracle이
  동시에 그것을 상대로 게임을 걸 수 있는 대상이며, 다른 어떤 case도 oracle이 없으므로 이
  노출을 갖지 않습니다.

## 훔쳐 올 것 하나

agent가 아니라 benchmark 구성 방식입니다.

[T1] SWE-bench는 실제 GitHub issue와 그에 대응하는 pull request로 만들어졌습니다. [T3]
우리의 해석은 이것이 데이터셋이 아니라 레시피라는 것입니다. bug tracker와 버전 관리
이력을 가진 팀이라면 이미 evaluation set의 원재료를 갖고 있습니다. 작업이 실제이고,
분포가 benchmark 설계자의 것이 아니라 그들의 것이며, 각 작업의 합격 기준을 그것을 고친
사람이 이미 작성해 둔 set입니다. agent를 만드는 대부분의 팀은 eval 사례를 손으로 쓰고,
더 많은 수고를 들여 더 작고 더 인위적인 set을 얻습니다.

## 따라 하지 말 것 하나

여러분의 도메인에도 oracle이 있으리라는 가정입니다.

[T3] 우리의 해석은 이것이 이 case를 잘못 적용하는 가장 흔한 방식이라는 것입니다. 여기의
거의 모든 설계 결정이 자동 검증의 하류에 있으므로 architecture가 깔끔하고 확신에 찬
것처럼 읽히지만, 연구 글쓰기나 고객 지원이나 analytics로 옮겨 갈 때는 그것을 작동하게 만든
바로 그 속성을 포기해야만 옮겨집니다. oracle이 없을 때 올바른 수는 case 03이 사람 평가로,
case 06이 사용자를 루프 안에 두는 것으로 하듯 검토를 전제로 설계하는 것이지, 이 형태를
채택하고 judge 모델이 대신해 주기를 바라는 것이 아닙니다.

## 관련 자료

**Lab exercises:** `15-evaluation`, `07-tool-design-aci`, `12-agent-loop`,
`06-evaluator-optimizer`.

**Paper topics:** `06-environment-and-interface`, `07-evaluation`,
`02-acting-and-tools`.

**다른 case:** `01-terminal-coding-agent`와의 대조가 이 case의 요점입니다.
`03-orchestrator-worker-research`는 oracle이 없을 때 evaluation이 얼마나 드는지를
보여 줍니다.
