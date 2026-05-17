# Landing Lead MVP

Backend behind a landing page form. Accepts a JSON lead, normalizes the
data, asks an LLM to summarize and classify it, stores it in SQLite, and
sends a Telegram notification.

## Pipeline

```
POST /lead -> normalize -> classify (LLM) -> SQLite -> Telegram
```

The Telegram step runs as a FastAPI background task, so a slow or
unreachable Telegram never delays the HTTP response.

## Quick start

```bash
docker compose up --build
curl -X POST localhost:8000/lead \
  -H "Content-Type: application/json" \
  -d @payload.json
```

With an empty `LLM_API_KEY` the classifier returns a deterministic mock
response, so the whole pipeline runs end-to-end without any external
accounts. Same for Telegram: no token, the notification is just logged
and skipped.

## With a real LLM

Get a free key at [console.groq.com](https://console.groq.com) (no card)
and put it in `.env`:

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
```

The client uses the `openai` SDK pointed at an OpenAI-compatible endpoint,
so swapping provider (Groq, OpenAI, DeepSeek, OpenRouter, local Ollama)
is an `.env` change, not a code change.

## With Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather).
2. Send any message to it, then get your `chat_id` from
   `https://api.telegram.org/bot<TOKEN>/getUpdates`.
3. Put both into `.env`:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

## Without Docker

```bash
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

## Tests

```bash
pytest
```

Three suites: pure normalization, classifier with a mocked LLM (covers
network error, bad JSON, schema-invalid response), and an e2e test of the
endpoint with TestClient and a temp SQLite DB.

## Layout

```
app/
  main.py        FastAPI app, POST /lead
  schemas.py     LeadIn -> Lead -> Classification -> EnrichedLead
  normalize.py   phone, email, source
  classify.py    LLM call + mock fallback
  storage.py     SQLite
  notify.py      Telegram via httpx
  config.py      pydantic-settings
prompts/
  classify.md    LLM prompt (kept out of code so it is diff-friendly)
tests/
schema.sql
payload.json
```
