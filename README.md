# Robin — empathetic chatbot API

A FastAPI backend for **Robin**, an emotionally supportive chatbot with a built-in
crisis safety net and India helplines. All code is in [`robin-api/`](robin-api).

## Run it

```bash
cd robin-api
cp .env.example .env          # add your OPENAI_API_KEY (or Groq, see the file)
pip install -r requirements.txt
python robin_single.py        # http://127.0.0.1:8000  (API docs at /docs)
```

Or with Docker:

```bash
cd robin-api
docker compose up --build     # http://localhost:8000
```

Run the tests:

```bash
pip install -r requirements-dev.txt
pytest
```

## API

| Method | Path | Body / notes |
|---|---|---|
| GET | `/health` | status and whether the AI key is set |
| POST | `/api/chat` | `{ "message": "...", "history": [{"role": "user"\|"assistant", "content": "..."}] }` |
| WS | `/ws/chat` | send the same JSON; receive `chunk` messages, then `done` (or `crisis` / `error`) |

## How the safety net works

1. Every message goes through `app/modules/crisis_detector.py` **before** it reaches
   the AI. Matching is on whole phrases, so everyday words like "diet" or "skill"
   don't trigger it, and simple tricks like "k1ll" are caught.
2. Severity 7 or above → the AI is skipped and Robin replies with India helplines.
3. Severity 4–6 → the AI is told to respond with extra care.
4. This works even if the AI key is missing or the AI service is down.

| Helpline | Number | Hours |
|---|---|---|
| Tele-MANAS (Govt. of India) | 14416 / 1-800-891-4416 | 24x7 |
| iCALL (TISS) | 9152987821 | Mon–Sat, 10 AM – 8 PM |
| Emergency | 112 | 24x7 |

Keyword rules can't catch everything. Re-check the helpline numbers before any public launch.
