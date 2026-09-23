"""
Junk filtering for discovered pages.

The previous collector kept any same-host link whose anchor text contained
a keyword like "research" or "grant". On a site's homepage that matches the
navigation menu, which is how rows such as "Submission Policies",
"Become an IEEE Conference Author" and "Publish with IEEE Conferences"
ended up stored as research opportunities.

Two gates are applied:
  1. `looks_like_navigation()` rejects menu items and site chrome by title.
  2. `has_call_signal()` requires the page to actually read like a call,
     not merely mention a keyword in passing.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from app.etl.utils import clean_text


_NAV_TITLES = re.compile(
    r"^(?:home|about(?:\s+us)?|contact(?:\s+us)?|sitemap|privacy(?:\s+policy)?|"
    r"terms(?:\s+of\s+use)?|login|log\s?in|sign\s?in|register|search|menu|"
    r"submission\s+policies|author\s+center|publish\s+with\s+[\w\s]+|"
    r"become\s+an?\s+[\w\s]+\s+author|subscribe|newsletter|faq|help|"
    r"advertisement|cookie\s+policy|accessibility|downloads?|gallery|"
    r"transparency\s+seal|citizens?\s+charter|organizational\s+chart|"
    r"bids\s+and\s+awards|job\s+(?:vacanc|opening)\w*)\s*$",
    re.I,
)

_BOILERPLATE = re.compile(
    r"skip\s+to\s+main\s+content|enable\s+javascript|this\s+site\s+uses\s+cookies|"
    r"your\s+browser\s+is\s+(?:out\s+of\s+date|not\s+supported)|"
    r"toggle\s+navigation|breadcrumb|back\s+to\s+top",
    re.I,
)

# A genuine call almost always contains one of these phrases.
_CALL_SIGNAL = re.compile(
    r"call\s+for\s+(?:papers?|proposals?|abstracts?|applications?|submissions?|"
    r"chapters?|manuscripts?|expressions?\s+of\s+interest)|"
    r"special\s+issue|research\s+grant|funding\s+opportunit|"
    r"invites?\s+(?:submissions?|proposals?|applications?)|"
    r"request\s+for\s+(?:proposals?|applications?)|\brfp\b|"
    r"grants?[- ]in[- ]aid|grants?\s+program|fellowship\s+program|"
    r"now\s+accepting\s+(?:submissions?|proposals?|applications?)",
    re.I,
)

# Literal index names, only ever read off the page -- never inferred.
_INDEXING_PATTERNS = {
    "SCOPUS": re.compile(r"\bscopus\b", re.I),
    "WEB_OF_SCIENCE": re.compile(
        r"web\s+of\s+science|\bwos\b|clarivate|"
        r"(?:science|social\s+sciences)\s+citation\s+index|\bscie?\b",
        re.I,
    ),
    "ACI": re.compile(r"asean\s+citation\s+index|\baci\b", re.I),
    "DOAJ": re.compile(r"\bdoaj\b|directory\s+of\s+open\s+access", re.I),
    "PUBMED": re.compile(r"\bpubmed\b|\bmedline\b", re.I),
}


def looks_like_navigation(title: str) -> bool:
    """True for menu items and site chrome that must never be stored."""
    value = clean_text(title)
    if len(value) < 12 or len(value.split()) < 3:
        return True
    return bool(_NAV_TITLES.match(value))


def has_call_signal(*texts: str | None) -> bool:
    """True if any text actually reads like a call for papers/proposals."""
    return any(_CALL_SIGNAL.search(t) for t in texts if t)


def strip_boilerplate(text: str | None, limit: int = 3000) -> str:
    """Clean a page body into a usable summary: drop scripts, nav and
    cookie banners, collapse whitespace, truncate."""
    if not text:
        return ""
    if "<" in text:
        soup = BeautifulSoup(text, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
            tag.decompose()
        text = soup.get_text("\n")
    lines = [ln.strip() for ln in re.split(r"[\n\r]+", text) if ln.strip()]
    lines = [ln for ln in lines if not _BOILERPLATE.search(ln)]
    return clean_text(" ".join(lines))[:limit]


def detect_indexing(*texts: str | None) -> list[str]:
    """Indexing labels literally stated on the page.

    An empty list means the page did not state an index -- NOT that the
    venue is unindexed. Never infer indexing status from reputation.
    """
    blob = " ".join(t for t in texts if t)
    if not blob:
        return []
    return [name for name, pattern in _INDEXING_PATTERNS.items()
            if pattern.search(blob)]
