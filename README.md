# 🔒 piast-gate

![Python version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)
![Language](https://img.shields.io/badge/lang-Polish-red.svg)
![LLM](https://img.shields.io/badge/LLM-litellm%20multi--provider-green.svg)
![License](https://img.shields.io/badge/license-GPL%203.0-blue.svg)

**Privacy-first LLM gateway — anonymize PII before it leaves your system.**

>[!IMPORTANT]
> This is a MVP Version — Currently supporting only **Polish-language** prompts. The LLM backend
> is powered by [litellm](https://docs.litellm.ai/docs/providers), so any provider it supports
> (Gemini, OpenAI, Anthropic, and 100+ others) is a config change away — no code changes needed.

>[!WARNING]
> **PII scanning currently covers plain-text message content only.** Tool/function-call
> arguments and results, and any image content in multimodal messages, are forwarded to the
> provider **without** anonymization or redaction — only text goes through the
> anonymize/redact/deanonymize pipeline described below. Don't put sensitive data in tool
> arguments/results or images until this gap is closed.

---

## How It Works

**piast-gate** sits between your app and the model. It strips sensitive data before sending, then restores it after the response. The model never sees real PII.

Detected PII types: `PERSON`, `LOCATION`, `ORGANIZATION` (via NER), `EMAIL`, `PHONE`, `DATE`, `PESEL`, `NIP`, `REGON`, `BANK_ACCOUNT` (IBAN/NRB). PESEL, NIP, REGON and IBAN/NRB matches are checksum-validated, so a random digit string of the right length won't be flagged as PII.

The model's response is also scanned before being returned: since the model is only ever shown placeholders, any PII-shaped text it produces on its own (hallucinated, or a corrupted echo of a placeholder) is redacted rather than forwarded. On `stream=false` this checks the full response with every detector; on `stream=true` it's a lighter, word-buffered check using only the fast checksum-validated detectors (NER is too slow to run per streamed word) — multi-word hallucinated PII such as names isn't caught in streaming mode.

## Example

**Input:**
```
Mam na imię Jan Kowalski, mój email to jan@example.com, a PESEL: 85010112345
```

**Sent to LLM:**
```
Mam na imię <PERSON_1>, mój email to <EMAIL_1>, a PESEL: <PESEL_1>
```

**Returned to client:**
```
Mam na imię Jan Kowalski, mój email to jan@example.com, a PESEL: 85010112345
```

---

## Quick Start

The recommended way to run this project is using [uv](https://docs.astral.sh/uv/).

`litellm` is pinned to an exact version in `pyproject.toml` rather than a range — PyPI briefly
served two compromised releases (`1.82.7`, `1.82.8`) in March 2026, so this project only ever
bumps to a specific, verified-clean version rather than tracking latest automatically.

### 1. Installation

Using `uv` (fast & recommended):
```bash
git clone https://github.com/your-org/piast-gate.git
cd piast-gate
uv sync
```

Using standard `pip`:
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows alternate: source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
```

Edit the `.env` file and provide the API key for whichever provider `DEFAULT_MODEL` points at
(e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) — litellm reads these directly from
the environment, no code changes needed to switch providers.

### 3. Run

Using `uv`:
```bash
uv run uvicorn main:app --workers 4
```

Using standard `python`:
```bash
uvicorn main:app --workers 4
```

### 4. Tests

```bash
uv run pytest     # using uv
pytest            # using venv
```

#### Anonymization accuracy eval

`tests/eval/` measures detector accuracy (precision/recall/F1 per PII type) against a labeled dataset, separate from the pass/fail unit tests:

```bash
uv run python tests/eval/run_eval.py            # using uv
python tests/eval/run_eval.py                   # using venv

python tests/eval/run_eval.py -v                # show missed/spurious entities per example
python tests/eval/run_eval.py --category person_declension   # run one category only
```

Add new cases to `tests/eval/dataset.json` as `{"text": ..., "entities": [{"type": "PERSON", "value": "..."}]}`.

#### Load tests (k6)

`tests/perf/` holds [k6](https://k6.io/docs/get-started/installation/) load-test scripts that hit a running instance of the app:

- `test_concurrency.js` — ramps virtual users up to 100 to check behavior under concurrent load.
- `test_input_scaling.js` — sends a single very long message to see how latency scales with input size.
- `test_entity_scaling.js` — sends a message packed with many PII entities to see how latency scales with entity count.

Run the server with the mock LLM provider so requests don't hit the real Gemini API, and make sure `test-api-key` is in `API_KEYS`:

```env
LLM_PROVIDER=mock
API_KEYS=["test-api-key"]
```

```bash
uv run uvicorn main:app --workers 4
```

Then, in a separate terminal, run any of the scripts:

```bash
k6 run tests/perf/test_concurrency.js
k6 run tests/perf/test_input_scaling.js
k6 run tests/perf/test_entity_scaling.js
```

### PL NER Model Download

The PL NER model (`PL_NER_MODEL_NAME`, default [`radlab/pii-pl-v1.0`](https://huggingface.co/radlab/pii-pl-v1.0)) is **not** bundled with the repo or fetched during `uv sync`/`pip install`. It downloads itself automatically from the Hugging Face Hub on app startup (via a FastAPI `lifespan` hook), so `uvicorn main:app` will block for a bit on the first run while it downloads and loads into memory — the app won't accept traffic until that finishes.

The download is cached by `huggingface_hub` in the standard HF cache dir (`~/.cache/huggingface/hub`, or `%USERPROFILE%\.cache\huggingface\hub` on Windows — override with the `HF_HOME` env var), so subsequent restarts just load the local copy and start fast. No `HF_TOKEN` is needed since the model is public.

To pre-populate the cache ahead of time (e.g. as a separate Docker build/CI step, so the runtime container never hits the network), you can pre-download it manually:

```bash
uv run hf download radlab/pii-pl-v1.0
```

### 5. API Keys Configuration

Example configuration in `.env`:
```env
LLM_PROVIDER=litellm
DEFAULT_MODEL=gemini/gemini-2.5-flash
ALLOWED_MODELS=[]
GEMINI_API_KEY=your_api_key_here
PL_NER_MODEL_NAME=radlab/pii-pl-v1.0
RATE_LIMIT_PER_MINUTE=60
API_KEYS=["your-secret-key"]
```

To switch providers, change `DEFAULT_MODEL` to the litellm `"<provider>/<model>"` form (e.g.
`openai/gpt-4o`, `anthropic/claude-sonnet-4-5-20250929`) and set the matching API key env var — see
[litellm's provider docs](https://docs.litellm.ai/docs/providers) for the exact key name per
provider. Set `ALLOWED_MODELS` to a JSON list to restrict which `model` values a request may pass;
leave it empty to allow any model litellm supports.

#### Using an external LiteLLM Proxy instead of (or alongside) direct provider calls

If your infrastructure already runs a [LiteLLM Proxy](https://docs.litellm.ai/docs/simple_proxy)
as its own service, piast-gate can hand off all provider connectivity to it instead of calling
Gemini/OpenAI/Anthropic/etc. directly — it then only does anonymization and forwards the already
zero-PII request to your proxy. Both modes are available at once, selected per-request purely by
model prefix, so nothing here forces an all-or-nothing choice:

```env
LITELLM_PROXY_API_BASE=http://litellm-proxy.internal:4000
LITELLM_PROXY_API_KEY=sk-...          # a virtual key issued by the proxy, not a real provider key
DEFAULT_MODEL=litellm_proxy/gpt-4o    # <alias> is whatever your proxy's config.yaml exposes
```

Any model requested with the `litellm_proxy/` prefix (as `DEFAULT_MODEL`, in `ALLOWED_MODELS`, or
in a request's own `model` field) is routed to `LITELLM_PROXY_API_BASE`; every other prefix
(`gemini/`, `openai/`, `anthropic/`, ...) always calls that provider directly, regardless of
whether the proxy settings above are set — so you can, for example, keep `gemini/gemini-2.5-flash`
as your default while still allowing `litellm_proxy/internal-model` for specific requests, or vice
versa. Provider API keys (`GEMINI_API_KEY`, etc.) aren't needed for proxy-routed models — the proxy
holds those itself.

### Usage

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

`model` is optional — omit it to use `DEFAULT_MODEL`, or pass an explicit
`"<provider>/<model>"` string to route a specific request elsewhere (subject to
`ALLOWED_MODELS`, if set). The request also accepts, passed straight through to the provider:
`tools`, `tool_choice`, `response_format`, `top_p`, `stop`, `presence_penalty`,
`frequency_penalty`, `seed`, and multimodal `content` (a list of OpenAI-style content parts, e.g.
`[{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {"url": "..."}}]`) — see the
warning above about the PII-scanning gap for tool calls and images.


**Response:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gemini/gemini-2.5-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Cześć Jan Kowalski! Jak mogę Ci pomóc?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 18, "completion_tokens": 9, "total_tokens": 27}
}
```

---

## Performance

Benchmarks run with `uvicorn main:app --workers 4`.

### By message length

| Characters | avg | min | median | p(90) | p(95) |
|---|---|---|---|---|---|
| 1290 | 391 ms | 144 ms | 236 ms | 339 ms | 367 ms |
| 12900 | 1.46 s | 839 ms | 1.47 s | 1.78 s | 1.86 s |
| 64500 | 7.32 s | 5.45 s | 7.33 s | 8.70 s | 9.11 s |

### By placeholder count

| Placeholders | avg | min | median | p(90) | p(95) |
|---|---|---|---|---|---|
| 3 | 162 ms | 97 ms | 164 ms | 182 ms | 186 ms |
| 15 | 177 ms | 102 ms | 179 ms | 198 ms | 206 ms |
| 60 | 260 ms | 127 ms | 257 ms | 323 ms | 333 ms |
| 300 | 809 ms | 562 ms | 805 ms | 916 ms | 946 ms |
