# Landing Lead MVP

A minimal backend that sits behind a landing-page lead form. It accepts a
JSON submission, normalizes the data, asks an LLM to summarize and classify
the lead, persists it to SQLite, and fires off a Telegram notification —
without blocking the response to the form.

## Pipeline

```
POST /lead
   │
   ▼
LeadIn         (Pydantic validation at the edge)
   │
   ▼
normalize  ──► Lead            (phone → +digits, email lowercased, source slugified)
   │
   ▼
classify   ──► Classification  (LLM, structured JSON output)
   │
   ▼
storage    ──► SQLite          (table `leads`)
   │
   ▼
notify     ──► Telegram        (background task — never blocks the response)
   │
   ▼
HTTP 201 { id, category, urgency, score, summary }
```

## Quick start — no external accounts required

```bash
docker compose up --build
```

Then in another terminal:

```bash
curl -X POST localhost:8000/lead \
  -H "Content-Type: application/json" \
  -d @payload.json
```

With an empty `LLM_API_KEY` the classifier returns a deterministic **mock**
response, so the full pipeline still runs end-to-end. Telegram behaves the
same way: missing token → notification is logged-skipped, not an error.

## Running with a real LLM (optional, 30 sec)

Sign up at [console.groq.com](https://console.groq.com) — free tier, no card
needed. Copy your API key into `.env`:

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
```

The client is OpenAI-compatible, so any provider that exposes that interface
works without code changes — Groq, OpenAI, DeepSeek, OpenRouter, local Ollama.
Swap providers by editing `.env`.

## Running with Telegram (optional)

1. Create a bot via [@BotFather](https://t.me/BotFather), copy the token.
2. Send any message to your bot, then fetch your `chat_id` from
   `https://api.telegram.org/bot<TOKEN>/getUpdates`.
3. Put both into `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
```

## Without Docker

```bash
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Three suites: `test_normalize` (pure functions), `test_classify` (mocked
LLM, three failure modes covered), `test_endpoint` (e2e through TestClient
with the mock classifier).

## Project layout

```
app/
  main.py        FastAPI app, single POST /lead endpoint
  schemas.py     LeadIn → Lead → Classification → EnrichedLead boundaries
  normalize.py   pure functions, no side effects, fully testable
  classify.py    LLM call + structured output + mock fallback
  storage.py     SQLite — schema lives in schema.sql
  notify.py      Telegram via httpx, fire-and-forget
  config.py      pydantic-settings, reads .env
prompts/
  classify.md    LLM prompt as a versioned artifact
tests/
  test_normalize.py
  test_classify.py    (mocked LLM)
  test_endpoint.py    (e2e via TestClient)
schema.sql       CREATE TABLE leads (...)
payload.json     example request body
```

## Design notes

- **Three Pydantic types mark stage boundaries.** `LeadIn` is what the form
  sends; `Lead` is canonical; `EnrichedLead` is what gets persisted. Nothing
  flows through the pipeline as `dict[str, Any]`.
- **Provider-agnostic LLM client.** Pointing `openai` at any OpenAI-compatible
  endpoint means swapping providers is an env change, not a refactor.
- **Structured output, not regex-parsed prose.** `response_format={"type":
  "json_object"}` plus Pydantic validation on our side. If the model returns
  bad JSON or violates the schema, we log and fall back to the mock — the
  request still succeeds.
- **Side-effects are optional and non-blocking.** Telegram runs as a
  `BackgroundTask` so the form gets its 201 even if Telegram is down or
  unconfigured. Same idea for the LLM: degraded mode beats a 500.
- **Prompt as a file**, not an f-string buried in `classify.py`. Diffable,
  reviewable, easy to A/B.
- **SQLite + `schema.sql`** instead of an ORM. One table, twelve lines.

## What is intentionally out of scope

This is an MVP, not a production system. The following are deliberate omissions:

- No retries / queue / dead-letter for LLM or Telegram — graceful skip and
  log only.
- No auth, no rate limiting, no CORS configuration — assume an upstream
  reverse-proxy handles it.
- No `phonenumbers` library — normalization is digits-only canonical form,
  not full E.164 validation.
- No metrics / tracing / structured JSON logs.

Each of those would be a real decision in production; in an MVP they would
be noise that obscures the shape of the pipeline.
