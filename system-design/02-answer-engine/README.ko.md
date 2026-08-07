# 02 - Answer engine

## Representative system

Perplexity. 외부에서 재구성한 내용을 따릅니다.

> ## 경고: 이것은 기술이 아니라 재구성입니다
>
> **Perplexity는 first-party architecture 기술을 공개한 적이 없습니다.** 이 파일의
> 어떤 것도 T1이 아닙니다. 아래의 모든 것은 외부 재구성에서 왔으며, 주로
> search-optimization 업계가 만들어 낸 것입니다. 그들이 이 시스템을 분석하는 목적은
> 그것을 문서화하는 것이 아니라 그 안에서 상위에 노출되는 것입니다.
>
> **여기서 사용한 두 재구성은 구체적인 내용에서 서로 어긋납니다.** 전체적인 형태에는
> 동의하고 각 단계가 무엇을 담고 있는지에서는 갈라지는데, 이는 두 저자 모두 볼 수 없는
> 시스템에 대해 독립적으로 추론했을 때 정확히 예상되는 패턴입니다.
>
> **이 문서는 제품에 대한 주장이 아니라 archetype에 대한 연구입니다.** read-only action
> space와 빡빡한 latency budget이 주어졌을 때 answer engine이 어떤 모습이어야 하는지를
> 읽기 위한 것입니다. Perplexity가 무엇을 하는지에 대한 근거로 인용하지 마세요. 아래
> 여러 dimension은 재구성 불가로 표시되어 있으며, 나머지를 만들어 낸 것과 같은 업계
> 논평으로 채우는 대신 비워 두었습니다.

## 이 archetype이 존재하는 이유

이 case는 case 01의 거의 모든 절충을 뒤집습니다.

[T3] 우리의 해석은 이렇습니다. 이것은 read-only action space와 빡빡한 latency budget을
가진 agent 인접 시스템입니다. case 01은 필요한 만큼 시간을 쓸 수 있고 그 행동이 실제로
물기 때문에, 설계 예산이 permission으로 가고 정확성은 사람이 결과를 검토하는 데서
나옵니다. 여기서는 시스템이 하는 어떤 일도 위험하지 않고 어떤 일도 느릴 수 없으므로, 설계
문제 전체가 첫 시도에 올바른 증거를 모델 앞에 놓는 일로 옮겨 갑니다.

그 결과이자 이 case가 자리를 차지할 자격을 얻는 이유는 이것입니다. **정확성이
verification 루프가 아니라 grounding으로 강제됩니다. 루프를 돌릴 시간이 없기 때문입니다.**
case 03은 초안 작성 이후 별도의 agent로 귀속을 검증합니다. case 04는 테스트를 돌리고 다시
시도합니다. case 06은 행동 전에 유효성 검사를 감당할 수 있습니다. 이 case는 그중 무엇도 할
수 없으며, 정확성을 대신 구조적으로 해결해야 합니다.

## 열두 개의 dimension

두 재구성이 뒷받침하는 dimension만 채웠습니다. 여럿은 의도적으로 비어 있습니다.

### 1. Problem and success criteria

[T3] 자연어 질문에 대해, 검색된 출처에 주장을 귀속시킬 수 있는 합성된 응답을 대화형
latency 예산 안에서 내놓는 것입니다.

[T3] 성공은 case 06과 같은 두 갈래 구조를 가지며 그 갈래는 서로 다릅니다. 답이 유용해야
하고, 동시에 검색된 것으로 뒷받침되어야 합니다. 자기 증거를 앞질러 가는 유창한 답이 이
archetype의 특징적인 실패입니다.

### 2. Autonomy level

[T2] 두 재구성 모두 모델이 자기 프로세스를 지휘하는 것이 아니라 단계로 나뉜 pipeline을
기술합니다. ziptie.dev는 query intent parsing, retrieval, ranking, prompt assembly,
synthesis를 순차적 단계로 기술하고, stackmatix.com은 retrieval에 이어 두 개의 reranking
계층이 더 있다고 기술합니다.

[T3] 우리의 해석이며 분명히 말해 둘 가치가 있습니다. 이 재구성들이 대략이라도 맞다면 이
시스템은 autonomy 스펙트럼에서 case 01보다 case 07에 가깝습니다. 이것이 이 라이브러리에
agent 인접 case로 들어와 있는 이유는 어떻게 통제되는가가 아니라 무엇을 하는가 때문입니다.

### 3. Observation space

[T2] retrieval을 통해 닿는 web 규모의 corpus입니다. ziptie.dev는 BM25와 dense embedding을
결합한 real-time hybrid retrieval을 기술하고, stackmatix.com은 BM25와 embedding retrieval을
세 계층 중 첫 계층으로 기술합니다.

[T3] 우리의 해석은 observation space가 사실상 무한하며, 시스템의 진짜 제약은 무엇을 볼 수
있는가가 아니라 예산 안에서 그중 얼마나 들여다볼 수 있는가라는 것입니다. 그래서 선택이 전부가
됩니다.

### 4. Action space

[T3] read-only입니다. retrieval, ranking, generation은 응답을 만들어 낼 뿐 시스템 바깥의
어떤 것도 바꾸지 않습니다.

[T3] 이 속성 하나가 case 01을 지배하는 permission 장치가 여기에 없는 이유이며, dimension
4가 설계를 이끄는 모습을 이 라이브러리에서 가장 깔끔하게 보여 주는 사례입니다. 둘 다 LLM을
중심으로 만들어진 두 시스템이 안전 architecture를 거의 공유하지 않을 수 있는데, 한쪽은 읽기만
할 수 있기 때문입니다.

### 5. Tools and agent-computer interface

[T2] 기술된 구성 요소는 모델이 그중에서 고르는 tool이 아니라 retrieval과 reranking
단계입니다. ziptie.dev는 three-tier reranker를 갖춘 multi-layer ML ranking을 기술하고,
stackmatix.com은 BM25와 embedding retrieval, 그다음 cross-encoder reranking, 그다음 entity와
authority 신호를 쓰는 ML reranker로 이루어진 three-layer reranking 시스템을 기술합니다.

[T2] 두 설명은 각 계층이 무엇을 담고 있는지에서 어긋납니다. stackmatix.com은 자신의 weight가
근사치이며 query 유형에 따라 달라진다고 밝히는데, 이는 재구성의 한계를 이례적으로 명시적으로
인정한 것이며 액면 그대로 받아들일 가치가 있습니다.

[T3] 우리의 해석은 case 04가 말하는 의미의 agent-computer interface가 여기에는 없다는
것입니다. 모델이 행동을 고르고 있지 않기 때문입니다. interface 설계 작업은 ranking stack에
있습니다.

### 6. Context strategy

[T2] ziptie.dev는 generation 이전에 citation이 삽입된 prompt assembly와, 검색된 증거로
제한된 synthesis를 기술합니다.

[T3] 우리의 해석이자 이 case에서 가장 옮겨 갈 만한 관찰입니다. citation을 나중이 아니라
generation 이전에 붙이는 것은 직접적인 결과를 갖는 구조적 선택입니다. case 03은 초안 작성
이후 별도의 agent로 귀속을 붙이는데, 초안을 쓰는 agent가 더 이상 출처를 들고 있지 않게 된
뒤에는 그것이 유일한 선택지이기 때문입니다. 여기서는 generation 시점에 출처가 여전히
있으므로, 귀속이 나중의 재구성이 아니라 prompt의 속성이 될 수 있습니다. latency 예산이 이를
강제하며, 그 결과는 대안보다 오히려 더 강합니다.

### 7. Memory and state

우리의 자료로는 재구성할 수 없습니다. 두 출처 모두 대화 상태, 개인화, query 간 캐싱을
기술하지 않습니다. 유추로 채우는 대신 비워 둡니다. `open-questions.md`를 참고하세요.

### 8. Control flow

[T2] 대체로 고정되어 있습니다. ziptie.dev는 직선 pipeline에서 벗어나는 지점을 하나
기술합니다. 세 번째 reranking 계층의 quality threshold와, 그 문턱을 넘는 후보가 너무 적을 때
후보 집합을 버리고 retrieval을 다시 시작하는 fail-safe입니다.

[T2] stackmatix.com은 이 fail-safe를 기술하지 않습니다. 따라서 두 출처는 이 pipeline에 루프가
있기는 한가에 대해 긴장 관계에 있으며, 우리에게는 그것을 해소할 방법이 없습니다.

[T3] 우리의 해석은, 그 fail-safe가 기술된 대로 존재한다면 그것이 이 설계가 반복에 내주는 유일한
양보이며 그 형태가 시사적이라는 것입니다. 답을 다시 만들어 내는 것이 아니라 retrieval을 다시
시작합니다. verification 루프를 돌릴 시간이 없는 시스템이 검증 대신 하는 일이 그것입니다.

### 9. Error handling and recovery

[T2] 위의 fail-safe가 두 출처를 통틀어 기술된 유일한 복구 장치입니다. quality threshold를
넘는 후보가 너무 적으면 후보 집합을 버리고 retrieval을 다시 시작합니다.

[T3] 우리의 해석은 이것이 출력이 아니라 입력을 겨냥한 복구라는 것입니다. 약한 증거 집합을
잡아내야 할 실패로 다루며, 이는 자기 증거를 앞질러 가는 유창한 답이 중요한 실패라는 dimension
1에서 따라 나옵니다.

### 10. Human involvement and permissions

[T3] query 진행 중에는 없습니다. read-only action space에서 따라 나옵니다. 승인할 것이
없습니다.

### 11. Evaluation

우리의 자료로는 재구성할 수 없습니다. 두 출처 모두 이 시스템이 어떻게 평가되는지 기술하지
않으며, 이는 놀랄 일이 아닙니다. evaluation은 내부적인 일이고 외부 재구성은 관측된 출력에서
작업하기 때문입니다. 비워 둡니다. `open-questions.md`를 참고하세요.

### 12. Cost and latency budget

[T3] 빡빡한 대화형 예산이며, 제품이 질의응답 인터페이스라는 점과 [T2] retrieval이
real-time으로 기술된다는 점에서 추론했습니다.

[T3] 우리의 해석은 이것이 architecture 전체가 그것을 중심으로 조직된 제약이며, 단계로 나뉜
reranker가 존재하는 이유라는 것입니다. 계층별 ranking은 줄어드는 후보 집합에 점점 더 많은
연산을 쓰는 방법이며, 모든 것을 정성껏 평가하는 것을 금지하는 예산에 대한 표준적인 답입니다.
두 출처 모두 수치를 제시하지 않으며 우리도 제시하지 않습니다.

## Failure modes

- **자기 증거를 앞질러 가는 유창한 답.** [T3] 이 archetype을 규정하는 실패이며, grounding이
  구조적으로 막으려는 대상입니다. 관찰이 아니라 설계로부터 추론했습니다.
- **어떤 품질 기준도 넘지 못하는 약한 후보 집합.** [T2] ziptie.dev가 바로 이것에 대한
  fail-safe를 기술하는데, 이는 적어도 그 저자의 재구성 안에서는 그 실패가 대비할 만큼
  실재한다는 증거입니다.
- **드문 query 유형에서 확신에 차서 틀리는 ranking.** [T2] stackmatix.com은 weight가 query
  유형에 따라 달라진다고 언급합니다. [T3] 우리의 해석은 여러 query 유형에 걸쳐 조정된 ranking
  stack에는 상대적으로 더 못 다루는 유형이 있게 마련이며, read-only pipeline에는 그것을
  사용자에게 드러내는 장치가 없다는 것입니다. 답은 어느 쪽이든 똑같아 보이기 때문입니다.
- **질문을 잘못 읽었음을 알아챌 장치의 부재.** [T2] query intent parsing이 첫 단계로
  기술됩니다. [T3] 우리의 해석은 거기서 생긴 오류가 이후의 모든 단계로 전파되며, verification
  루프가 없는 pipeline에는 그것을 잡아낼 자리가 없다는 것입니다.

## 훔쳐 올 것 하나

citation을 나중에 붙이지 말고 generation 이전에 삽입하십시오.

[T2] ziptie.dev는 generation 이전에 citation이 삽입된 prompt assembly와 검색된 증거로 제한된
synthesis를 기술합니다. [T3] 이것이 일반화되는 이유에 대한 우리의 해석은 이렇습니다. 사후에
붙이는 귀속은 재구성 문제이며, case 03은 그것을 풀기 위해 별도의 agent 하나를 통째로 만들어야
합니다. generation 시점에 존재하는 귀속은 대신 generation에 대한 제약이 됩니다. 초안을 쓸 때
아직 출처를 들고 있는 시스템이라면 두 번째를 택해야 하며, 대부분의 시스템은 필요보다 일찍
요약함으로써 그 위치를 스스로 포기합니다.

## 따라 하지 말 것 하나

어떤 구체적 형태로든 reranker 내부 구성입니다.

두 재구성은 단계로 나뉜 ranking stack이 있다는 데 동의하고 그 안에 무엇이 있는지에서
갈라집니다. [T2] stackmatix.com은 cross-encoder reranking에 이어 entity와 authority 신호를
쓰는 ML reranker를 기술하며 자신의 weight가 근사치이고 query 유형에 따라 달라진다고 밝힙니다.
[T2] ziptie.dev는 세 번째 계층에 quality threshold를 둔 three-tier reranker를 기술합니다.
[T3] 우리의 해석은 둘 중 어느 명세를 복사하든 그것은 두 저자 모두 볼 수 없는 시스템에 대한
외부의 추측을 복사하는 일이라는 것입니다. hybrid retrieval, 단계적 reranking, 제한된
synthesis라는 그 형태가 둘이 동의하는 부분이며 교훈으로 다뤄야 할 유일한 부분입니다.

## 관련 자료

**Lab exercises:** `08-rag-basics`, `09-retrieval-quality`, `03-routing`,
`02-prompt-chaining`.

**Worked example:** `projects/answer-engine` — hybrid retrieval, staged rerank,
cite-before-generation, grounding eval을 갖춘 순수 workflow.

**Paper topics:** `04-memory-and-retrieval`, `07-evaluation`.

**다른 case:** `01-terminal-coding-agent`가 이 case와 짝을 이루는 반전입니다.
`03-orchestrator-worker-research`는 귀속 문제를 반대편 끝에서 풉니다.
`07-workflow-not-agent`는 autonomy 스펙트럼에서 이 case가 실은 속할 법한 자리입니다.
