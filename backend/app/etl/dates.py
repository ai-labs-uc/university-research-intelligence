"""
Deadline extraction.

This module exists because the ETL previously never wrote a deadline at
all: `research_opportunities.deadline` is defined in the schema, but the
INSERT in pipeline_service.py did not include the column, so every row in
production has deadline = NULL. That makes deadline notifications
structurally impossible -- there is nothing to compare against.

Agency and publisher pages almost never mark deadlines up semantically,
so we extract from text using an ordered set of patterns: the most
explicit phrasing wins, and dates that appear in a "published on" style
context are rejected.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from dateutil import parser as dateparser

from app.etl.utils import clean_text


_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)"
)

_DATE_SHAPES = [
    rf"\d{{1,2}}\s+{_MONTH}\.?\s+\d{{4}}",       # 31 July 2026
    rf"{_MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}",     # July 31, 2026
    r"\d{4}-\d{2}-\d{2}",                        # 2026-07-31
    r"\d{1,2}/\d{1,2}/\d{4}",                    # 31/07/2026
]
_DATE_ALT = "|".join(f"(?:{shape})" for shape in _DATE_SHAPES)


# Ordered by confidence. "Submission deadline" is a far stronger signal
# than a bare "until <date>", so it is tried first.
_DEADLINE_CUES = [
    r"submission\s+deadline",
    r"deadline\s+for\s+(?:the\s+)?submission(?:\s+of\s+[\w\s]{0,40})?",
    r"deadline\s+of\s+submission",
    r"abstract\s+submission\s+deadline",
    r"full\s+paper\s+deadline",
    r"proposal\s+deadline",
    r"application\s+deadline",
    r"closing\s+date",
    r"closes\s+on",
    r"due\s+(?:on|date)",
    r"deadline",
    r"submit(?:ted)?\s+(?:on\s+or\s+before|no\s+later\s+than|"
    r"not\s+later\s+than|until|by)",
    r"on\s+or\s+before",
    r"no\s+later\s+than",
    r"not\s+later\s+than",
]

# Filler between cue and date is kept short so we do not jump a sentence
# boundary and pick up an unrelated date.
_DEADLINE_PATTERNS = [
    re.compile(rf"{cue}\b[^.\n]{{0,40}}?({_DATE_ALT})", re.I)
    for cue in _DEADLINE_CUES
]

# "<date> is the deadline" / "<date> (cut-off)"
_REVERSE_PATTERN = re.compile(
    rf"({_DATE_ALT})[^.\n]{{0,25}}?\b(?:deadline|closing|cut[- ]?off)",
    re.I,
)

# Dates in these contexts are publication or opening dates, not deadlines.
_NEGATIVE_CONTEXT = re.compile(
    r"(?:published|posted|released|updated|accessed|copyright|"
    r"opening\s+date|opened\s+on|start(?:s|ing)?\s+(?:on|date)|"
    r"announced|issued)\s*:?\s*$",
    re.I,
)

_OPENING_CUES = [
    r"opening\s+date",
    r"opens\s+on",
    r"call\s+opens",
    r"start\s+date",
]


def _parse(raw: str) -> date | None:
    try:
        # dayfirst=True: Philippine and UK sources both write 31/07/2026.
        return dateparser.parse(raw, dayfirst=True, fuzzy=True).date()
    except (ValueError, OverflowError, TypeError):
        return None


def extract_deadline(*texts: str | None, not_before: date | None = None) -> date | None:
    """Best-effort submission deadline from one or more blobs of text.

    Returns the highest-confidence match. Dates earlier than ``not_before``
    (default: today) are rejected -- an expired date on a live listing is
    almost always a previous cycle's deadline left on an archive page.
    """
    floor = not_before or datetime.now(timezone.utc).date()

    for blob in texts:
        if not blob:
            continue
        text = clean_text(blob)

        for pattern in _DEADLINE_PATTERNS:
            for match in pattern.finditer(text):
                prefix = text[max(0, match.start() - 30):match.start()]
                if _NEGATIVE_CONTEXT.search(prefix):
                    continue
                parsed = _parse(match.group(1))
                if parsed and parsed >= floor:
                    return parsed

        match = _REVERSE_PATTERN.search(text)
        if match:
            parsed = _parse(match.group(1))
            if parsed and parsed >= floor:
                return parsed

    return None


def extract_opening_date(*texts: str | None) -> date | None:
    """Opening/announcement date, so the UI can show how long a call has
    been open. Unlike deadlines, past dates are valid here."""
    for blob in texts:
        if not blob:
            continue
        text = clean_text(blob)
        for cue in _OPENING_CUES:
            match = re.search(rf"{cue}\b[^.\n]{{0,40}}?({_DATE_ALT})", text, re.I)
            if match:
                parsed = _parse(match.group(1))
                if parsed:
                    return parsed
    return None


def derive_status(deadline: date | None, opening: date | None = None) -> str:
    """Map dates onto the status ENUM ('OPEN','UPCOMING','CLOSED','UNKNOWN')."""
    today = datetime.now(timezone.utc).date()
    if deadline and deadline < today:
        return "CLOSED"
    if opening and opening > today:
        return "UPCOMING"
    if deadline:
        return "OPEN"
    return "UNKNOWN"
