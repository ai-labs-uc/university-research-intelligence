"""
ETL pipeline: collect -> classify -> extract dates -> persist.

Defects fixed here relative to the original version:

1. DEADLINES WERE NEVER WRITTEN. The old INSERT omitted the `deadline`
   column entirely, so every row in production has deadline = NULL and
   no deadline notification could ever fire. Deadlines are now extracted
   (app.etl.dates) and stored, and a detail page is fetched when the
   listing excerpt did not carry one.
2. scope_type held the opportunity type (`"scope": result`). It now
   holds NATIONAL / INTERNATIONAL.
3. opportunity_type received values outside its allowed set
   ('CALL_FOR_PAPER_INTERNATIONAL'). It now receives GRANT /
   CALL_FOR_PAPER, with the composite value kept in `category` where
   the API expects it.
4. Source health was never recorded, so `opportunity_sources.last_checked_at`
   and `last_status` were NULL for every row -- a dead scraper looked
   exactly like a healthy one with no new calls.
5. `links[:20]` silently capped every source at 20 items.
6. Expired and vanished items were never closed out, so the dashboard
   accumulated stale rows forever.

Storage note: this collection is deduplicated/upserted on
`content_hash` rather than MySQL's `ON DUPLICATE KEY UPDATE` -- see
`_upsert_opportunity` below. A known deadline is never overwritten
with NULL: a later run whose excerpt lacks the date must not erase
what an earlier run found.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.core.database import next_id, utcnow
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


def run_pipeline(db) -> dict:
    started_at = utcnow()
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
        except Exception as exc:  # noqa: BLE001
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
        (utcnow() - started_at).total_seconds(), 1
    )
    _finish_run(db, run_id, report)
    return report


def _process_items(db, source: dict, items: list[dict]) -> dict:
    stats = {"discovered": len(items), "inserted": 0, "skipped": 0,
              "with_deadline": 0}
    detail_fetches = 0
    now = utcnow()

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
            _upsert_opportunity(
                db,
                content_hash=make_hash(url, title),
                fields={
                    "opportunity_type": classification["opportunity_type"],
                    "scope_type": classification["scope_type"],
                    "category": classification["category"],
                    "title": title[:1000],
                    "organization": source.get("name", "")[:255],
                    "summary": body[:3000],
                    "country": source.get("country"),
                    "currency": source.get("currency"),
                    "opening_date": opening,
                    "source_url": url[:1000],
                    "canonical_url": canonicalize_url(url)[:1000],
                    "status": derive_status(deadline, opening),
                    "verification_status": (
                        "PARTIALLY_VERIFIED" if source.get("mirrored")
                        else "UNVERIFIED"
                    ),
                    # Mongo stores arrays natively -- no need to
                    # serialize to a JSON string the way the MySQL
                    # JSON column required.
                    "indexing_flags": indexing or None,
                },
                deadline=deadline,
                now=now,
            )
            stats["inserted"] += 1
            if deadline:
                stats["with_deadline"] += 1
        except Exception:  # noqa: BLE001
            log.exception("Upsert failed for %s", url)
            stats["skipped"] += 1

    return stats


def _upsert_opportunity(db, content_hash: str, fields: dict, deadline, now: datetime) -> None:
    """Insert a new opportunity, or update an existing one matched by
    content_hash, without ever replacing a known deadline with None."""
    existing = db.research_opportunities.find_one({"content_hash": content_hash}, {"_id": 1})

    update_fields = dict(fields)
    update_fields.update({"is_current": True, "last_seen": now, "updated_at": now})
    if deadline is not None:
        update_fields["deadline"] = deadline

    if existing:
        db.research_opportunities.update_one({"_id": existing["_id"]}, {"$set": update_fields})
    else:
        doc = dict(update_fields)
        doc["_id"] = next_id("research_opportunities")
        doc["content_hash"] = content_hash
        doc["deadline"] = deadline
        doc["discovered_at"] = now
        db.research_opportunities.insert_one(doc)


# ------------------------------------------------------------------
# Source health
# ------------------------------------------------------------------
def _record_source_health(db, source: dict, count: int, error: str | None) -> None:
    """Populate last_checked_at / last_status, which were NULL for every
    row in production -- the reason nobody noticed the scrapers had never
    successfully run."""
    status = f"ERROR: {error}"[:50] if error else f"OK: {count} items"[:50]
    try:
        now = utcnow()
        name = source.get("name", source["code"])[:255]
        url = source.get("listing_url", "")[:1000]
        source_type = {
            "wp_api": "API", "rss": "RSS", "html": "HTML",
        }.get(source.get("kind", "html"), "HTML")
        trust = (
            "OFFICIAL_PUBLISHER"
            if source.get("scope") == "INTERNATIONAL"
            else "OFFICIAL_AGENCY"
        )

        existing = db.opportunity_sources.find_one({"code": source["code"]}, {"_id": 1})
        if existing:
            db.opportunity_sources.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "name": name,
                    "base_url": url,
                    "last_checked_at": now,
                    "last_status": status,
                }},
            )
        else:
            db.opportunity_sources.insert_one({
                "_id": next_id("opportunity_sources"),
                "code": source["code"],
                "name": name,
                "base_url": url,
                "source_type": source_type,
                "trust_level": trust,
                "enabled": True,
                "last_checked_at": now,
                "last_status": status,
                "created_at": now,
            })
    except Exception:  # noqa: BLE001
        log.exception("Could not record health for %s", source["code"])


def _close_stale(db) -> int:
    """Close out expired items and ones that have stopped appearing, so
    the dashboard reflects genuinely active opportunities."""
    try:
        now = utcnow()
        cutoff = now - timedelta(days=STALE_AFTER_DAYS)
        result = db.research_opportunities.update_many(
            {
                "is_current": True,
                "$or": [
                    {"deadline": {"$ne": None, "$lt": now}},
                    {"last_seen": {"$ne": None, "$lt": cutoff}},
                ],
            },
            {"$set": {"is_current": False, "status": "CLOSED"}},
        )
        return result.modified_count or 0
    except Exception:  # noqa: BLE001
        log.exception("Stale close-out failed")
        return 0


# ------------------------------------------------------------------
# Run bookkeeping
# ------------------------------------------------------------------
def _start_run(db) -> int | None:
    try:
        run_id = next_id("pipeline_runs")
        db.pipeline_runs.insert_one({
            "_id": run_id,
            "started_at": utcnow(),
            "finished_at": None,
            "status": "RUNNING",
            "discovered_count": 0,
            "inserted_count": 0,
            "updated_count": 0,
            "classified_count": 0,
            "skipped_count": 0,
            "error_message": None,
        })
        return run_id
    except Exception:  # noqa: BLE001
        return None


def _finish_run(db, run_id: int | None, report: dict) -> None:
    if not run_id:
        return
    try:
        db.pipeline_runs.update_one(
            {"_id": run_id},
            {"$set": {
                "finished_at": utcnow(),
                "status": report["status"],
                "discovered_count": report["discovered"],
                "inserted_count": report["inserted"],
                "skipped_count": report["skipped"],
                "error_message": "; ".join(report["errors"])[:2000] or None,
            }},
        )
    except Exception:  # noqa: BLE001
        log.exception("Could not finalise pipeline run %s", run_id)
