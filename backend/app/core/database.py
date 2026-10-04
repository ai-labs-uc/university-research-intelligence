from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient, ReturnDocument

from app.core.config import settings

client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_db_name]


def utcnow() -> datetime:
    """Current time as a naive UTC datetime.

    PyMongo decodes BSON dates back out as naive datetimes by default
    (interpreted as UTC), so a value built with ``datetime.now(timezone.utc)``
    stops being comparable to it after a single round trip through the
    database -- Python refuses to compare an aware and a naive datetime.
    Every datetime this app stores in, or compares against, MongoDB
    should be built with this helper instead, so nothing anywhere ends
    up mixing aware and naive values.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class _DBHandle:
    """Thin wrapper so call sites written for the old per-request SQL
    session (``SessionLocal()`` ... ``.close()``) keep working unchanged.
    PyMongo's client is already connection-pooled and thread-safe, so
    there is nothing to open or close per request — ``close()`` is a
    no-op and every attribute access is forwarded straight to the
    underlying Mongo database handle.
    """

    def __init__(self, database):
        self._database = database

    def __getattr__(self, name):
        return getattr(self._database, name)

    def close(self) -> None:
        pass


def SessionLocal() -> _DBHandle:
    return _DBHandle(db)


def get_db():
    yield SessionLocal()


def next_id(sequence_name: str) -> int:
    """Atomically allocate the next integer id for a logical sequence
    (one counter document per collection), so documents keep the same
    small integer ids the rest of the app, the frontend, and JWT
    ``sub`` claims already expect instead of switching to ObjectId.
    """
    doc = db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]


def ensure_indexes() -> None:
    """Create every unique/lookup index the app relies on. Safe to call
    repeatedly (index creation is a no-op once an identical index
    exists) — called explicitly from the API's startup hook and from
    the ETL entry point, rather than at import time, so importing this
    module never requires a live database connection.
    """
    db.users.create_index("email", unique=True)
    db.users.create_index("google_sub", unique=True, sparse=True)

    # Unused by any current route, kept for schema parity with the
    # original MySQL tables in case researcher-level features return.
    db.researchers.create_index("email", unique=True)
    db.researchers.create_index("employee_no", unique=True, sparse=True)

    db.opportunity_sources.create_index("code", unique=True)

    db.research_opportunities.create_index("content_hash", unique=True, sparse=True)
    db.research_opportunities.create_index([("deadline", ASCENDING), ("is_current", ASCENDING)])
    db.research_opportunities.create_index([("category", ASCENDING), ("is_current", ASCENDING)])

    db.notification_log.create_index(
        [
            ("user_id", ASCENDING),
            ("opportunity_id", ASCENDING),
            ("lead_days", ASCENDING),
            ("channel", ASCENDING),
        ],
        unique=True,
    )
    db.notification_log.create_index([("user_id", ASCENDING), ("sent_at", ASCENDING)])

    db.alerts.create_index(
        [
            ("user_id", ASCENDING),
            ("opportunity_id", ASCENDING),
            ("alert_type", ASCENDING),
            ("lead_days", ASCENDING),
        ],
        unique=True,
    )
    db.alerts.create_index([("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", ASCENDING)])
