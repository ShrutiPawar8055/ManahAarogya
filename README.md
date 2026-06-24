# Manah Arogya (acm2k26)

Full-stack mental wellness platform with:
- Next.js frontend (`frontend/`)
- FastAPI backend (`backend/`)
- AI-powered assistant and recommenders (Cerebras with safe fallbacks)

## Features

- Google sign-in flow and user session handling
- Assessment flow (PHQ-9 + GAD-7), scoring, summary, alerts
- Dashboard overview
- Habit tracker + AI habit coach
- AI assistant chat with conversation history
- Resource library + AI recommendations
- Appointments booking and rescheduling
- Events discovery and registration
- Community posts, likes, replies, groups, mentors

## Tech Stack

- Frontend: Next.js 16, React 19
- Backend: FastAPI, Pydantic
- AI: Cerebras Chat Completions API (with fallback behavior if key is unavailable)
- Auth/UI session: Firebase (frontend side)

## Project Structure

```text
acm2k26/
  backend/
    main.py
    requirements.txt
    app/
  frontend/
    package.json
    src/
  requirements.txt   # root entrypoint -> backend/requirements.txt
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (recommended 20 LTS)
- npm

## Setup (Run from Root)

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\requirements.txt
```

Create `backend/.env`:

```env
APP_NAME=Manah Arogya Backend
APP_VERSION=1.0.0
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

SUPABASE_URL=
SUPABASE_SERVICE_KEY=

FIREBASE_CREDENTIALS_PATH=
FIREBASE_PROJECT_ID=
ALLOW_DEV_AUTH_BYPASS=true

CEREBRAS_API_KEY=
CEREBRAS_MODEL=gpt-oss-120b
CEREBRAS_TIMEOUT_SECONDS=30
```

Run backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Run frontend:

```bash
npm run dev
```

Open: `http://localhost:3000`

## Build / Verification

### Frontend checks

```bash
cd frontend
npm run lint
npm run build
```

### Backend quick check

Backend docs:
- `http://127.0.0.1:8000/docs`

Health endpoints:
- `GET /`
- `GET /health`

## GitHub Push Checklist (Before Push)

1. Ensure secrets are not staged (`backend/.env`, local keys, tokens).
2. Run frontend checks (`npm run lint` and `npm run build`).
3. Run backend and verify `/docs` + health endpoints.
4. Check changes:
   - `git status`
   - `git diff --stat`
5. Stage and commit:
   - `git add .`
   - `git commit -m "your message"`
6. Push:
   - `git push origin main`

## Notes

- API routes are mounted under `/api/v1` and are aligned with frontend module contracts.
- Protected endpoints accept `Authorization: Bearer <firebase_id_token>`. For local development, `ALLOW_DEV_AUTH_BYPASS=true` enables `X-User-Id` fallback.
- Root repo contains `backend/.git` as nested metadata in your local workspace. This is ignored by root `.gitignore` to avoid accidental nested-repo commits.
- Root `requirements.txt` is intentionally mapped to `backend/requirements.txt` for simple setup from `acm2k26` root.
