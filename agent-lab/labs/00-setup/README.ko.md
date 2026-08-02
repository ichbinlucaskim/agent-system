# Lab 00 - Setup

## 목표

이 lab을 마치면 로컬 환경에서 Claude API에 인증하고, Messages API 요청을 보내고, streaming 응답과 non-streaming 응답 중 상황에 맞는 쪽을 의도적으로 선택하고, 모든 응답이 보고하는 token usage를 읽을 수 있습니다.

## 사전 준비

Python 3.11 이상과 Anthropic API key 외에는 없습니다. 개념: environment variable, 그리고 모델 호출이 HTTP 상의 요청과 응답이라는 점.

## 예상 소요 시간

20분에서 30분

## 배경

API key는 비밀 정보입니다. environment variable에 두고, 소스 코드에 넣지 않으며, prompt에도 넣지 않고, git이 추적하는 파일에도 넣지 않습니다. 이 저장소는 `.env.example`을 placeholder로 제공하고 `.env`는 git에서 제외합니다. `common/client.py`는 `ANTHROPIC_API_KEY`를 읽고 값이 없으면 이름이 붙은 에러를 발생시키므로, 자격 증명 누락이 실행 도중이 아니라 즉시 드러납니다.

Messages API 요청에는 세 가지가 필요합니다. `model`, 상한값인 `max_tokens`, 그리고 role과 content 쌍의 목록인 `messages`입니다. 응답은 문자열이 아닙니다. `content`는 block의 리스트이며 text block이 항상 첫 번째는 아니므로, `content[0]`으로 인덱싱하지 말고 항상 block type으로 걸러야 합니다. 응답에는 생성이 끝난 이유를 알려주는 `stop_reason`과 `usage`도 함께 담깁니다.

streaming과 non-streaming은 같은 답을 만들어냅니다. 다른 것은 호출자가 그 답을 언제 보게 되는가입니다. non-streaming 호출은 응답 전체가 생성될 때까지 블로킹되는데, 짧은 classification에는 괜찮지만 긴 응답에는 문제가 됩니다. non-streaming 요청에서 `max_tokens`가 크면 HTTP timeout 위험이 있기 때문입니다. streaming 호출은 생성되는 대로 text delta를 내보내므로 화면을 보고 있는 사람은 즉시 진행 상황을 확인할 수 있습니다.

`max_tokens`는 thinking을 포함해 모델이 내보내는 모든 것에 대한 하드 상한입니다. thinking이 기본으로 켜져 있는 모델에서는 눈에 보이는 답변 분량만 고려한 상한값이 응답을 문장 중간에서 잘라버릴 수 있습니다. `stop_reason`이 `max_tokens`로 돌아왔다면 그런 상황입니다.

token usage는 비용과 context budget 양쪽의 단위이며, 이 과정의 이후 내용은 모두 이 단위로 측정됩니다. `input_tokens`는 프롬프트 중 캐시되지 않은 나머지만 센다는 점에 유의하세요. 전체 프롬프트 크기는 input token에 cache read와 cache write를 더한 값입니다. `input_tokens`가 작아서 저렴해 보이는 실행이 실제로는 큰 캐시를 읽고 있을 뿐일 수 있습니다.

## 단계

1. `mask`를 구현해 API key를 노출 없이 출력할 수 있게 만드세요. 짧은 접두사와 접미사만 남기고 가운데는 대체하며, 안전한 접두사를 남기기에 너무 짧은 key는 점만 반환합니다.
2. `check_api_key`를 구현하세요. `common.client`의 `read_api_key`를 호출하고 마스킹된 형태를 반환합니다. `MissingAPIKeyError`는 그대로 전파시키세요. 자격 증명 누락은 실행을 중단시켜야지 품질만 떨어뜨려서는 안 됩니다.
3. `ask`를 구현하세요. user message 하나로 non-streaming 요청을 보내고 응답 객체를 그대로 반환해서 호출자가 `stop_reason`과 `usage`를 계속 읽을 수 있게 합니다.
4. `ask_streaming`을 구현하세요. `stream_text`를 순회하며 delta를 이어 붙입니다. `main`을 실행해 두 방식의 체감 차이를 비교해 보세요.
5. `usage_summary`를 구현하세요. `getattr`로 `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`를 방어적으로 읽고 각각 기본값 0을 적용한 뒤 `total_tokens` 항목을 추가합니다.
6. `main`을 구현해 마스킹된 key, model, usage를 포함한 non-streaming 답변, 그리고 도착하는 대로 출력되는 streaming 답변을 보여주세요. `MissingAPIKeyError`면 1을, 아니면 0을 반환합니다.

## 검증

```bash
pytest labs/00-setup/tests -v
```

오프라인 테스트는 key 처리, masking, usage 파싱을 다루며 API key 없이도 통과해야 합니다. 실제 호출을 하는 두 테스트는 `ANTHROPIC_API_KEY`가 없으면 깔끔하게 skip되고, 통과했다면 output token이 0이 아닌 실제 답변을 받았다는 뜻입니다.

## 더 나아가기

- `max_tokens`를 16으로 설정하고 `stop_reason`을 확인하세요. 잘림이 조용히 넘어가지 않고 응답에 드러나는지 확인합니다.
- 같은 prompt를 두 번 보내고 `usage`를 비교하세요. 그다음 긴 system prompt와 함께 보내고 다시 비교합니다.
- 두 호출 방식의 전체 소요 시간과, 각각 첫 글자가 보이기까지의 시간을 재보세요. 그 두 숫자의 차이가 streaming이 주는 이득입니다.

## 인증 시험 매핑

- **Anthropic, Building Effective Agents 및 Effective context engineering for AI agents**: augmented LLM building block이 확장하는 대상인 기본 모델 호출.
- **Databricks Generative AI Engineer Associate**: RAG 및 LLM chain을 포함한 application development.
- **NVIDIA NCA Generative AI LLMs**: LLM integration and deployment, Python libraries for LLMs.

시험 목표는 시간이 지나면 바뀝니다. 이것을 syllabus가 아니라 참고용 지침으로 여기고 공식 시험 가이드를 직접 확인하세요. 전체 표는 `docs/cert-mapping.md`에 있습니다.
