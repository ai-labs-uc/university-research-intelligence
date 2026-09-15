# Simple Architecture

## Technology responsibilities

```text
PYTHON
Engine
- ETL
- parsing
- normalization
- rule-based classification (call for paper / grant / out of scope)
- FastAPI

MYSQL
System of record
- users (login — password and/or Google, see docs/AUTH.md)
- researchers, projects (profile directory — not currently matched
  against; see database/ERD.md)
- sources
- opportunities (call for papers and grants only, + indexing flags)
- pipeline runs

REACT + TAILWIND
User interface
- login / register
- dashboard
- opportunities (Call for Papers / Grants tabs)
- source status
```

## Why this is deliberately plain

There is no orchestrator service, no local AI service, and no
containerization requirement. Everything runs as two processes
(FastAPI + React) plus one database:

```text
FastAPI  → uvicorn app.main:app
React    → npm run dev
MySQL    → mysqld
```

The ETL pipeline is just a Python function (`run_pipeline`). It can be
triggered three ways, all of which end up running the exact same code:

1. Manually, from `POST /api/pipeline/run` (e.g. via Swagger UI).
2. From the "Run Pipeline" button in the React dashboard.
3. On a schedule, with the OS scheduler calling
   `python -m app.etl.run_once` (cron on Linux/macOS, Task Scheduler on
   Windows). See `docs/BEGINNER_SETUP.md`.

## Why Redis/Celery were removed

The earlier design used:

```text
Redis + Celery + Celery Beat + n8n
```

That is unnecessarily complex for a first university deployment.
Python remains responsible for actual ETL and business logic; the OS's
own scheduler handles timing, so nothing extra needs to run
continuously in the background.

If scale later requires distributed workers or richer orchestration,
Redis/Celery or a workflow tool can be added back then.

## Why there is no local AI model

Classification and topic extraction are done with a small, editable
keyword list in `backend/app/etl/classifier.py` instead of calling an
LLM. That keeps the system:

- Free to run (no GPU or model download required).
- Deterministic and easy to explain to a research office.
- Simple to extend — add a phrase to `TYPE_KEYWORDS` or
  `TOPIC_VOCABULARY` and it applies on the next pipeline run.

If you want semantic classification later, that step can be swapped
back in without touching the database schema, the API, or the frontend
— `classify_type()` and `extract_topics()` are the only two functions
that would need to change.

The same file also has `detect_indexing()`, which flags Scopus/Web of
Science/other index phrasing found on the source page (see
`docs/PIPELINE.md`).

## Why there is no matching engine anymore

Two matching mechanisms existed at different points and both were cut.
An earlier version matched opportunities to individual researcher
profiles and raised per-researcher alerts; it was cut because the page
had no way to pick which researcher you were (it hardcoded one demo
profile), so it was really just a re-sorted subset of Opportunities. A
later version matched opportunities against academic units
(colleges/programs) on a Programs page; it was cut once the system's
scope narrowed to just calls for papers and grants — with only two
categories and a research office that reads the list directly, a
separate scored-matching view stopped earning its keep. See
`database/ERD.md` for the full history of both removals. Real login
exists now (`docs/AUTH.md`), which is the piece either kind of matching
would need if it came back later.

## Authentication

Every `/api/*` route except `/health` and `/api/auth/*` requires a
signed-in user (a FastAPI dependency on the whole router — see
`backend/app/api/routes.py`). Login is email/password, Google sign-in,
or both — see `docs/AUTH.md` for the full design, the Google Cloud
setup steps, and what's intentionally not built yet (password reset,
email verification, role-gated endpoints).
