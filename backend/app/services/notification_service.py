"""
Deadline notifications.

This is the feature that could never have worked before: every row had
deadline = NULL, so no comparison against "today" could ever match. With
deadlines now populated by the ETL, this module turns them into alerts.

Design:
* Lead times are per-user and configurable; defaults are 30/14/7/3/1 days.
* Sends are idempotent. A (user, opportunity, lead_days) triple is
  recorded, so running the job twice in a day cannot double-notify.
* Fires the TIGHTEST threshold an item has crossed, so a call first
  scraped 5 days before its deadline still alerts (at the 7-day rule)
  rather than being skipped because the 30/14 marks already passed.
* Email delivery is optional. With SMTP_HOST unset, in-app alerts are
  still created and email is logged instead of sent -- safe for local
  development and for deployments without mail configured.

Storage note: the original query built its candidate set with a SQL
CROSS JOIN between opportunities and users (plus a LEFT JOIN for
per-user preferences), which has no single-call Mongo equivalent.
`_find_pending` below fetches the (small, bounded) set of upcoming
opportunities and active users separately and does the same matching
in Python -- same result, same idempotency guarantees.
"""

from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass
from datetime import date, timedelta
from email.message import EmailMessage

from pymongo.errors import DuplicateKeyError

from app.core.database import next_id, utcnow

log = logging.getLogger(__name__)

DEFAULT_LEAD_DAYS = [30, 14, 7, 3, 1]
MAX_LOOKAHEAD_DAYS = 30

APP_URL = os.getenv(
    "FRONTEND_URL",
    "https://university-research-intelligence-fr.vercel.app",
)


@dataclass
class Alert:
    user_id: int
    email: str
    name: str
    opportunity_id: int
    title: str
    organization: str
    deadline: date
    days_left: int
    lead_days: int
    source_url: str
    category: str


def run_deadline_notifications(db, digest: bool = True) -> dict:
    alerts = _find_pending(db)
    if not alerts:
        return {"pending": 0, "sent": 0, "users": 0}

    by_user: dict[int, list[Alert]] = {}
    for alert in alerts:
        by_user.setdefault(alert.user_id, []).append(alert)

    sent = 0
    mailer = SMTPMailer()

    for user_id, user_alerts in by_user.items():
        user_alerts.sort(key=lambda a: a.days_left)
        try:
            _create_in_app(db, user_alerts)
            if digest:
                mailer.send(
                    user_alerts[0].email,
                    _digest_subject(user_alerts),
                    _digest_body(user_alerts),
                )
            else:
                for alert in user_alerts:
                    mailer.send(
                        alert.email, _single_subject(alert), _digest_body([alert])
                    )
            _record_sent(db, user_alerts)
            sent += len(user_alerts)
        except Exception:  # noqa: BLE001
            log.exception("Notification failed for user %s", user_id)

    return {"pending": len(alerts), "sent": sent, "users": len(by_user)}


def _find_pending(db) -> list[Alert]:
    now = utcnow()
    lookahead_cutoff = now + timedelta(days=MAX_LOOKAHEAD_DAYS)

    opportunities = list(db.research_opportunities.find({
        "deadline": {"$ne": None, "$gte": now, "$lte": lookahead_cutoff},
        "is_current": True,
    }))
    if not opportunities:
        return []

    users = list(db.users.find({"active": True}))
    if not users:
        return []

    prefs_by_user = {
        p["_id"]: p
        for p in db.notification_prefs.find({"_id": {"$in": [u["_id"] for u in users]}})
    }

    already_sent = {
        (r["user_id"], r["opportunity_id"], r["lead_days"])
        for r in db.notification_log.find({}, {"user_id": 1, "opportunity_id": 1, "lead_days": 1})
    }

    default_leads_csv = ",".join(str(d) for d in DEFAULT_LEAD_DAYS)
    today = now.date()

    alerts: list[Alert] = []
    for opp in opportunities:
        deadline_dt = opp["deadline"]
        deadline_date = deadline_dt.date() if hasattr(deadline_dt, "date") else deadline_dt
        days_left = (deadline_date - today).days

        for user in users:
            prefs = prefs_by_user.get(user["_id"])

            email_enabled = prefs.get("email_enabled", 1) if prefs else 1
            if not email_enabled:
                continue

            categories_filter = prefs.get("categories_filter") if prefs else None
            if categories_filter:
                allowed = [c.strip() for c in categories_filter.split(",")]
                if (opp.get("category") or "") not in allowed:
                    continue

            lead_days_csv = prefs.get("lead_days", default_leads_csv) if prefs else default_leads_csv
            leads = sorted(
                (int(x) for x in str(lead_days_csv).split(",") if x.strip().isdigit()),
                reverse=True,
            )
            matched = next((lead for lead in leads if days_left <= lead), None)
            if matched is None:
                continue
            if (user["_id"], opp["_id"], matched) in already_sent:
                continue

            alerts.append(Alert(
                user_id=user["_id"],
                email=user["email"],
                name=user.get("name") or "",
                opportunity_id=opp["_id"],
                title=opp["title"],
                organization=opp.get("organization") or "",
                deadline=deadline_date,
                days_left=days_left,
                lead_days=matched,
                source_url=opp.get("source_url") or "",
                category=opp.get("category") or "",
            ))

    return alerts


def _create_in_app(db, alerts: list[Alert]) -> None:
    now = utcnow()
    for alert in alerts:
        message = f"Deadline in {alert.days_left} day(s) \u2014 {alert.deadline:%d %b %Y}"
        db.alerts.update_one(
            {
                "user_id": alert.user_id,
                "opportunity_id": alert.opportunity_id,
                "alert_type": "DEADLINE_SOON",
                "lead_days": alert.lead_days,
            },
            {
                "$set": {"message": message, "created_at": now},
                "$setOnInsert": {"_id": next_id("alerts"), "is_read": False},
            },
            upsert=True,
        )


def _record_sent(db, alerts: list[Alert]) -> None:
    now = utcnow()
    for alert in alerts:
        try:
            db.notification_log.insert_one({
                "_id": next_id("notification_log"),
                "user_id": alert.user_id,
                "opportunity_id": alert.opportunity_id,
                "lead_days": alert.lead_days,
                "channel": "email",
                "sent_at": now,
            })
        except DuplicateKeyError:
            pass  # Already recorded -- mirrors MySQL's INSERT IGNORE.


# ------------------------------------------------------------------
# Email rendering
# ------------------------------------------------------------------
def _single_subject(alert: Alert) -> str:
    urgency = ("closing tomorrow" if alert.days_left <= 1
               else f"{alert.days_left} days left")
    return f"[{urgency}] {alert.title[:80]}"


def _digest_subject(alerts: list[Alert]) -> str:
    soonest = alerts[0]
    if soonest.days_left <= 1:
        extra = f" (+{len(alerts) - 1} more)" if len(alerts) > 1 else ""
        return f"Closing tomorrow: {soonest.title[:60]}{extra}"
    return (f"{len(alerts)} research deadline(s) approaching \u2014 "
            f"soonest in {soonest.days_left} days")


def _digest_body(alerts: list[Alert]) -> str:
    rows = []
    for alert in alerts:
        urgent = alert.days_left <= 3
        urgency = ("TOMORROW" if alert.days_left <= 1
                   else f"{alert.days_left} days left")
        kind = (alert.category or "").replace("_", " ").title()
        rows.append(f"""
        <tr>
            <td style="padding:12px 8px;border-bottom:1px solid #e5e7eb">
                <div style="font-weight:600;color:#09593c">{alert.title}</div>
                <div style="color:#6b7280;font-size:13px">
                    {alert.organization} &middot; {kind}</div>
            </td>
            <td style="padding:12px 8px;border-bottom:1px solid #e5e7eb;
                white-space:nowrap;text-align:right">
                <div style="font-weight:600">{alert.deadline:%d %b %Y}</div>
                <div style="font-size:13px;color:{'#dc2626' if urgent else '#6b7280'}">
                    {urgency}</div>
            </td>
            <td style="padding:12px 8px;border-bottom:1px solid #e5e7eb">
                <a href="{alert.source_url}" style="color:#09593c">View</a></td>
        </tr>""")

    plural = "y" if len(alerts) == 1 else "ies"
    return f"""<!doctype html><html><body
    style="font-family:system-ui,-apple-system,sans-serif;background:#f9fafb;padding:24px">
    <div style="max-width:640px;margin:auto;background:#fff;border-radius:12px;padding:24px">
        <h2 style="color:#09593c;margin:0 0 4px">Upcoming research deadlines</h2>
        <p style="color:#6b7280;margin:0 0 20px">
            {len(alerts)} opportunit{plural} approaching the submission deadline.</p>
        <table style="width:100%;border-collapse:collapse">{''.join(rows)}</table>
        <p style="margin-top:24px">
            <a href="{APP_URL}/opportunities"
               style="background:#09593c;color:#fff;padding:10px 18px;
               border-radius:8px;text-decoration:none;display:inline-block">
                Open dashboard</a></p>
        <p style="color:#9ca3af;font-size:12px;margin-top:20px">
            University of the Cordilleras \u00b7 Research Intelligence.
            Alert timing can be changed in your notification settings.</p>
    </div></body></html>"""


class SMTPMailer:
    """Env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM.

    With SMTP_HOST unset, messages are logged rather than sent. That keeps
    local runs from mailing real users by accident, and lets the job be
    deployed before mail credentials exist.
    """

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")
        self.sender = os.getenv("SMTP_FROM") or self.user or "noreply@uc-bcf.edu.ph"

    def send(self, to: str, subject: str, html: str) -> None:
        if not self.host:
            log.info("[email suppressed: SMTP_HOST unset] to=%s subject=%s",
                      to, subject)
            return
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = to
        message.set_content(
            "Open this message in an HTML-capable client to see your deadlines."
        )
        message.add_alternative(html, subtype="html")

        with smtplib.SMTP(self.host, self.port, timeout=30) as server:
            server.starttls()
            if self.user:
                server.login(self.user, self.password)
            server.send_message(message)
