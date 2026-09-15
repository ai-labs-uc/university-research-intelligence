"""
Plain rule-based classification for scraped opportunities.

This replaces the earlier Ollama step. It only ever labels an opportunity
type and pulls out topic keywords that are already present in the source
text — it never invents facts (deadlines, eligibility, funding amounts).
Those must still come directly from the source page.

The system's scope is deliberately narrow: calls for papers and grants
only (see database/ERD.md for why the broader type list — conferences,
fellowships, scholarships, startup challenges, etc. — was removed).
classify_type() returns None for anything that isn't clearly one of the
two, and the pipeline skips ingesting those rather than mis-labeling them.
"""

# Ordered: first matching classification wins, so put more specific
# phrases first. A "special issue" or "call for proposal" is folded into
# the closer of the two remaining buckets rather than dropped, since both
# are, in substance, a call for papers / a grant under another name.
TYPE_KEYWORDS = [
    ("CALL_FOR_PAPER", [
        "call for paper", "call for papers", "cfp",
        "manuscript submission", "paper submission",
        "abstract submission", "extended abstract",
        "call for publication", "call for publications",
        "call for chapters", "call for manuscripts",
        "special issue",
    ]),
    ("GRANT", [
        "grant", "funding opportunity", "research grant",
        "grants-in-aid", "grant-in-aid",
        "call for proposal", "call for proposals",
        "request for proposal", "rfp", "request for submission",
    ]),
]

# A small, editable vocabulary. Extend this list to match the research
# priorities of your institution — no AI call is involved, it is a
# straight substring scan against the scraped title + text.
TOPIC_VOCABULARY = [
    "artificial intelligence", "machine learning", "deep learning",
    "data science", "cybersecurity", "renewable energy",
    "climate change", "biotechnology", "public health",
    "disaster resilience", "gis", "remote sensing",
    "education technology", "agriculture", "food security",
    "materials science", "robotics", "internet of things",
    "blockchain", "social science", "nanotechnology",
    "environmental science", "water resources", "energy",
    "marine science", "disaster risk reduction",
    "entrepreneurship", "startup", "innovation", "fintech",
    "agritech", "digital transformation", "circular economy",
    "social enterprise", "spin-off", "technology transfer",
    "commercialization", "intellectual property",
]


def classify_type(text: str) -> str | None:
    """Returns "CALL_FOR_PAPER" or "GRANT", or None when the text doesn't
    clearly match either — callers should treat None as out of scope and
    skip the item rather than guessing."""
    lowered = text.lower()
    for opportunity_type, keywords in TYPE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return opportunity_type
    return None


def extract_topics(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(
        topic for topic in TOPIC_VOCABULARY if topic in lowered
    )


# Literal phrases that indicate a publication venue's indexing/database
# status, as institutions and researchers actually care about it when
# deciding where to submit (Scopus and Web of Science first, since CHED
# and most university RIGA/promotion points systems key off those two).
# Unordered/non-exclusive on purpose: a single call for papers can
# legitimately advertise more than one index at once ("Scopus and WoS
# indexed journal"), so every match is kept, not just the first.
INDEXING_KEYWORDS = [
    ("SCOPUS", ["scopus"]),
    ("WEB_OF_SCIENCE", [
        "web of science", "wos-indexed", "wos indexed",
        "clarivate", "isi-indexed", "isi indexed",
        "science citation index", "sci-indexed", "sci indexed",
    ]),
    ("ASEAN_CITATION_INDEX", [
        "asean citation index", "aci-indexed", "aci indexed",
    ]),
    ("PUBMED", ["pubmed", "medline"]),
    ("IEEE_XPLORE", ["ieee xplore"]),
    ("DOAJ", [
        "doaj", "directory of open access journals",
    ]),
    ("CHED_ACCREDITED", [
        "ched accredited journal", "ched-accredited journal",
        "ched recognized journal",
    ]),
    ("PEER_REVIEWED", [
        "peer-reviewed journal", "peer reviewed journal",
        "refereed journal",
    ]),
]


def detect_indexing(text: str) -> list[str]:
    """Return every indexing/database label whose phrasing literally
    appears in the scraped text — never inferred from the venue name
    alone. Empty result means the source page didn't state an index,
    not that the venue is unindexed; callers/UI should present it that
    way (e.g. "not stated on source page") rather than "not indexed"."""
    lowered = text.lower()
    return sorted(
        label
        for label, keywords in INDEXING_KEYWORDS
        if any(keyword in lowered for keyword in keywords)
    )
