# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A minimal FastAPI service that tracks phone app usage sessions. It is also exposed as an MCP server via `fastapi-mcp`, so all HTTP endpoints are simultaneously available as MCP tools.

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Docker

```bash
docker build -t phone-tracker .
docker run -p 8000:8000 phone-tracker
```

There are no tests and no linter configuration.

## Architecture

Everything lives in a single file: `main.py`.

**Database**: Supabase (PostgreSQL via REST API). All queries use `httpx` to call the Supabase PostgREST endpoint directly. The Supabase URL and publishable key are hardcoded in `main.py` — this is intentional (publishable keys are safe to expose).

**`app_sessions` table schema** (inferred from the code):
| column | type | notes |
|---|---|---|
| `id` | uuid/int | primary key |
| `app_name` | text | name of the tracked app |
| `opened_at` | timestamptz | set on open |
| `closed_at` | timestamptz | null while session is open |
| `minutes` | int | duration computed on close |

**Toggle logic** (`GET /toggle/{app_name}`): Queries for an open session (`closed_at is null`) for the given app. If none exists, inserts a new open session. If one exists, patches it with `closed_at` and `minutes` (duration in whole minutes). This is the core write path.

**Timezone**: All timestamps are written in CST (UTC+8, hardcoded as `timedelta(hours=8)`). The `/report` endpoint derives "today" from CST as well.

**MCP mounting**: `FastApiMCP(app).mount()` at the bottom of `main.py` exposes all routes as MCP tools automatically — no extra registration needed. Adding a new `@app.get(...)` route makes it available as an MCP tool without any other changes.

## Endpoints

| route | purpose |
|---|---|
| `GET /toggle/{app_name}` | Open or close a session for the named app |
| `GET /report` | Today's aggregated usage by app (CST date) |
| `GET /sessions` | Last 20 sessions, most recent first |
| `GET /health` | Liveness check |
