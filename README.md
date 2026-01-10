# Prompt Inspection & Anonymization Security Tunnel (PIAST)

A secure gateway to anonymize PII before sending prompts to LLMs.

## Features (MVP)
- **PII Detection**: Regex-based detection for Email, Phone, and PESEL.
- **Anonymization**: Replaces PII with safe tokens `<PII:TYPE:ID>`.
- **Deanonymization**: Restores original values in the LLM response.
- **Mock LLM**: Simulates LLM interaction for testing.
- **FastAPI**: High-performance async API.

## Requirements
- Python 3.14+
- Dependencies listed in `requirements.txt`

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the server using Uvicorn:

```bash
uvicorn main:app
```

The API will be available at `http://127.0.0.1:8000`.

### API Documentation
Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

## Testing

Run unit and integration tests using `pytest`:

```bash
pytest
```

## Usage Example

**Request:**
```http
POST /chat
Content-Type: application/json

{
  "prompt": "My email is test@example.com"
}
```

**Response:**
```json
{
  "response": "LLM response to: My email is test@example.com"
}
```

(Note: The internal Mock LLM sees the anonymized version, e.g., `LLM response to: My email is <PII:EMAIL:xyz>`)
