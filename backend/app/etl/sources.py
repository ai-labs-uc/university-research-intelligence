"""
Configured opportunity sources.

Every source here must be:
  1. A public page that does not require logging in.
  2. Fetchable with a plain HTTP GET (no JavaScript rendering needed) —
     this ETL is `requests` + BeautifulSoup, not a browser.
  3. Something the publisher is fine with being read by a script. We
     only point this at official agency/aggregator sites, never at
     social media search results — platforms like Facebook require an
     authenticated session and explicitly prohibit automated scraping
     in their Terms of Service, so they can't be added here no matter
     how useful the content looks. If your office needs something
     that's only posted on social media, the sustainable fix is asking
     the poster to also list it on one of the sites below (or on
     startup.gov.ph / WikiCFP, which exist precisely so it doesn't only
     live on social media).

`keywords` filters which same-host links on the listing page get
followed, by matching against the link's visible text (not the page
content). Leave it as `[]` for a page that is already 100% about one
topic (e.g. a CFP aggregator's category page) — that takes every
same-host link instead of filtering.
"""

SOURCES = [
    # ---- research grants & calls for proposals -----------------------
    {
        "code": "PCIEERD",
        "name": "DOST-PCIEERD",
        "listing_url": "https://pcieerd.dost.gov.ph/work-with-us/",
        "keywords": ["grant", "call for proposal", "funding"],
    },
    {
        "code": "PCHRD",
        "name": "DOST-PCHRD",
        "listing_url": "https://www.pchrd.dost.gov.ph/calls_and_events/",
        "keywords": ["grant", "call for proposal", "research"],
    },
    {
        "code": "PCAARRD",
        "name": "DOST-PCAARRD",
        "listing_url": (
            "https://www.pcaarrd.dost.gov.ph/index.php/"
            "quick-information-dispatch-qid-articles"
        ),
        "keywords": [
            "call for proposal", "grant", "call for",
            "startup grant fund", "request for submission",
        ],
    },
    {
        "code": "NRCP",
        "name": "National Research Council of the Philippines",
        "listing_url": "https://nrcp.dost.gov.ph/",
        "keywords": ["call for proposal", "grants-in-aid", "call for"],
    },
    {
        "code": "CHED",
        "name": "Commission on Higher Education",
        "listing_url": "https://legacy.ched.gov.ph/issuances/",
        "keywords": ["scholarship", "grant", "call for", "memorandum order"],
    },
    {
        "code": "SEI",
        "name": "DOST Science Education Institute",
        "listing_url": "https://www.sei.dost.gov.ph/",
        "keywords": ["scholarship", "application", "call for"],
    },

    # ---- startup challenges, spin-offs & tech transfer -----------------
    {
        "code": "STARTUPGOVPH",
        "name": "Startup Innovations Portal (DICT / Innovative Startup Act)",
        "listing_url": "https://startup.gov.ph/",
        "keywords": [
            "grant fund", "startup grant", "call for",
            "open call", "apply", "challenge",
        ],
    },
    {
        "code": "TAPI",
        "name": "DOST-TAPI Technology Transfer",
        "listing_url": "https://tapitechtransfer.dost.gov.ph/news-archive",
        # TAPI runs the government's research commercialization pipeline
        # — invention → spin-off company → licensed technology — so its
        # news archive is the place calls for spin-off/investment-
        # readiness cohorts and tech-transfer programs actually get
        # posted first.
        "keywords": [
            "spin-off", "spinoff", "technology transfer",
            "commercialization", "call for", "grant", "funding",
            "investment readiness", "invention",
        ],
    },

    # ---- calls for papers / conferences --------------------------------
    {
        "code": "ACM",
        "name": "Association for Computing Machinery",
        "listing_url": "https://www.acm.org/conferences",
        "keywords": ["call for papers", "cfp", "submission deadline"],
    },
    {
        "code": "WIKICFP",
        "name": "WikiCFP",
        "listing_url": "http://www.wikicfp.com/cfp/",
        # WikiCFP's listing links are conference names ("ICML 2027"),
        # never the literal words "call for papers" — the whole page
        # already is a call-for-papers index, so take every link.
        "keywords": [],
    },
]


def enabled_default_sources():
    return SOURCES
