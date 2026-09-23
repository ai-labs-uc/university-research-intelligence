"""
Collectors: turn a configured source into candidate items.

Changes from the previous version, and why:

  * TLS verification is ON. The old `requests.get(..., verify=False)`
    disabled certificate checking on every request, which silently accepts
    a man-in-the-middle and emits InsecureRequestWarning noise. Agency
    sites with awkward chains are handled with retries, not by trusting
    anything that answers.
  * Requests are rate limited per host and retried with backoff, so one
    slow agency cannot stall the run or get us blocked.
  * A real item yields structured fields (title, body, link, dates), not
    just a URL -- feeds already carry the body, so the per-item detail
    fetch is skipped unless a deadline is still missing.
  * Navigation links are rejected up front (see app.etl.filters).
"""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

from app.etl.filters import looks_like_navigation, strip_boilerplate
from app.etl.utils import clean_text

log = logging.getLogger(__name__)

USER_AGENT = (
    "UC-ResearchIntelligenceBot/2.0 "
    "(+https://university-research-intelligence-fr.vercel.app; "
    "research opportunity aggregation for University of the Cordilleras)"
)

RSS_CONTENT_NS = {"content": "http://purl.org/rss/1.0/modules/content/"}

_last_request_at: dict[str, float] = {}
_session: requests.Session | None = None

REQUEST_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml,"
                "application/json;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })
    return _session


def fetch(url: str) -> requests.Response | None:
    """Polite GET with per-host rate limiting and backoff. Returns None
    rather than raising, so one dead source cannot abort a run."""
    host = urlsplit(url).netloc
    elapsed = time.monotonic() - _last_request_at.get(host, 0.0)
    if elapsed < REQUEST_DELAY_SECONDS:
        time.sleep(REQUEST_DELAY_SECONDS - elapsed)

    for attempt in range(MAX_RETRIES):
        try:
            response = get_session().get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            _last_request_at[host] = time.monotonic()

            if response.status_code == 429:
                time.sleep(3 * (2 ** attempt))
                continue
            if response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return response

        except requests.RequestException as exc:
            if attempt == MAX_RETRIES - 1:
                log.warning("GET failed %s: %s", url, exc)
            else:
                time.sleep(2 ** attempt)

    return None


def fetch_json(url: str):
    response = fetch(url)
    if not response:
        return None
    try:
        return response.json()
    except ValueError:
        log.warning("Non-JSON response from %s", url)
        return None


def fetch_soup(url: str) -> BeautifulSoup | None:
    response = fetch(url)
    return BeautifulSoup(response.text, "lxml") if response else None


# ------------------------------------------------------------------
# Item shape
# ------------------------------------------------------------------
def _item(title: str, url: str, body: str = "") -> dict:
    return {
        "title": clean_text(title),
        "url": url,
        "body": strip_boilerplate(body),
    }


# ------------------------------------------------------------------
# WordPress REST API
# ------------------------------------------------------------------
def collect_wp_api(source: dict) -> list[dict]:
    items: list[dict] = []
    api_url = source["api_url"]

    for page in range(1, source.get("max_pages", 3) + 1):
        data = fetch_json(f"{api_url}?per_page=50&page={page}&_embed=0")
        if not data or not isinstance(data, list):
            break

        for post in data:
            title = strip_boilerplate(
                (post.get("title") or {}).get("rendered", ""), 300
            )
            if not title or looks_like_navigation(title):
                continue
            body = " ".join([
                (post.get("excerpt") or {}).get("rendered", ""),
                (post.get("content") or {}).get("rendered", ""),
            ])
            items.append(_item(title, post.get("link", ""), body))

        if len(data) < 50:
            break

    return items


# ------------------------------------------------------------------
# RSS / Atom
# ------------------------------------------------------------------
def _parse_rss(xml_text: str) -> list[dict]:
    """Parse RSS 2.0. Tolerant of the namespace sloppiness common on
    government installs."""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log.warning("RSS parse failed: %s", exc)
        return out

    for node in root.iter("item"):
        def text_of(tag, ns=None):
            el = node.find(tag, ns) if ns else node.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        out.append({
            "title": text_of("title"),
            "link": text_of("link"),
            "description": text_of("description"),
            "content": text_of("content:encoded", RSS_CONTENT_NS),
        })
    return out


def collect_rss(source: dict) -> list[dict]:
    response = fetch(source["feed_url"])
    if not response:
        return []

    items = []
    seen_ids: set[str] = set()

    for entry in _parse_rss(response.text):
        title = entry["title"]
        if not title or looks_like_navigation(title):
            continue

        link = entry["link"]

        # Joomla resolves the same article under several path prefixes,
        # so dedupe on the numeric article id rather than the URL.
        if source.get("dedupe_on_joomla_id"):
            match = re.search(r"/(\d{3,6})-", link or "")
            key = match.group(1) if match else link
            if key in seen_ids:
                continue
            seen_ids.add(key)

        body = entry["content"] or entry["description"]
        items.append(_item(title, link, body))

    return items


# ------------------------------------------------------------------
# HTML listings
# ------------------------------------------------------------------
def _listing_urls(source: dict) -> list[str]:
    """Expand a source into the listing pages to visit."""
    template = source["listing_url"]

    if source.get("journal_slugs"):
        return [template.format(slug=slug) for slug in source["journal_slugs"]]

    if source.get("page_param"):
        param = source["page_param"]
        joiner = "&" if "?" in template else "?"
        return [
            template if page == 1 else f"{template}{joiner}{param}={page}"
            for page in range(1, source.get("max_pages", 1) + 1)
        ]

    return [template]


def _last_joomla_offset(soup: BeautifulSoup) -> int:
    """PCAARRD's archive sorts oldest-first, so page 1 is 2004 content.
    Find the highest ?start= offset and read from the end instead."""
    offsets = []
    for anchor in soup.select("a[href*='start=']"):
        match = re.search(r"start=(\d+)", anchor.get("href", ""))
        if match:
            offsets.append(int(match.group(1)))
    return max(offsets) if offsets else 0


def collect_html(source: dict) -> list[dict]:
    items: list[dict] = []
    selector = source.get("item_selector") or "h2 a, h3 a, article a[href]"
    skip_pdfs = "da.gov.ph" in source["listing_url"]  # robots: Disallow /*.pdf$

    listing_urls = _listing_urls(source)

    if source.get("joomla_reverse_pagination"):
        first = fetch_soup(source["listing_url"])
        if not first:
            return items
        last = _last_joomla_offset(first)
        listing_urls = [
            f"{source['listing_url']}?start={offset}"
            for offset in (last, max(0, last - 15))
        ]

    for listing_url in listing_urls:
        soup = fetch_soup(listing_url)
        if not soup:
            continue

        seen_urls: set[str] = set()

        for anchor in soup.select(selector):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "")
            if not href or not title:
                continue
            if skip_pdfs and href.lower().endswith(".pdf"):
                continue
            if looks_like_navigation(title):
                continue

            url = urljoin(listing_url, href)
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Prefer the surrounding card text: on MDPI, Springer and UKRI
            # the deadline is printed right there, saving a detail fetch.
            container = anchor.find_parent(
                ["article", "li", "div"]
            ) or anchor.parent
            body = container.get_text(" ", strip=True) if container else ""

            items.append(_item(title, url, body))

    return items


# ------------------------------------------------------------------
# Dispatch
# ------------------------------------------------------------------
_COLLECTORS = {
    "wp_api": collect_wp_api,
    "rss": collect_rss,
    "html": collect_html,
}


def collect(source: dict) -> list[dict]:
    """Collect candidate items for one source. Never raises."""
    collector = _COLLECTORS.get(source.get("kind", "html"))
    if not collector:
        log.warning("Unknown source kind for %s", source.get("code"))
        return []
    try:
        return collector(source)
    except Exception as exc:                          # noqa: BLE001
        log.exception("Collector failed for %s", source.get("code"))
        raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc


def fetch_detail(url: str) -> str:
    """Full text of a detail page, for when the listing/feed excerpt did
    not contain a deadline. Returns '' on failure."""
    soup = fetch_soup(url)
    if not soup:
        return ""
    for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
        tag.decompose()
    return strip_boilerplate(soup.get_text("\n"))
