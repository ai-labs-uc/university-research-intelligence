# Beginner Setup — Simple v1

## 1. Install

Install:

```text
Python 3.12
Node.js 22 LTS
MySQL 8
MySQL Workbench
VS Code
Git
```

## 2. MySQL

Create the database first — the schema files deliberately don't create
one themselves (a hardcoded database name would silently put the tables
in the wrong place on a managed host like Railway, which assigns its
own database name):

```sql
CREATE DATABASE research_intelligence
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Then load, in order, against that database:

```text
database/001_schema.sql
database/002_seed.sql
```

e.g. `mysql -u root -p research_intelligence < database/001_schema.sql`.

(`database/004_auth_migration.sql` and `database/005_remove_programs_narrow_scope.sql`
are only for upgrading a database that already existed before login was
added / before the Programs feature was removed — skip both on a fresh
install, `001_schema.sql` already has the final table shape.)

Create the application user:

```sql
CREATE USER IF NOT EXISTS
'researchapp'@'localhost'
IDENTIFIED BY 'researchapp';

GRANT ALL PRIVILEGES
ON research_intelligence.*
TO 'researchapp'@'localhost';

FLUSH PRIVILEGES;
```

## 3. Environment

Copy each app's example file to a real `.env` next to it:

```text
backend/.env.example   →  backend/.env
frontend/.env.example  →  frontend/.env
```

Change `SECRET_KEY` to a real random value (it signs login sessions) —
e.g. `python -c "import secrets; print(secrets.token_hex(32))"`. Leave
`GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID` blank to skip Google
sign-in for now; email/password login works either way. See
`docs/AUTH.md` to set Google sign-in up later.

## 4. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Test:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## 5. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

You'll land on the login page — every page and API endpoint (besides
`/health` and `/api/auth/*`) requires a signed-in user now. Click
**Register** and create the first account (any email/password works
locally); every self-registered account defaults to the `RESEARCHER`
role. To try Swagger's endpoints directly instead of through the app,
register/login there too — `POST /api/auth/register` or
`POST /api/auth/login` returns an `access_token`, which Swagger's
**Authorize** button (top right of `/docs`) accepts as a Bearer token.

## 6. Run one pipeline manually

Either click "Run Pipeline" on the dashboard (while signed in), or open
Swagger, **Authorize** with a token from step 5, and run:

```text
POST /api/pipeline/run
```

## 7. Schedule the pipeline to run automatically (optional)

There is no separate orchestrator service — the OS's own scheduler is
enough to call the pipeline on a timer.

### Option A — call the standalone ETL script directly

Linux/macOS, edit the crontab with `crontab -e` and add a line to run
every day at 6 AM:

```text
0 6 * * * cd /path/to/backend && /path/to/.venv/bin/python -m app.etl.run_once >> /var/log/research_etl.log 2>&1
```

Windows: open Task Scheduler → Create Basic Task → Daily, and set:

```text
Program:  C:\path\to\backend\.venv\Scripts\python.exe
Args:     -m app.etl.run_once
Start in: C:\path\to\backend
```

### Option B — call the running API instead

If FastAPI is already running as a service, you can instead schedule a
plain HTTP call. `/api/pipeline/run` requires a valid session token
like every other `/api/*` route now, so register a dedicated account
for this (e.g. `etl-scheduler@uc-bcf.edu.ph`) and pass its token:

```text
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"etl-scheduler@uc-bcf.edu.ph","password":"..."}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/pipeline/run \
  -H "Authorization: Bearer $TOKEN"
```

A token expires after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h), so a
script that runs less often than that needs to log in fresh each time,
as above, rather than caching one token — option A (calling
`app.etl.run_once` directly, which isn't behind the API at all) avoids
this entirely and is simpler for pure scheduling.

Either option runs the exact same pipeline code — pick whichever fits
how you're already running things.

## 8. Daily startup order

```text
1. MySQL
2. FastAPI
3. React
```

That is all you need for Simple v1.

You do NOT need Redis, Celery, a local AI service, or a workflow
orchestrator in this simplified version. Classification and topic
extraction are plain keyword rules in
`backend/app/etl/classifier.py`, and scheduling is handled by cron or
Task Scheduler.
