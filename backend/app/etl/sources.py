"""
Configured opportunity sources.

Rewritten around structured feeds rather than homepage link-scraping.
The previous configuration pointed most sources at the agency HOMEPAGE
with keywords like "research" and "grant", which matched the navigation
menu -- that is why site chrome was being stored as opportunities.

Each source declares a `kind` that tells the collector how to read it:

    "wp_api"  WordPress REST API  -> JSON, no HTML parsing at all
    "rss"     RSS/Atom feed       -> structured items
    "html"    HTML listing page   -> CSS selector for item links

Verified 22 Sep 2026. Notes on what is deliberately absent:

  * ScienceDirect / Elsevier -- robots.txt is a blanket `Disallow: /` and
    explicitly names automated agents. Not scraped. No official CFP API
    exists; these calls must be reviewed manually.
  * link.springer.com/search -- Disallowed by robots.txt. Per-journal
    /collections pages are allowed and are what we use.
  * IEEE conference search -- returns HTTP 418 to automated clients.
    Removed: `conferences.ieeeauthorcenter.ieee.org` was the source of the
    "Become an IEEE Conference Author" rows.
  * WikiCFP -- robots.txt could not be retrieved during verification. A
    well-behaved crawler treats unreachable robots.txt as full disallow,
    so it is disabled pending an independent check. It is also
    user-submitted and un-vetted, mixing indexed and predatory venues.
  * CHED / DOST-SEI -- both behind a WAF or JS-rendered; a plain HTTP
    client gets 403 or an empty shell. Covered via university research
    office mirrors, which republish the same calls.
"""

from __future__ import annotations


# ============================================================
# PHILIPPINE GRANTS / FUNDING
# ============================================================

PH_GRANT_SOURCES = [
    {
        # The one PH agency exposing an open WordPress REST API.
        # content.rendered carries the full post body, so deadlines can be
        # extracted without a second request per item.
        "code": "PCIEERD",
        "name": "DOST-PCIEERD",
        "kind": "wp_api",
        "listing_url": "https://pcieerd.dost.gov.ph/work-with-us/",
        "api_url": "https://pcieerd.dost.gov.ph/wp-json/wp/v2/posts",
        "max_pages": 3,
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        # /wp-json is 401 here; the feed works and also avoids the
        # Elementor AJAX pagination on the HTML listing.
        "code": "NRCP",
        "name": "National Research Council of the Philippines",
        "kind": "rss",
        "listing_url": "https://nrcp.dost.gov.ph/news-and-updates/",
        "feed_url": "https://nrcp.dost.gov.ph/feed/",
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        # Joomla feed. Carries the bilateral programmes (DOST-JSPS,
        # MECO-TECO, JST) that never appear on the council sites.
        "code": "DOST",
        "name": "Department of Science and Technology",
        "kind": "rss",
        "listing_url": "https://www.dost.gov.ph/23-announcements/",
        "feed_url": "https://www.dost.gov.ph/23-announcements/?format=feed&type=rss",
        "dedupe_on_joomla_id": True,
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        # Joomla, no feed. Listing sorts OLDEST FIRST -- the collector
        # jumps to the last pagination offset for recent items.
        "code": "PCAARRD",
        "name": "DOST-PCAARRD",
        "kind": "html",
        "listing_url": "https://www.pcaarrd.dost.gov.ph/index.php/news-archive",
        "item_selector": "h2 a, h3 a, .item-title a",
        "joomla_reverse_pagination": True,
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        "code": "PCHRD",
        "name": "DOST-PCHRD",
        "kind": "html",
        "listing_url": "https://www.pchrd.dost.gov.ph/calls_and_events/",
        "item_selector": ".entry-title a, h2 a, h3 a, article a[href]",
        "scope": "NATIONAL",
        "country": "Philippines",
        # Newest item observed was April 2024. Kept enabled so a revival
        # is picked up automatically, but do not expect yield.
        "expect_low_yield": True,
    },
    {
        # Detail pages are keyed ?id=N; listing paginates ?pageno=N.
        # Intermittent WAF -- the session retries with backoff.
        "code": "DABAR",
        "name": "DA-Bureau of Agricultural Research",
        "kind": "html",
        "listing_url": "https://www.bar.gov.ph/media-resources/news-and-events",
        "item_selector": "a[href*='details?id=']",
        "page_param": "pageno",
        "max_pages": 3,
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        # robots.txt disallows /*.pdf$ -- the collector never follows PDFs
        # on this host.
        "code": "DA",
        "name": "Department of Agriculture",
        "kind": "html",
        "listing_url": "https://www.da.gov.ph/news/",
        "item_selector": "h2 a, h3 a, article a[href]",
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        "code": "DENR",
        "name": "Department of Environment and Natural Resources",
        "kind": "rss",
        "listing_url": "https://denr.gov.ph/news-events/",
        "feed_url": "https://denr.gov.ph/feed/",
        "scope": "NATIONAL",
        "country": "Philippines",
        "expect_low_yield": True,
    },
    {
        # ched.gov.ph 403s every automated request. University research
        # offices republish CHED calls reliably, so we read them there.
        "code": "CHED",
        "name": "Commission on Higher Education",
        "kind": "html",
        "listing_url": "https://ovcre.uplb.edu.ph/announcements/",
        "item_selector": ".entry-title a, h2 a, h3 a",
        "scope": "NATIONAL",
        "country": "Philippines",
        "mirrored": True,
    },
]


# ============================================================
# PHILIPPINE CALLS FOR PAPERS
# ============================================================

PH_CFP_SOURCES = [
    {
        "code": "UPCIDS",
        "name": "UP Center for Integrative and Development Studies",
        "kind": "rss",
        "listing_url": "https://cids.up.edu.ph/",
        "feed_url": "https://cids.up.edu.ph/feed/",
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        "code": "UPMAIN",
        "name": "University of the Philippines",
        "kind": "rss",
        "listing_url": "https://up.edu.ph/",
        "feed_url": "https://up.edu.ph/feed/",
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        # PSSC's /feed/ is 403 at the edge; the HTML listing works.
        "code": "PSSC",
        "name": "Philippine Social Science Council",
        "kind": "html",
        "listing_url": "https://pssc.org.ph/latest-news-and-events/3/",
        "item_selector": "h3 a, h2 a",
        "scope": "NATIONAL",
        "country": "Philippines",
    },
    {
        # Most CHED-recognised PH journals run Open Journal Systems, and
        # every OJS 3 install exposes /announcement with identical markup.
        # Add journal bases here as they are identified; OpenAlex can seed
        # the list via /sources?filter=country_code:PH,is_ojs:true
        "code": "OJS_PH",
        "name": "Philippine OJS Journals",
        "kind": "html",
        "listing_url": "https://phjlis.org/index.php/phjlis/announcement",
        "item_selector": ".obj_announcement_summary h2 a, "
                         ".obj_announcement_summary h3 a",
        "scope": "NATIONAL",
        "country": "Philippines",
    },
]


# ============================================================
# INTERNATIONAL CALLS FOR PAPERS
# ============================================================

INTERNATIONAL_CFP_SOURCES = [
    {
        # Largest robots-permitted, server-rendered CFP corpus with
        # machine-readable deadlines ("submission deadline 31 Jul 2026").
        # robots.txt allows the listing; only /special_issues/*/download
        # is disallowed and we never request it.
        "code": "MDPI",
        "name": "MDPI Special Issues",
        "kind": "html",
        "listing_url": "https://www.mdpi.com/journal/{slug}/special_issues?page_count=50",
        "item_selector": "a[href*='/special_issues/']",
        "journal_slugs": [
            "sustainability", "applsci", "education-sciences", "ijerph",
            "agriculture", "water", "energies", "sensors", "information",
            "electronics", "mathematics", "foods", "land", "buildings",
        ],
        "scope": "INTERNATIONAL",
        "require_deadline": True,
    },
    {
        # /search is robots-disallowed; per-journal /collections is allowed.
        "code": "SPRINGER",
        "name": "Springer Nature Collections",
        "kind": "html",
        "listing_url": "https://link.springer.com/journal/{slug}/collections",
        "item_selector": "h2 a",
        "journal_slugs": ["11229", "10639", "10661", "11423", "13748"],
        "scope": "INTERNATIONAL",
        "require_deadline": True,
    },
]


# ============================================================
# INTERNATIONAL GRANTS
# ============================================================

INTERNATIONAL_GRANT_SOURCES = [
    {
        # Rare and valuable: closing dates appear on the listing page, so
        # no per-item detail fetch is needed.
        "code": "UKRI",
        "name": "UK Research and Innovation",
        "kind": "html",
        "listing_url": "https://www.ukri.org/opportunity/?filter_order=closing_date",
        "item_selector": "a[href*='/opportunity/']",
        "scope": "INTERNATIONAL",
        "currency": "GBP",
    },
]


# ============================================================
# DISABLED -- do not enable without re-verification
# ============================================================

DISABLED_SOURCES = [
    {
        "code": "WIKICFP",
        "name": "WikiCFP",
        "kind": "rss",
        "listing_url": "http://www.wikicfp.com/cfp/",
        "feed_url": "http://www.wikicfp.com/cfp/rss",
        "scope": "INTERNATIONAL",
        "enabled": False,
        "disabled_reason": (
            "robots.txt unreachable during verification; a crawler must "
            "treat that as disallow. Also user-submitted and un-vetted."
        ),
    },
    {
        "code": "IEEE_AUTHOR_CENTER",
        "name": "IEEE Author Center",
        "kind": "html",
        "listing_url": "https://conferences.ieeeauthorcenter.ieee.org/",
        "scope": "INTERNATIONAL",
        "enabled": False,
        "disabled_reason": (
            "Author-guidance site, not a CFP listing. Produced the "
            "'Become an IEEE Conference Author' / 'Submission Policies' "
            "rows. IEEE conference search returns HTTP 418 to bots."
        ),
    },
]


ALL_SOURCES = (
    PH_GRANT_SOURCES
    + PH_CFP_SOURCES
    + INTERNATIONAL_CFP_SOURCES
    + INTERNATIONAL_GRANT_SOURCES
)


def enabled_default_sources():
    """Return every enabled source. Kept as a function because
    pipeline_service.py imports it directly."""
    return [s for s in ALL_SOURCES if s.get("enabled", True)]
