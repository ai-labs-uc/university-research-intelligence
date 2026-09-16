import re


GRANT_SOURCE_KEYWORDS = [

    "dost",
    "pcieerd",
    "pchrd",
    "pcaarrd",
    "tapi",

    "department of agriculture",
    "da",

    "ched",
    "commission on higher education",

    "denr",

    "nih",
    "national science foundation",
    "nsf",

    "horizon europe",
    "world bank",
    "unesco"

]


GRANT_KEYWORDS = [

    "research grant",

    "grant program",

    "grant opportunity",

    "funding opportunity",

    "research funding",

    "funding support",

    "funded project",

    "call for proposal",

    "call for proposals",

    "request for proposal",

    "rfp",

    "grants-in-aid",

    "project proposal",

    "research project funding"

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

    "paper submission",

    "abstract submission",

    "submit manuscript",

]



NATIONAL_CFP_KEYWORDS = [

    "philippine conference",

    "philippines conference",

    "national conference",

    "university research conference",

    "research conference",

    "philippine journal",

    "local journal",

    "call for papers",

    "paper submission",

    "abstract submission"

]



INVALID_PAGE_KEYWORDS = [

    "calls and events",

    "news",

    "announcement",

    "memorandum",

    "issuance",

    "contact",

    "about us",

    "homepage",

]



def normalize(text):

    if not text:

        return ""

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    )



def classify_type(
    title,
    content,
    source_name=""
):

    combined = normalize(
        f"""
        {title}
        {content}
        {source_name}
        """
    )


    source = normalize(
        source_name
    )


    # ----------------------------
    # Ignore category pages
    # ----------------------------

    if title:

        title_clean = normalize(title)

        for bad in INVALID_PAGE_KEYWORDS:

            if title_clean == bad:

                return None



    # ----------------------------
    # Grants first
    # ----------------------------

    for word in GRANT_SOURCE_KEYWORDS:

        if word in source:

            for grant_word in GRANT_KEYWORDS:

                if grant_word in combined:

                    return "GRANT"



    for grant_word in GRANT_KEYWORDS:

        if grant_word in combined:

            return "GRANT"



    # ----------------------------
    # International CFP
    # ----------------------------

    for word in INTERNATIONAL_CFP_KEYWORDS:

        if word in combined:

            return "CALL_FOR_PAPER_INTERNATIONAL"



    # ----------------------------
    # National CFP
    # ----------------------------

    for word in NATIONAL_CFP_KEYWORDS:

        if word in combined:

            return "CALL_FOR_PAPER_NATIONAL"



    return None