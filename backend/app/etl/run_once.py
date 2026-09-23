"""
Standalone ETL entry point, run by the Render cron service (see
render.yaml) or any OS scheduler.

One full cycle: collect -> classify -> extract deadlines -> persist, then
scan for approaching deadlines and send notifications.

Run the whole thing:
    python -m app.etl.run_once

Or one half at a time:
    python -m app.etl.run_once --harvest-only
    python -m app.etl.run_once --notify-only
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from app.core.database import SessionLocal
from app.services.notification_service import run_deadline_notifications
from app.services.pipeline_service import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("etl")


def main() -> int:
    parser = argparse.ArgumentParser(description="Research Intelligence ETL")
    parser.add_argument("--harvest-only", action="store_true")
    parser.add_argument("--notify-only", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    exit_code = 0

    try:
        if not args.notify_only:
            report = run_pipeline(db)
            log.info("Harvest: %s", json.dumps(report, default=str))

            if report["status"] == "FAILED":
                exit_code = 1
            # A run that stores items but finds no deadlines is the exact
            # silent failure that disabled notifications before. Surface it
            # as a non-zero exit so the scheduler reports it.
            elif report["inserted"] and not report["with_deadline"]:
                log.error(
                    "Harvest stored %s items but found 0 deadlines — "
                    "deadline extraction is likely broken.",
                    report["inserted"],
                )
                exit_code = 1

        if not args.harvest_only:
            result = run_deadline_notifications(db)
            log.info("Notifications: %s", json.dumps(result, default=str))

        return exit_code

    except Exception as exc:                           # noqa: BLE001
        log.exception("ETL run failed: %s", exc)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
