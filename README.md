# piast-gate

![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)
![Language](https://img.shields.io/badge/lang-Polish-red.svg)
![LLM](https://img.shields.io/badge/LLM-litellm%20multi--provider-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**A PII anonymization gateway for LLMs, built for Polish — not translated into it.**

piast-gate sits between your app and any LLM. It strips PII from a prompt before it leaves your system, and restores it in the response — the model itself never sees real data. Most anonymization tools bolt Polish onto an English-first pipeline and quietly lose accuracy on it; piast-gate is designed around Polish's grammar.

> [!IMPORTANT]
> MVP — Polish-language prompts only, by design: doing one language precisely instead of many languages approximately. The LLM backend runs on [litellm](https://docs.litellm.ai/docs/providers), so switching providers (Gemini, OpenAI, Anthropic, 100+ others) is a config change, not a code change.

> [!WARNING]
> Only plain-text message content is scanned. Tool/function-call arguments, results, and image content in multimodal messages are forwarded **unredacted**. Keep sensitive data out of those until this is closed.

## How it works

1. **Detect** — `PERSON`, `LOCATION`, `ORGANIZATION` (NER, Polish-tuned), `EMAIL`, `PHONE`, `DATE`, `PESEL`, `NIP`, `REGON`, `BANK_ACCOUNT`
2. **Anonymize** — each match is swapped for a placeholder before the request reaches the model
3. **Deanonymize** — placeholders in the response are swapped back for the original values

The response is also scanned before it's returned: since the model only ever sees placeholders, any PII-shaped text it produces on its own is redacted rather than forwarded. Streaming responses get a lighter, word-buffered version of this check (checksum detectors only — NER is too slow per streamed word).

```
Input:            Mam na imię Jan Kowalski, mój email to jan@example.com, a PESEL: 85010112345
Sent to LLM:       Mam na imię <PERSON_1>, mój email to <EMAIL_1>, a PESEL: <PESEL_1>
Returned to you:  Mam na imię Jan Kowalski, mój email to jan@example.com, a PESEL: 85010112345
```

## Quick start

```bash
git clone https://github.com/your-org/piast-gate.git
cd piast-gate
uv sync                    # or: pip install -e ".[dev]"

cp .env.example .env       # then set DEFAULT_MODEL's API key, e.g. GEMINI_API_KEY

uv run uvicorn main:app --workers 4
```

The Polish NER model (`radlab/pii-pl-v1.0` by default) downloads from Hugging Face on first startup and is cached locally after that — the first run will pause while it loads.

```env
LLM_PROVIDER=litellm
DEFAULT_MODEL=gemini/gemini-2.5-flash
GEMINI_API_KEY=your_api_key_here
API_KEYS={"your-secret-key": "your-client-name"}
```

`API_KEYS` maps each key to a client name for logging — every key has equal access. To switch providers, change `DEFAULT_MODEL` to litellm's `"<provider>/<model>"` form and set the matching key (`openai/gpt-4o` + `OPENAI_API_KEY`, etc.).

## Usage

```bash
curl -X POST http://localhost:8000/v1/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key" \
  -d '{
    "messages": [
      {"role": "user", "content": "Mam na imię Jan Kowalski, email: jan@example.com"}
    ]
  }'
```

`model` is optional (defaults to `DEFAULT_MODEL`). `tools`, `tool_choice`, `response_format`, `top_p`, `stop`, `presence_penalty`, `frequency_penalty`, `seed`, and multimodal `content` are all passed straight through to the provider — see the warning above regarding those.

<details>
<summary><strong>Response format</strong></summary>

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gemini/gemini-2.5-flash",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "Cześć Jan Kowalski! Jak mogę Ci pomóc?" },
      "finish_reason": "stop"
    }
  ],
  "usage": { "prompt_tokens": 18, "completion_tokens": 9, "total_tokens": 27 }
}
```

</details>

<details>
<summary><strong>Routing through an external LiteLLM Proxy</strong></summary>

If your infrastructure already runs a [LiteLLM Proxy](https://docs.litellm.ai/docs/simple_proxy), piast-gate can hand off provider connectivity to it instead of calling Gemini/OpenAI/Anthropic directly:

```env
LITELLM_PROXY_API_BASE=http://litellm-proxy.internal:4000
LITELLM_PROXY_API_KEY=sk-...          # a virtual key issued by the proxy
DEFAULT_MODEL=litellm_proxy/gpt-4o    # alias exposed by the proxy's config.yaml
```

Any model requested with the `litellm_proxy/` prefix routes to the proxy; every other prefix (`gemini/`, `openai/`, ...) always calls that provider directly — both modes can be used side by side, selected per-request by model prefix.

</details>

## Testing

```bash
uv run pytest                                   # unit tests
uv run python tests/eval/run_eval.py            # detector accuracy (precision/recall/F1)
```

<details>
<summary><strong>Load testing (k6)</strong></summary>

`tests/perf/` holds [k6](https://k6.io/docs/get-started/installation/) scripts against a running instance — run with `LLM_PROVIDER=mock` so requests don't hit a real provider:

```bash
k6 run tests/perf/test_concurrency.js       # ramps to 100 virtual users
k6 run tests/perf/test_input_scaling.js     # latency vs. message length
k6 run tests/perf/test_entity_scaling.js    # latency vs. PII entity count
```

</details>

## Performance

Benchmarked with `uvicorn main:app --workers 4`.

| Characters | avg | median | p95 |
|---|---|---|---|
| 1,290 | 391 ms | 236 ms | 367 ms |
| 12,900 | 1.46 s | 1.47 s | 1.86 s |
| 64,500 | 7.32 s | 7.33 s | 9.11 s |

| Placeholders | avg | median | p95 |
|---|---|---|---|
| 3 | 162 ms | 164 ms | 186 ms |
| 15 | 177 ms | 179 ms | 206 ms |
| 60 | 260 ms | 257 ms | 333 ms |
| 300 | 809 ms | 805 ms | 946 ms |

## License

[MIT](LICENSE)
