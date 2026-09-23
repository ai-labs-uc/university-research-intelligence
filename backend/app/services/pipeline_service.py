"""
ETL pipeline: collect -> classify -> extract dates -> persist.

Defects fixed here relative to the previous version:

  1. DEADLINES WERE NEVER WRITTEN. The old INSERT omitted the `deadline`
     column entirely, so every row in production has deadline = NULL and
     no deadline notification could ever fire. Deadlines are now extracted
     (app.etl.dates) and stored, and a detail page is fetched when the
     listing excerpt did not carry one.
  2. scope_type held the opportunity type (`"scope": result`). It now
     holds NATIONAL / INTERNATIONAL.
  3. opportunity_type received values outside its ENUM
     ('CALL_FOR_PAPER_INTERNATIONAL'), which MySQL silently blanks in
     non-strict mode. It now receives GRANT / CALL_FOR_PAPER, with the
     composite value kept in `category` where the API expects it.
  4. Source health was never recorded, so `opportunity_sources.last_checked_at`
     and `last_status` were NULL for every row -- a dead scraper looked
     exactly like a healthy one with no new calls.
  5. `links[:20]` silently capped every source at 20 items.
  6. Expired and vanished items were never closed out, so the dashboard
     accumulated stale rows forever.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.etl.classifier import classify
from app.etl.collector import collect, fetch_detail
from app.etl.dates import derive_status, extract_deadline, extract_opening_date
from app.etl.filters import detect_indexing
from app.etl.sources import enabled_default_sources
from app.etl.utils import canonicalize_url, make_hash

log = logging.getLogger(__name__)

MAX_ITEMS_PER_SOURCE = 100
MAX_DETAIL_FETCHES_PER_SOURCE = 25
STALE_AFTER_DAYS = 45


UPSERT_SQL = text("""
INSERT INTO research_opportunities (
    opportunity_type, scope_type, category, title, organization, summary,
    country, currency, opening_date, deadline, source_url, canonical_url,
    content_hash, status, verification_status, indexing_flags,
    is_current, last_seen, discovered_at, updated_at
) VALUES (
    :opportunity_type, :scope_type, :category, :title, :organization, :summary,
    :country, :currency, :opening_date, :deadline, :source_url, :canonical_url,
    :content_hash, :status, :verification_status, :indexing_flags,
    1, :now, :now, :now
)
ON DUPLICATE KEY UPDATE
    title            = VALUES(title),
    summary          = VALUES(summary),
    category         = VALUES(category),
    scope_type       = VALUES(scope_type),
    opening_date     = VALUES(opening_date),
    -- Never overwrite a known deadline with NULL: a later run whose
    -- excerpt lacks the date must not erase what an earlier run found.
    deadline         = COALESCE(VALUES(deadline), deadline),
    status           = VALUES(status),
    indexing_flags   = VALUES(indexing_flags),
    is_current       = 1,
    last_seen        = VALUES(last_seen),
    updated_at       = VALUES(updated_at)
""")


def run_pipeline(db) -> dict:
    started_at = datetime.now(timezone.utc)
    run_id = _start_run(db)

    report = {
        "status": "SUCCESS",
        "sources": {},
        "discovered": 0,
        "inserted": 0,
        "skipped": 0,
        "with_deadline": 0,
        "errors": [],
    }

    for source in enabled_default_sources():
        code = source["code"]
        try:
            items = collect(source)
        except Exception as exc:                       # noqa: BLE001
            log.warning("Source %s failed: %s", code, exc)
            report["errors"].append(f"{code}: {exc}")
            report["sources"][code] = {"error": str(exc)}
            _record_source_health(db, source, 0, str(exc))
            continue

        stats = _process_items(db, source, items)
        report["sources"][code] = stats
        report["discovered"] += stats["discovered"]
        report["inserted"] += stats["inserted"]
        report["skipped"] += stats["skipped"]
        report["with_deadline"] += stats["with_deadline"]

        _record_source_health(db, source, stats["inserted"], None)

        # A source that yields items but never a deadline is the exact
        # failure mode that disabled notifications before. Make it loud.
        if stats["inserted"] and not stats["with_deadline"]:
            log.warning(
                "Source %s stored %s items but found 0 deadlines",
                code, stats["inserted"],
            )

    closed = _close_stale(db)
    report["closed_stale"] = closed

    if report["errors"]:
        report["status"] = "PARTIAL" if report["inserted"] else "FAILED"

    report["duration_seconds"] = round(
        (datetime.now(timezone.utc) - started_at).total_seconds(), 1
    )
    _finish_run(db, run_id, report)
    return report


def _process_items(db, source: dict, items: list[dict]) -> dict:
    stats = {"discovered": len(items), "inserted": 0, "skipped": 0,
             "with_deadline": 0}
    detail_fetches = 0
    now = datetime.now(timezone.utc)

    for item in items[:MAX_ITEMS_PER_SOURCE]:
        title, body, url = item["title"], item["body"], item["url"]
        if not title or not url:
            stats["skipped"] += 1
            continue

        classification = classify(title, body, source)
        if not classification:
            stats["skipped"] += 1
            continue

        deadline = extract_deadline(title, body)

        # Only pay for a detail fetch when we still lack a deadline --
        # feeds and listing cards usually already have it.
        if deadline is None and detail_fetches < MAX_DETAIL_FETCHES_PER_SOURCE:
            detail = fetch_detail(url)
            detail_fetches += 1
            if detail:
                deadline = extract_deadline(detail)
                body = body or detail

        if source.get("require_deadline") and deadline is None:
            # For publisher special-issue listings, an item with no open
            # deadline is noise rather than an opportunity.
            stats["skipped"] += 1
            continue

        opening = extract_opening_date(body)
        indexing = detect_indexing(title, body)

        try:
            db.execute(UPSERT_SQL, {
                "opportunity_type": classification["opportunity_type"],
                "scope_type": classification["scope_type"],
                "category": classification["category"],
                "title": title[:1000],
                "organization": source.get("name", "")[:255],
                "summary": body[:3000],
                "country": source.get("country"),
                "currency": source.get("currency"),
                "opening_date": opening,
                "deadline": deadline,
                "source_url": url[:1000],
                "canonical_url": canonicalize_url(url)[:1000],
                "content_hash": make_hash(url, title),
                "status": derive_status(deadline, opening),
                "verification_status": (
                    "PARTIALLY_VERIFIED" if source.get("mirrored")
                    else "UNVERIFIED"
                ),
                "indexing_flags": _json_or_none(indexing),
                "now": now,
            })
            stats["inserted"] += 1
            if deadline:
                stats["with_deadline"] += 1
        except Exception:                              # noqa: BLE001
            log.exception("Insert failed for %s", url)
            stats["skipped"] += 1

    db.commit()
    return stats


def _json_or_none(values: list[str]) -> str | None:
    import json
    return json.dumps(values) if values else None


# ------------------------------------------------------------------
# Source health
# ------------------------------------------------------------------
def _record_source_health(db, source: dict, count: int, error: str | None) -> None:
    """Populate last_checked_at / last_status, which were NULL for every
    row in production -- the reason nobody noticed the scrapers had never
    successfully run."""
    status = f"ERROR: {error}"[:50] if error else f"OK: {count} items"[:50]
    try:
        db.execute(
            text("""
                INSERT INTO opportunity_sources
                    (code, name, base_url, source_type, trust_level, enabled,
                     last_checked_at, last_status)
                VALUES
                    (:code, :name, :url, :source_type, :trust, 1, NOW(), :status)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    base_url = VALUES(base_url),
                    last_checked_at = NOW(),
                    last_status = VALUES(last_status)
            """),
            {
                "code": source["code"],
                "name": source.get("name", source["code"])[:255],
                "url": source.get("listing_url", "")[:1000],
                "source_type": {
                    "wp_api": "API", "rss": "RSS", "html": "HTML",
                }.get(source.get("kind", "html"), "HTML"),
                "trust": (
                    "OFFICIAL_PUBLISHER"
                    if source.get("scope") == "INTERNATIONAL"
                    else "OFFICIAL_AGENCY"
                ),
                "status": status,
            },
        )
        db.commit()
    except Exception:                                  # noqa: BLE001
        db.rollback()
        log.exception("Could not record health for %s", source["code"])


def _close_stale(db) -> int:
    """Close out expired items and ones that have stopped appearing, so
    the dashboard reflects genuinely active opportunities."""
    try:
        result = db.execute(
            text("""
                UPDATE research_opportunities
                   SET is_current = 0,
                       status = 'CLOSED'
                 WHERE is_current = 1
                   AND (
                        (deadline IS NOT NULL AND deadline < CURDATE())
                     OR (last_seen IS NOT NULL
                         AND last_seen < DATE_SUB(NOW(), INTERVAL :days DAY))
                   )
            """),
            {"days": STALE_AFTER_DAYS},
        )
        db.commit()
        return result.rowcount or 0
    except Exception:                                  # noqa: BLE001
        db.rollback()
        log.exception("Stale close-out failed")
        return 0


# ------------------------------------------------------------------
# Run bookkeeping
# ------------------------------------------------------------------
def _start_run(db) -> int | None:
    try:
        result = db.execute(
            text("INSERT INTO pipeline_runs (started_at, status) "
                 "VALUES (NOW(), 'RUNNING')")
        )
        db.commit()
        return result.lastrowid
    except Exception:                                  # noqa: BLE001
        db.rollback()
        return None


def _finish_run(db, run_id: int | None, report: dict) -> None:
    if not run_id:
        return
    try:
        db.execute(
            text("""
                UPDATE pipeline_runs
                   SET finished_at = NOW(),
                       status = :status,
                       discovered_count = :discovered,
                       inserted_count = :inserted,
                       skipped_count = :skipped,
                       error_message = :errors
                 WHERE id = :id
            """),
            {
                "status": report["status"],
                "discovered": report["discovered"],
                "inserted": report["inserted"],
                "skipped": report["skipped"],
                "errors": "; ".join(report["errors"])[:2000] or None,
                "id": run_id,
            },
        )
        db.commit()
    except Exception:                                  # noqa: BLE001
        db.rollback()
        log.exception("Could not finalise pipeline run %s", run_id)
