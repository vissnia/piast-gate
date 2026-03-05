# 🔒 piast-gate

![Python version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)
![Language](https://img.shields.io/badge/lang-Polish-red.svg)

**Privacy-first LLM gateway — anonymize PII before it leaves your system.**

> Optimized for **Polish-language** prompts. Built for production.

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

### 1. Install

```bash
git clone https://github.com/your-org/piast-gate.git
cd piast-gate

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.sample .env
```

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
MODEL_NAME=gemini-2.0-flash
PL_NER_MODEL_NAME=pl_core_news_lg
RATE_LIMIT_PER_MINUTE=60
API_KEYS=["your-secret-key"]
```

### 3. Run

```bash
uvicorn main:app --workers 4
```

### Usage

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"message": "Mam na imię Jan Kowalski, email: jan@example.com"}'
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
