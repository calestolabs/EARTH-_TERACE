# EARTHTRACE Detective Assistant integration

This is the supplied ADK/FastAPI service, integrated with `components/Assistant.tsx`.
The published Next.js site is a static export; Python needs a separate HTTPS host.
No private .env, service-account key, virtual environment or session database from
the uploaded ZIP is included. The original ZIP remains unchanged.

## Local setup (PowerShell)

```powershell
cd ai-backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Fill the root .env with your server-only credentials.
uvicorn main:app --host 127.0.0.1 --port 8001
```

In the frontend root `.env.local`, supply the Firebase Web configuration from
`.env.example` and `NEXT_PUBLIC_AI_API_URL=http://127.0.0.1:8001`.
Enable Google authentication and authorize the frontend domain in Firebase.
For the hosted frontend, use an HTTPS backend URL, set CORS_ORIGINS to the exact
frontend origin and rebuild the frontend. A local URL cannot serve other visitors.

## Chat contract

POST `/api/ai/chat`, with `Authorization: Bearer <Firebase ID token>`:
`{"message":"...","session_id":null}`.
Response: `{"reply":"...","session_id":"UUID","mode":"demo"}`.
The frontend reuses the session ID for follow-ups, obtains a fresh token per
request, permits at most 4,000 characters including attached field notes, times
out after 60 seconds, and preserves the question after errors. New chat clears
only the current frontend session. Server session retention is managed separately.

Current evidence is sent as compact user-supplied context, explicitly labelled
browser-computed and unverified by the server. The agent instructions distinguish
this from the fictional built-in demo results. Demo responses carry a visible
DEMO DATA label in the UI. Do not treat the default demo tool as real observations.

`GET /health` is unauthenticated. The results endpoint requires authentication.
The supplied adapter's external analysis API contract is separate from the existing
`backend/main.py` analysis service: it is NOT automatically wired to that service.
Keep RESULTS_MODE=demo until you implement the results adapter and enforce ownership
of each investigation on the results service. This integration does not provision
Python hosting, model access, Firebase keys or an investigation results store.

The service uses SQLite sessions (persistent disk is needed on a host). Its original
README was outdated about authentication and persistence; the current code verifies
Firebase tokens and stores sessions with DatabaseSessionService. The uploaded API
tests also predate token authentication; update their auth fixture before running
against this secured service. No live Gemini response was verified during this update.
