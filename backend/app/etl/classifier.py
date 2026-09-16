import re


GRANT_KEYWORDS = [

    "research grant",
    "grant opportunity",
    "funding opportunity",
    "funding program",
    "project funding",
    "call for proposal",
    "request for proposal",
    "rfp",
    "grants-in-aid",

    "dost grant",
    "pcieerd",
    "pchrd",
    "pcaarrd",

    "department of agriculture",
    "da research",

    "commission on higher education",
    "ched research",

    "denr research",

    "national science foundation",
    "nih grant",
    "horizon europe",
    "world bank grant"

]


INTERNATIONAL_CFP_KEYWORDS = [

    "scopus",
    "web of science",
    "wos",
    "clarivate",

    "ieee",
    "ieee xplore",
    "acm",

    "springer",
    "elsevier",
    "wiley",
    "taylor and francis",
    "mdpi",

    "international conference",
    "international symposium",

    "call for papers",
    "cfp",

    "paper submission",
    "submit paper",
    "full paper",
    "abstract submission"

]


NATIONAL_CFP_KEYWORDS = [

    "philippine conference",
    "philippines conference",

    "national conference",

    "university research conference",

    "research conference",

    "paper submission",

    "call for papers",

    "abstract submission"

]



IGNORE_KEYWORDS = [

    "memorandum",
    "issuance",
    "administrative order",
    "announcement only",
    "scholarship",
    "job opening"

]



def normalize(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    )



def classify_type(text, source_name):

    text = normalize(text)



    # Ignore administrative pages

    for word in IGNORE_KEYWORDS:

        if word in text:

            return None



    # Grants first

    for word in GRANT_KEYWORDS:

        if word in text:

            return "GRANT"



    # International indexed CFP

    for word in INTERNATIONAL_CFP_KEYWORDS:

        if word in text:

            return "CALL_FOR_PAPER_INTERNATIONAL"



    # National CFP

    for word in NATIONAL_CFP_KEYWORDS:

        if word in text:

            return "CALL_FOR_PAPER_NATIONAL"



    return None