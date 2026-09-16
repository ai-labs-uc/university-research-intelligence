import re


GRANT_KEYWORDS = [
    "grant",
    "funding",
    "research funding",
    "funding opportunity",
    "call for proposal",
    "research grant",
    "grants-in-aid",
    "rfp",
    "financial support"
]


INTERNATIONAL_CFP_KEYWORDS = [
    "scopus",
    "web of science",
    "wos",
    "clarivate",
    "indexed journal",
    "ieee",
    "acm",
    "springer",
    "elsevier",
    "wiley",
    "taylor and francis",
    "mdpi",
    "international conference",
    "international symposium",
    "call for papers"
]


NATIONAL_CFP_KEYWORDS = [
    "philippines",
    "philippine",
    "ched",
    "dost",
    "national conference",
    "local conference",
    "university conference",
    "regional conference"
]


def normalize(text):
    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    )


def classify_type(text):

    text = normalize(text)


    # International CFP first
    for keyword in INTERNATIONAL_CFP_KEYWORDS:
        if keyword in text:
            return "CALL_FOR_PAPER_INTERNATIONAL"


    # National CFP
    for keyword in NATIONAL_CFP_KEYWORDS:
        if keyword in text:
            return "CALL_FOR_PAPER_NATIONAL"


    # Grants
    for keyword in GRANT_KEYWORDS:
        if keyword in text:
            return "GRANT"


    return None