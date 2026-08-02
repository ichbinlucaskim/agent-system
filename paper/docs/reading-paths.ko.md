# Reading paths

일곱 개 topic을 지나는 세 가지 경로입니다. 무엇을 만들려 하는지에 맞는 경로를
고르고 나머지 둘은 무시하세요.

**이 순서들은 합의가 아니라 학습상의 견해입니다.** 한 명의 독자가 이 특정한
논문 열여섯 편을 어떻게 배열하기로 했는지를 반영할 뿐입니다. 이 분야의 누구도
여기에 동의한 적이 없고, 뒷받침하는 survey도 없으며, 목적이 다른 독자라면 다르게
배열했을 것이고 그 역시 똑같이 정당합니다. 언제든 버려도 되는 출발 순서로
여기세요.

## 기본 경로

```text
01-reasoning
  -> 02-acting-and-tools
    -> 03-self-correction
      -> 04-memory-and-retrieval
        -> 07-evaluation
          -> 05-multi-agent
            -> 06-environment-and-interface
```

reasoning이 먼저인 이유는 나머지 전부가 중간 단계를 만들어 내는 하나의 호출 위에
세워지기 때문입니다. 그다음 acting이 그 단계들을 루프로 바꿉니다. 그다음
self-correction은 그 루프가 개선할 만한 첫 시도를 내놓은 뒤에 손을 뻗게 되는
것입니다. 그다음 memory와 retrieval은 루프가 context를 다 써 버리는 문제에 대한
답입니다.

evaluation이 multi-agent보다 앞에 오는 것은 의도적입니다. agent를 측정할 수 있게
되고 나면 조정에 관한 주장이 검증될 자리가 생기고, 개선과 단순한 재배치를 구분할
수 있게 됩니다.

**multi-agent가 뒤에 오는 이유는 단일 agent 루프를 먼저 이해해야 하기
때문입니다.** agent 사이에서 생기는 조정 문제의 거의 전부는 단일 agent 루프가
이미 갖고 있는 문제이며, 루프가 종료되지 않는 상황을 겪어 보기 전에 orchestration
문헌을 읽으면 multi-agent 논문들이 만난 적도 없는 문제에 대한 해법처럼 보입니다.

environment와 interface가 마지막인 것은 덜 중요해서가 아닙니다. 행동 표면이 설계
변수라는 그 핵심 논지는, 그 위의 다른 모든 interface를 이미 고정된 것으로 받아들인
뒤에야 가장 강하게 와닿기 때문입니다.

## RAG 중심 경로

```text
04-memory-and-retrieval
  -> 02-acting-and-tools
    -> 07-evaluation
```

자율 agent가 아니라 retrieval 시스템을 만드는 경우입니다. retrieval을 generation의
구성 요소로 보는 데서 시작하고, 그다음 acting 논문들을 읽어 앞에서 한 번만
검색하는 대신 다시 검색하기로 결정할 수 있게 하는 루프를 이해하고, 그다음
evaluation으로 갑니다. 이 스택에서 retrieval 품질만큼 자주 주장되면서 드물게
측정되는 부분도 없기 때문입니다.

여기서 reasoning을 건너뛰는 것은 의도적인 교환입니다. generation 단계가 왜 그렇게
동작하는지 이해하지 못한 채로 retrieval 시스템이 무엇을 하는지 이해하게 되며, 그
상태는 문제가 되기 전까지는 대체로 받아들일 만합니다.

## Evaluation 중심 경로

```text
07-evaluation
  -> 03-self-correction
    -> 02-acting-and-tools
```

이미 만들어진 agent를 넘겨받아 그것이 동작하는지 알아내야 하는 사람을 위한
경로입니다. 이 benchmark들이 어떻게 구성되고 그 구성이 무엇을 측정 가능하게
만드는지에서 시작합니다. 그다음 self-correction으로 갑니다. evaluator와 critic은
방향만 다를 뿐 같은 장치이며, 함께 읽으면 그 재사용이 분명해지기 때문입니다.
그다음 acting으로 가서 여러분이 측정하고 있는 루프를 이해합니다.

이 경로는 의도적으로 이 분야를 거꾸로 읽습니다. 숫자에 더 빨리 도달하는 대신, 그
숫자가 무엇으로 이루어져 있는지는 나중에 알게 됩니다.

## 세 경로 모두가 다루지 않는 것

이 라이브러리는 논문 열여섯 편입니다. pretraining, alignment 기법, inference
최적화, 모델 내부에 관한 문헌은 전혀 다루지 않습니다. 이는 reading path에서 빠진
것이 아니라 라이브러리 자체에서 빠진 것이며, 이 경로들 중 어느 것이든 완결된
것으로 여기기 전에 알아 둘 가치가 있습니다.
