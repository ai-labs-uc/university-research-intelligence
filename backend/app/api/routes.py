from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user


router = APIRouter()


# Shared projection, so every listing endpoint returns the same shape and
# the frontend can render one card component everywhere.
_OPPORTUNITY_SELECT = """
    SELECT
        o.*,
        COALESCE(s.name, o.organization) AS source_name,
        CASE
            WHEN o.deadline IS NULL THEN NULL
            ELSE DATEDIFF(o.deadline, CURDATE())
        END AS days_until_deadline
    FROM research_opportunities o
    LEFT JOIN opportunity_sources s ON s.id = o.source_id
"""

# Items with a deadline first and soonest-first, so the most actionable
# opportunity is at the top. Previously this ordered by id DESC, which
# surfaced whatever was scraped last rather than what closes next.
_OPPORTUNITY_ORDER = """
    ORDER BY
        CASE WHEN o.deadline IS NULL THEN 1 ELSE 0 END,
        o.deadline ASC,
        o.id DESC
    LIMIT :limit
"""


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard")
def dashboard(
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            SELECT
                COUNT(*) AS total_opportunities,
                SUM(category LIKE 'GRANT%')                      AS grants,
                SUM(category = 'CALL_FOR_PAPER_NATIONAL')        AS national_cfp,
                SUM(category = 'CALL_FOR_PAPER_INTERNATIONAL')   AS international_cfp,
                SUM(deadline IS NOT NULL)                        AS with_deadline,
                SUM(deadline IS NOT NULL
                    AND deadline BETWEEN CURDATE()
                    AND DATE_ADD(CURDATE(), INTERVAL 30 DAY))    AS closing_soon
            FROM research_opportunities
            WHERE is_current = 1
        """)
    ).mappings().first()

    return {
        "total_opportunities": row["total_opportunities"] or 0,
        "grants": int(row["grants"] or 0),
        "national_call_for_papers": int(row["national_cfp"] or 0),
        "international_call_for_papers": int(row["international_cfp"] or 0),
        "with_deadline": int(row["with_deadline"] or 0),
        "closing_soon": int(row["closing_soon"] or 0),
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
    db: Session = Depends(get_db),
):
    clause = "WHERE o.is_current = 1"
    params: dict = {"limit": limit}

    if closing_within_days:
        clause += (
            " AND o.deadline IS NOT NULL"
            " AND o.deadline BETWEEN CURDATE()"
            " AND DATE_ADD(CURDATE(), INTERVAL :days DAY)"
        )
        params["days"] = closing_within_days

    return db.execute(
        text(_OPPORTUNITY_SELECT + clause + _OPPORTUNITY_ORDER), params
    ).mappings().all()


@router.get("/grants")
def grants(
    limit: int = Query(500, ge=1, le=1000),
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.execute(
        text(
            _OPPORTUNITY_SELECT
            + " WHERE o.is_current = 1 AND o.category LIKE 'GRANT%'"
            + _OPPORTUNITY_ORDER
        ),
        {"limit": limit},
    ).mappings().all()


@router.get("/call-for-papers")
def call_for_papers(
    scope: str | None = Query(
        None, description="NATIONAL or INTERNATIONAL. Omit for both."
    ),
    limit: int = Query(500, ge=1, le=1000),
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    params: dict = {"limit": limit}

    if scope:
        normalized = scope.strip().upper()
        if normalized not in ("NATIONAL", "INTERNATIONAL"):
            raise HTTPException(
                status_code=400,
                detail="scope must be NATIONAL or INTERNATIONAL",
            )
        clause = " WHERE o.is_current = 1 AND o.category = :category"
        params["category"] = f"CALL_FOR_PAPER_{normalized}"
    else:
        clause = " WHERE o.is_current = 1 AND o.category LIKE 'CALL_FOR_PAPER%'"

    return db.execute(
        text(_OPPORTUNITY_SELECT + clause + _OPPORTUNITY_ORDER), params
    ).mappings().all()


@router.get("/sources")
def sources(
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.execute(
        text("SELECT * FROM opportunity_sources ORDER BY code")
    ).mappings().all()


# ============================================================
# PIPELINE
# ============================================================

def _run_pipeline_job() -> None:
    """Runs on its own session: the request's session is closed as soon as
    the response returns, long before a full harvest finishes."""
    from app.services.pipeline_service import run_pipeline

    db = SessionLocal()
    try:
        run_pipeline(db)
    finally:
        db.close()


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
def pipeline_status(_user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Per-source health plus data-quality warnings.

    This endpoint exists because the original failure was invisible: every
    source row had last_checked_at = NULL and every opportunity had
    deadline = NULL, and nothing in the UI said so.
    """
    sources_rows = db.execute(
        text("""
            SELECT code, name, source_type, enabled,
                   last_checked_at, last_status
              FROM opportunity_sources
             ORDER BY last_checked_at IS NULL DESC, code
        """)
    ).mappings().all()

    stats = db.execute(
        text("""
            SELECT COUNT(*) AS total,
                   SUM(deadline IS NOT NULL) AS with_deadline,
                   SUM(is_current = 1)       AS active
              FROM research_opportunities
        """)
    ).mappings().first()

    last_run = db.execute(
        text("SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 1")
    ).mappings().first()

    warnings = []
    never_checked = [s["code"] for s in sources_rows if not s["last_checked_at"]]
    if never_checked:
        warnings.append(
            f"{len(never_checked)} source(s) have never been checked: "
            + ", ".join(never_checked)
        )

    failing = [s["code"] for s in sources_rows
               if (s["last_status"] or "").startswith("ERROR")]
    if failing:
        warnings.append("Source(s) failing on last run: " + ", ".join(failing))

    total = int(stats["total"] or 0)
    with_deadline = int(stats["with_deadline"] or 0)
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
        "stats": {
            "total": total,
            "active": int(stats["active"] or 0),
            "with_deadline": with_deadline,
        },
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
    db: Session = Depends(get_db),
):
    clause = "AND a.is_read = 0" if unread_only else ""
    return db.execute(
        text(f"""
            SELECT a.*, o.title, o.deadline, o.source_url, o.category,
                   DATEDIFF(o.deadline, CURDATE()) AS days_until_deadline
              FROM alerts a
              JOIN research_opportunities o ON o.id = a.opportunity_id
             WHERE a.user_id = :user_id {clause}
             ORDER BY a.created_at DESC
             LIMIT 200
        """),
        {"user_id": user["id"]},
    ).mappings().all()


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = db.execute(
        text("UPDATE alerts SET is_read = 1 "
             "WHERE id = :id AND user_id = :user_id"),
        {"id": alert_id, "user_id": user["id"]},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok"}


@router.post("/notifications/run")
def trigger_notifications(
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run the deadline scan now. Also runs nightly via the cron service
    defined in render.yaml."""
    from app.services.notification_service import run_deadline_notifications

    return run_deadline_notifications(db)


@router.get("/notifications/prefs")
def get_prefs(user: dict = Depends(get_current_user),
              db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM notification_prefs WHERE user_id = :id"),
        {"id": user["id"]},
    ).mappings().first()

    if row:
        return row
    return {
        "user_id": user["id"],
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
    db: Session = Depends(get_db),
):
    lead_days = str(payload.get("lead_days", "30,14,7,3,1"))
    parts = [p.strip() for p in lead_days.split(",") if p.strip()]
    if not parts or not all(p.isdigit() and 0 < int(p) <= 365 for p in parts):
        raise HTTPException(
            status_code=400,
            detail="lead_days must be comma-separated numbers between 1 and 365.",
        )

    db.execute(
        text("""
            INSERT INTO notification_prefs
                (user_id, lead_days, email_enabled, inapp_enabled,
                 digest_mode, categories_filter, updated_at)
            VALUES
                (:user_id, :lead_days, :email, :inapp,
                 :digest, :categories, NOW())
            ON DUPLICATE KEY UPDATE
                lead_days = VALUES(lead_days),
                email_enabled = VALUES(email_enabled),
                inapp_enabled = VALUES(inapp_enabled),
                digest_mode = VALUES(digest_mode),
                categories_filter = VALUES(categories_filter),
                updated_at = NOW()
        """),
        {
            "user_id": user["id"],
            "lead_days": ",".join(parts),
            "email": 1 if payload.get("email_enabled", True) else 0,
            "inapp": 1 if payload.get("inapp_enabled", True) else 0,
            "digest": 1 if payload.get("digest_mode", True) else 0,
            "categories": payload.get("categories_filter"),
        },
    )
    db.commit()
    return {"status": "ok"}
