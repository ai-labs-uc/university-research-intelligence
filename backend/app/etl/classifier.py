"""
Classification: what kind of opportunity is this, and what scope.

Three values come out of here and they are NOT the same thing -- the
previous pipeline conflated them, writing the opportunity type into
`scope_type` as well (`"scope": result`), so scope_type held values like
"CALL_FOR_PAPER_INTERNATIONAL" instead of "INTERNATIONAL".

  opportunity_type  ENUM('GRANT','CALL_FOR_PAPER')   -- narrow, matches schema
  scope_type        'NATIONAL' | 'INTERNATIONAL'
  category          'GRANT_PHILIPPINES' | 'GRANT_INTERNATIONAL'
                    | 'CALL_FOR_PAPER_NATIONAL'
                    | 'CALL_FOR_PAPER_INTERNATIONAL'

`category` is what the API filters on, so it stays the composite value.

Note the previous classifier returned "CALL_FOR_PAPER_INTERNATIONAL" and
"CALL_FOR_PAPER_NATIONAL" directly into the opportunity_type column, which
the schema declares as ENUM('GRANT','CALL_FOR_PAPER'). Under MySQL's
default non-strict mode an out-of-range ENUM silently becomes '' -- so
those writes were either being blanked or erroring depending on the
server's sql_mode.
"""

from __future__ import annotations

import re

from app.etl.filters import has_call_signal
from app.etl.utils import clean_text

TYPE_GRANT = "GRANT"
TYPE_CFP = "CALL_FOR_PAPER"

SCOPE_NATIONAL = "NATIONAL"
SCOPE_INTERNATIONAL = "INTERNATIONAL"


_GRANT_SIGNALS = re.compile(
    r"call\s+for\s+(?:proposals?|applications?)|"
    r"request\s+for\s+(?:proposals?|applications?)|\brfp\b|"
    r"research\s+grant|grants?[- ]in[- ]aid|grants?\s+program|"
    r"funding\s+opportunit|project\s+funding|financial\s+(?:support|assistance)|"
    r"fellowship\s+program|research\s+funding",
    re.I,
)

_CFP_SIGNALS = re.compile(
    r"call\s+for\s+(?:papers?|abstracts?|chapters?|manuscripts?|submissions?)|"
    r"special\s+issue|paper\s+submission|abstract\s+submission|"
    r"topical\s+collection|conference\s+proceedings",
    re.I,
)

_INTERNATIONAL_HINTS = re.compile(
    r"\bscopus\b|web\s+of\s+science|\bwos\b|clarivate|\bieee\b|\bacm\b|"
    r"springer|elsevier|wiley|\bmdpi\b|taylor\s+&?\s*francis|sage\s+publishing|"
    r"international\s+(?:conference|journal|symposium|workshop)|"
    r"horizon\s+europe|\bukri\b|erasmus|\bnsf\b|\bnih\b|world\s+bank|"
    r"european\s+commission|\bjsps\b",
    re.I,
)

_PHILIPPINE_HINTS = re.compile(
    r"philippin|\bdost\b|\bched\b|pcieerd|pchrd|pcaarrd|\bnrcp\b|"
    r"\bda-bar\b|\bdenr\b|\bpssc\b|\bup\s+diliman\b|\bcordillera\b|"
    r"commission\s+on\s+higher\s+education|bureau\s+of\s+agricultural\s+research",
    re.I,
)


def classify(title: str, content: str = "", source: dict | None = None) -> dict | None:
    """Return {opportunity_type, scope_type, category} or None to skip.

    Returning None is the common case and is correct: most pages on an
    agency site are news, not calls. The previous version's willingness to
    classify anything containing the word "research" is what filled the
    table with navigation links.
    """
    source = source or {}
    text = clean_text(f"{title} {content} {source.get('name', '')}")

    # Hard gate: it must actually read like a call.
    if not has_call_signal(title, content):
        return None

    # Grant phrasing wins over CFP phrasing -- "call for proposals" is a
    # grant call, and would otherwise be caught by the looser CFP rules.
    if _GRANT_SIGNALS.search(text):
        opportunity_type = TYPE_GRANT
    elif _CFP_SIGNALS.search(text):
        opportunity_type = TYPE_CFP
    else:
        return None

    scope_type = _detect_scope(text, source)

    if opportunity_type == TYPE_GRANT:
        category = (
            "GRANT_PHILIPPINES" if scope_type == SCOPE_NATIONAL
            else "GRANT_INTERNATIONAL"
        )
    else:
        category = f"CALL_FOR_PAPER_{scope_type}"

    return {
        "opportunity_type": opportunity_type,
        "scope_type": scope_type,
        "category": category,
    }


def _detect_scope(text: str, source: dict) -> str:
    """Source configuration is authoritative; text hints only break ties."""
    configured = source.get("scope")
    if configured in (SCOPE_NATIONAL, SCOPE_INTERNATIONAL):
        return configured

    if _PHILIPPINE_HINTS.search(text):
        return SCOPE_NATIONAL
    if _INTERNATIONAL_HINTS.search(text):
        return SCOPE_INTERNATIONAL
    return SCOPE_NATIONAL


# Backwards compatibility: pipeline_service previously imported
# classify_type() and used the returned string directly.
def classify_type(title, content, source_name=""):
    result = classify(title, content, {"name": source_name})
    return result["category"] if result else None
