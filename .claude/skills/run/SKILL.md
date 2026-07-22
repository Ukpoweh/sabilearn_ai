---
name: run
description: Launch SabiLearn AI locally (Postgres via Docker, FastAPI backend, Streamlit frontend) for manual testing or screenshots. Use when asked to run, start, or verify this app end-to-end.
---

# Running SabiLearn AI locally

Three-part stack: Postgres (Docker), FastAPI backend (native process, port
8000), Streamlit frontend (native process, port 8501).

## 0. Prerequisites

- `.env` must exist in the repo root (copy from `.env.example` if missing)
  with a real `GEMINI_API_KEY` and:
  ```
  DATABASE_URL=postgresql+psycopg2://sabilearn:sabilearn@localhost:5433/sabilearn
  ```
- Python deps installed: `pip install -r requirements.txt`

## 1. Start Docker Desktop (if not already running)

On this machine Docker Desktop is not running by default and must be
started first:

```bash
"/c/Program Files/Docker/Docker/Docker Desktop.exe" &
disown
for i in $(seq 1 24); do docker ps >/dev/null 2>&1 && break; sleep 5; done
```

Took ~10s on a cold start in testing. If `docker ps` still fails after ~2
minutes, Docker Desktop needs manual attention (WSL2 backend issue, etc).

## 2. Start Postgres

```bash
docker-compose up -d database
for i in $(seq 1 15); do
  status=$(docker inspect -f '{{.State.Health.Status}}' sabilearn_ai-database-1 2>/dev/null)
  [ "$status" = "healthy" ] && break
  sleep 3
done
```

### Known gotcha: port 5432 conflict

This machine (and possibly others) has a **native Windows PostgreSQL 17
service** (`postgresql-x64-17`) already listening on port 5432. A native
(non-Docker) process connecting to `localhost:5432` hits that service
instead of the container — you'll see `password authentication failed
for user "sabilearn"` even though the container is healthy and its
credentials are correct. `psql`/`docker exec` into the container itself
still works fine (it's a real conflict at the host network level, not a
credentials problem).

**Fix already applied in this repo**: `docker-compose.yml` maps the
container to host port **5433**, and `DATABASE_URL` in `.env`/`.env.example`
points at `localhost:5433`. Don't revert this unless you've confirmed
nothing else is bound to 5432. To check for the same conflict elsewhere:

```bash
netstat -ano | grep ":5432" | grep LISTENING
```

## 3. Start the backend

```bash
PYTHONIOENCODING=utf-8 py -m uvicorn backend.main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
disown
for i in $(seq 1 20); do curl -sf http://127.0.0.1:8000/ >/dev/null && break; sleep 1; done
curl -s http://127.0.0.1:8000/          # → {"message":"Welcome to SabiLearn AI Backend!"}
curl -s http://127.0.0.1:8000/analytics # → total_lessons/avg_sentiment/etc, all zeroed on a fresh DB
```

`PYTHONIOENCODING=utf-8` is a belt-and-suspenders env var; `backend/ai/generator.py`
and `backend/ai/sentiment.py` also self-reconfigure stdout/stderr to UTF-8 on
import (Windows consoles default to cp1252, which can't encode the emoji in
their log prints and used to crash the app on startup).

If startup fails, check `/tmp/backend.log` — a `psycopg2.OperationalError:
... password authentication failed` almost always means the port-5432
conflict above, not a real credentials issue.

## 4. Start the frontend

```bash
PYTHONIOENCODING=utf-8 py -m streamlit run frontend/app.py --server.headless true --server.port 8501 > /tmp/frontend.log 2>&1 &
disown
for i in $(seq 1 30); do curl -sf http://127.0.0.1:8501 >/dev/null && break; sleep 1; done
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8501  # → 200
```

Open **http://localhost:8501** in a real browser to interact with it —
Dashboard / Generate Lesson / Submit Feedback via the sidebar. There is no
`chromium-cli` or Playwright installed in this environment for automated
screenshots; on this project that's fine to skip since it always runs on
a developer's own desktop with a real browser at hand. If a screenshot is
genuinely needed, `pip install playwright && playwright install chromium`
first.

## 5. Stop everything

Find the PIDs bound to the ports rather than pattern-killing — this dev
machine commonly has unrelated Python processes running for other
projects.

```bash
netstat -ano | grep -E ":8000 |:8501 " | grep LISTENING
taskkill //F //T //PID <backend_pid>
taskkill //F //T //PID <frontend_pid>
docker-compose stop database
```

### Known gotcha: always use `//T` (kill the whole tree)

`uvicorn --reload` spawns a child worker process under the PID you see
listening on the port. `taskkill //F //PID <pid>` **without `//T`** only
kills that one process — if it's the reloader, the actual worker child
survives as an orphan, silently keeps serving on the port, and does not
pick up any subsequent code changes. Symptom: you restart the backend,
your edits don't show up (old routes/behavior persist), and `netstat`
shows *two* PIDs `LISTENING` on the same port. Always kill with `//T`,
and if you ever see two PIDs on one port, kill both with `//T` and
restart clean.
