# 🔒 piast-gate

![Python version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)
![Language](https://img.shields.io/badge/lang-Polish-red.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini-green.svg)
![License](https://img.shields.io/badge/license-GPL%203.0-blue.svg)

**Privacy-first LLM gateway — anonymize PII before it leaves your system.**

>[!IMPORTANT]
> This is a MVP Version — Currently supporting only **Google Gemini API** and **Polish-language** prompts.

---

## How It Works

**piast-gate** sits between your app and the model. It strips sensitive data before sending, then restores it after the response. The model never sees real PII.

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

Edit the `.env` file and provide your `GEMINI_API_KEY`.

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
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.5-flash
PL_NER_MODEL_NAME=radlab/pii-pl-v1.0
RATE_LIMIT_PER_MINUTE=60
API_KEYS=["your-secret-key"]
```

### Usage

```bash
curl -X POST http://localhost:8000/v1/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-key" \
  -d '{
    "model": "piast-gate",
    "messages": [
      {"role": "user", "content": "Mam na imię Jan Kowalski, email: jan@example.com"}
    ]
  }'
```


**Response:**
```json
{
  "response": "Cześć Jan Kowalski! Jak mogę Ci pomóc?"
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
