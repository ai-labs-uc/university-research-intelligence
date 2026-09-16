"""
Configured opportunity sources for the Research Intelligence ETL.

The collector uses:
    listing_url
    keywords

The keywords are matched against visible link text on each listing page.

An empty keywords list means that all same-host links may be considered.
"""


# ============================================================
# MAIN SOURCES
# ============================================================

SOURCES = [

    # ========================================================
    # PHILIPPINE RESEARCH GRANTS / FUNDING
    # ========================================================

    {
        "code": "PCIEERD",
        "name": "DOST-PCIEERD",
        "listing_url": "https://pcieerd.dost.gov.ph/",
        "keywords": [
            "grant",
            "funding",
            "proposal",
            "call for proposal",
            "research",
        ],
    },

    {
        "code": "PCHRD",
        "name": "DOST-PCHRD",
        "listing_url": "https://www.pchrd.dost.gov.ph/",
        "keywords": [
            "grant",
            "funding",
            "proposal",
            "call for proposal",
            "research",
        ],
    },

    {
        "code": "PCAARRD",
        "name": "DOST-PCAARRD",
        "listing_url": "https://www.pcaarrd.dost.gov.ph/",
        "keywords": [
            "grant",
            "funding",
            "proposal",
            "call for proposal",
            "research",
        ],
    },

    {
        "code": "NRCP",
        "name": "National Research Council of the Philippines",
        "listing_url": "https://nrcp.dost.gov.ph/",
        "keywords": [
            "grant",
            "grants-in-aid",
            "funding",
            "proposal",
            "research",
        ],
    },

    {
        "code": "CHED",
        "name": "Commission on Higher Education",
        "listing_url": "https://ched.gov.ph/",
        "keywords": [
            "research",
            "grant",
            "funding",
            "proposal",
        ],
    },

    {
        "code": "SEI",
        "name": "DOST Science Education Institute",
        "listing_url": "https://www.sei.dost.gov.ph/",
        "keywords": [
            "grant",
            "research",
            "funding",
            "proposal",
        ],
    },

    {
        "code": "TAPI",
        "name": "DOST Technology Application and Promotion Institute",
        "listing_url": "https://tapitechtransfer.dost.gov.ph/news-archive",
        "keywords": [
            "grant",
            "funding",
            "research",
            "technology transfer",
            "commercialization",
            "proposal",
            "startup",
            "spin-off",
        ],
    },

    {
        "code": "STARTUPGOVPH",
        "name": "Startup Innovations Portal",
        "listing_url": "https://startup.gov.ph/",
        "keywords": [
            "grant",
            "funding",
            "research",
            "proposal",
            "open call",
            "startup grant",
        ],
    },

    {
        "code": "DA",
        "name": "Department of Agriculture",
        "listing_url": "https://www.da.gov.ph/",
        "keywords": [
            "research",
            "grant",
            "funding",
            "proposal",
        ],
    },

    {
        "code": "DENR",
        "name": "Department of Environment and Natural Resources",
        "listing_url": "https://denr.gov.ph/",
        "keywords": [
            "research",
            "grant",
            "funding",
            "proposal",
        ],
    },


    # ========================================================
    # NATIONAL CALLS FOR PAPERS
    # ========================================================

    # Additional Philippine university/journal/conference
    # sources can be added here as their public listing pages
    # are identified and verified.


    # ========================================================
    # INTERNATIONAL CALLS FOR PAPERS
    # ========================================================

    {
        "code": "ACM",
        "name": "Association for Computing Machinery",
        "listing_url": "https://www.acm.org/conferences",
        "keywords": [
            "conference",
            "call for papers",
            "submission",
        ],
    },

    {
        "code": "WIKICFP",
        "name": "WikiCFP",
        "listing_url": "http://www.wikicfp.com/cfp/",
        "keywords": [],
    },

]


# ============================================================
# ADDITIONAL INTERNATIONAL CFP SOURCES
# ============================================================

INTERNATIONAL_CFP_SOURCES = [

    {
        "code": "IEEE",
        "name": "IEEE Conferences",
        "listing_url": "https://conferences.ieeeauthorcenter.ieee.org/",
        "keywords": [
            "conference",
            "call for papers",
            "submission",
        ],
    },

    {
        "code": "SPRINGER",
        "name": "Springer Conferences",
        "listing_url": (
            "https://www.springer.com/"
            "gp/computer-science/lncs/conferences"
        ),
        "keywords": [
            "conference",
            "call for papers",
            "submission",
        ],
    },

]


# ============================================================
# PUBLIC ACCESSOR
# ============================================================

def enabled_default_sources():
    """
    Return the default enabled ETL sources.

    Kept as a function because pipeline_service.py imports this
    function directly.
    """

    return SOURCES