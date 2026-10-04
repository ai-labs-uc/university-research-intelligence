from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.core.database import SessionLocal, get_db, utcnow
from app.core.security import get_current_user

router = APIRouter()


def _serialize(doc: dict | None) -> dict | None:
    """Mongo documents key on _id; the frontend expects `id`."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return doc


def _with_source_name_and_days(opp: dict, sources_by_id: dict) -> dict:
    """Mirrors the old SELECT's computed columns:
    COALESCE(s.name, o.organization) AS source_name, and
    DATEDIFF(o.deadline, CURDATE()) AS days_until_deadline.
    """
    source = sources_by_id.get(opp.get("source_id"))
    opp = _serialize(opp)
    opp["source_name"] = (source["name"] if source else None) or opp.get("organization")

    deadline = opp.get("deadline")
    if deadline is None:
        opp["days_until_deadline"] = None
    else:
        today = utcnow().date()
        deadline_date = deadline.date() if hasattr(deadline, "date") else deadline
        opp["days_until_deadline"] = (deadline_date - today).days
    return opp


def _list_opportunities(db, match: dict, limit: int) -> list[dict]:
    """Shared listing logic for /opportunities, /grants and
    /call-for-papers. Items with a deadline first and soonest-first, so
    the most actionable opportunity is at the top (previously ordered
    by id DESC, which surfaced whatever was scraped last rather than
    what closes next).

    This application's opportunity volume is small (a university
    research office tracking grants/CFPs — hundreds to low thousands
    of rows, not millions), so fetching the matched set and sorting in
    Python is simpler and just as correct as a native Mongo "nulls
    last" sort, which needs its own aggregation stage to get right.
    """
    rows = list(db.research_opportunities.find(match))
    rows.sort(
        key=lambda r: (
            r.get("deadline") is None,
            r.get("deadline") or datetime.max,
            -r["_id"],
        )
    )
    rows = rows[:limit]

    source_ids = {r["source_id"] for r in rows if r.get("source_id") is not None}
    sources_by_id = (
        {s["_id"]: s for s in db.opportunity_sources.find({"_id": {"$in": list(source_ids)}})}
        if source_ids
        else {}
    )

    return [_with_source_name_and_days(r, sources_by_id) for r in rows]


# ============================================================
# DASHBOARD
# ============================================================


@router.get("/dashboard")
def dashboard(
    _user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    today = utcnow()
    pipeline = [
        {"$match": {"is_current": True}},
        {
            "$group": {
                "_id": None,
                "total_opportunities": {"$sum": 1},
                "grants": {
                    "$sum": {
                        "$cond": [
                            {"$regexMatch": {"input": {"$ifNull": ["$category", ""]}, "regex": "^GRANT"}},
                            1,
                            0,
                        ]
                    }
                },
                "national_cfp": {"$sum": {"$cond": [{"$eq": ["$category", "CALL_FOR_PAPER_NATIONAL"]}, 1, 0]}},
                "international_cfp": {
                    "$sum": {"$cond": [{"$eq": ["$category", "CALL_FOR_PAPER_INTERNATIONAL"]}, 1, 0]}
                },
                "with_deadline": {"$sum": {"$cond": [{"$ne": ["$deadline", None]}, 1, 0]}},
                "closing_soon": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$deadline", None]},
                                    {"$gte": ["$deadline", today]},
                                    {"$lte": ["$deadline", today + timedelta(days=30)]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
    ]
    result = list(db.research_opportunities.aggregate(pipeline))
    row = result[0] if result else {}

    return {
        "total_opportunities": row.get("total_opportunities", 0),
        "grants": int(row.get("grants", 0)),
        "national_call_for_papers": int(row.get("national_cfp", 0)),
        "international_call_for_papers": int(row.get("international_cfp", 0)),
        "with_deadline": int(row.get("with_deadline", 0)),
        "closing_soon": int(row.get("closing_soon", 0)),
    }


# ============================================================
# LISTINGS
# ============================================================


@router.get("/opportunities")
def opportunities(
    closing_within_days: int | None = Query(
        None, ge=1, le=365,
        description="Only items whose deadline falls within this many days.",
    ),
    limit: int = Query(500, ge=1, le=1000),
    _user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    match: dict = {"is_current": True}
    if closing_within_days:
        today = utcnow()
        match["deadline"] = {
            "$ne": None,
            "$gte": today,
            "$lte": today + timedelta(days=closing_within_days),
        }
    return _list_opportunities(db, match, limit)


@router.get("/grants")
def grants(
    limit: int = Query(500, ge=1, le=1000),
    _user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    match = {"is_current": True, "category": {"$regex": "^GRANT"}}
    return _list_opportunities(db, match, limit)


@router.get("/call-for-papers")
def call_for_papers(
    scope: str | None = Query(
        None, description="NATIONAL or INTERNATIONAL. Omit for both."
    ),
    limit: int = Query(500, ge=1, le=1000),
    _user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if scope:
        normalized = scope.strip().upper()
        if normalized not in ("NATIONAL", "INTERNATIONAL"):
            raise HTTPException(
                status_code=400,
                detail="scope must be NATIONAL or INTERNATIONAL",
            )
        match = {"is_current": True, "category": f"CALL_FOR_PAPER_{normalized}"}
    else:
        match = {"is_current": True, "category": {"$regex": "^CALL_FOR_PAPER"}}

    return _list_opportunities(db, match, limit)


@router.get("/sources")
def sources(
    _user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    rows = list(db.opportunity_sources.find({}).sort("code", 1))
    return [_serialize(r) for r in rows]


# ============================================================
# PIPELINE
# ============================================================


def _run_pipeline_job() -> None:
    """Runs on its own handle: PyMongo's client is pooled/thread-safe,
    so this doesn't need the open/close dance the old per-request SQL
    session did, but SessionLocal() is kept so this still reads the
    same way as before."""
    from app.services.pipeline_service import run_pipeline

    db = SessionLocal()
    run_pipeline(db)


@router.post("/pipeline/run")
def trigger_pipeline(
    background: BackgroundTasks,
    _user: dict = Depends(get_current_user),
):
    """Start a harvest in the background.

    A full run takes minutes; doing it inline would exceed the platform's
    request timeout and return a 502 even though the work succeeded.
    """
    background.add_task(_run_pipeline_job)
    return {"status": "started"}


@router.get("/pipeline/status")
def pipeline_status(_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Per-source health plus data-quality warnings.

    This endpoint exists because the original failure was invisible: every
    source row had last_checked_at = NULL and every opportunity had
    deadline = NULL, and nothing in the UI said so.
    """
    sources_rows = list(
        db.opportunity_sources.find(
            {},
            {"code": 1, "name": 1, "source_type": 1, "enabled": 1,
             "last_checked_at": 1, "last_status": 1},
        )
    )
    # Nulls first, then code ascending — mirrors
    # "ORDER BY last_checked_at IS NULL DESC, code".
    sources_rows.sort(key=lambda s: (s.get("last_checked_at") is not None, s["code"]))
    sources_rows = [_serialize(s) for s in sources_rows]

    total = db.research_opportunities.count_documents({})
    with_deadline = db.research_opportunities.count_documents({"deadline": {"$ne": None}})
    active = db.research_opportunities.count_documents({"is_current": True})

    last_run = _serialize(db.pipeline_runs.find_one(sort=[("_id", -1)]))

    warnings = []
    never_checked = [s["code"] for s in sources_rows if not s.get("last_checked_at")]
    if never_checked:
        warnings.append(
            f"{len(never_checked)} source(s) have never been checked: "
            + ", ".join(never_checked)
        )

    failing = [s["code"] for s in sources_rows if (s.get("last_status") or "").startswith("ERROR")]
    if failing:
        warnings.append("Source(s) failing on last run: " + ", ".join(failing))

    if total and with_deadline == 0:
        warnings.append(
            "No opportunity has a deadline — deadline notifications "
            "cannot fire. Check deadline extraction."
        )
    elif total and with_deadline < total * 0.25:
        warnings.append(
            f"Only {with_deadline} of {total} opportunities have a deadline."
        )

    return {
        "sources": sources_rows,
        "stats": {"total": total, "active": active, "with_deadline": with_deadline},
        "last_run": last_run,
        "warnings": warnings,
    }


# ============================================================
# ALERTS / NOTIFICATIONS
# ============================================================


@router.get("/alerts")
def list_alerts(
    unread_only: bool = Query(False),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    match: dict = {"user_id": user["_id"]}
    if unread_only:
        match["is_read"] = False

    alert_rows = list(db.alerts.find(match).sort("created_at", -1).limit(200))
    opp_ids = {a["opportunity_id"] for a in alert_rows}
    opps_by_id = (
        {o["_id"]: o for o in db.research_opportunities.find({"_id": {"$in": list(opp_ids)}})}
        if opp_ids
        else {}
    )

    today = utcnow().date()
    results = []
    for alert in alert_rows:
        opp = opps_by_id.get(alert["opportunity_id"])
        if opp is None:
            # Matches the original INNER JOIN: an alert pointing at an
            # opportunity that no longer exists is dropped, not shown
            # with blank fields.
            continue

        row = _serialize(alert)
        row["title"] = opp.get("title")
        row["deadline"] = opp.get("deadline")
        row["source_url"] = opp.get("source_url")
        row["category"] = opp.get("category")

        deadline = opp.get("deadline")
        if deadline is None:
            row["days_until_deadline"] = None
        else:
            deadline_date = deadline.date() if hasattr(deadline, "date") else deadline
            row["days_until_deadline"] = (deadline_date - today).days

        results.append(row)
    return results


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    result = db.alerts.update_one(
        {"_id": alert_id, "user_id": user["_id"]},
        {"$set": {"is_read": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok"}


@router.post("/notifications/run")
def trigger_notifications(
    _user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Run the deadline scan now. Also runs nightly via the cron service
    defined in render.yaml."""
    from app.services.notification_service import run_deadline_notifications

    return run_deadline_notifications(db)


@router.get("/notifications/prefs")
def get_prefs(user: dict = Depends(get_current_user), db=Depends(get_db)):
    row = db.notification_prefs.find_one({"_id": user["_id"]})
    if row:
        return {
            "user_id": row["_id"],
            "lead_days": row["lead_days"],
            "email_enabled": row["email_enabled"],
            "inapp_enabled": row["inapp_enabled"],
            "digest_mode": row["digest_mode"],
            "categories_filter": row.get("categories_filter"),
            "updated_at": row.get("updated_at"),
        }
    return {
        "user_id": user["_id"],
        "lead_days": "30,14,7,3,1",
        "email_enabled": 1,
        "inapp_enabled": 1,
        "digest_mode": 1,
        "categories_filter": None,
    }


@router.put("/notifications/prefs")
def update_prefs(
    payload: dict,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lead_days = str(payload.get("lead_days", "30,14,7,3,1"))
    parts = [p.strip() for p in lead_days.split(",") if p.strip()]
    if not parts or not all(p.isdigit() and 0 < int(p) <= 365 for p in parts):
        raise HTTPException(
            status_code=400,
            detail="lead_days must be comma-separated numbers between 1 and 365.",
        )

    db.notification_prefs.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "lead_days": ",".join(parts),
                "email_enabled": 1 if payload.get("email_enabled", True) else 0,
                "inapp_enabled": 1 if payload.get("inapp_enabled", True) else 0,
                "digest_mode": 1 if payload.get("digest_mode", True) else 0,
                "categories_filter": payload.get("categories_filter"),
                "updated_at": utcnow(),
            }
        },
        upsert=True,
    )
    return {"status": "ok"}
