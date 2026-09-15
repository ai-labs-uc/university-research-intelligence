"""
Standalone ETL entry point.

This replaces n8n's job of triggering the pipeline on a schedule. It
opens its own database session and runs one full collect -> classify ->
match cycle, then exits. Point your OS scheduler at this instead of
running a separate orchestrator service:

Linux/macOS (crontab -e), every day at 6 AM:
    0 6 * * * cd /path/to/backend && /path/to/.venv/bin/python -m app.etl.run_once >> /var/log/research_etl.log 2>&1

Windows (Task Scheduler), daily action:
    Program:  C:\\path\\to\\backend\\.venv\\Scripts\\python.exe
    Args:     -m app.etl.run_once
    Start in: C:\\path\\to\\backend

You can also just call it by hand any time:
    python -m app.etl.run_once
"""

import sys

from app.core.database import SessionLocal
from app.services.pipeline_service import run_pipeline


def main() -> int:
    db = SessionLocal()
    try:
        result = run_pipeline(db)
        print(result)
        return 0
    except Exception as exc:
        print(f"Pipeline run failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
