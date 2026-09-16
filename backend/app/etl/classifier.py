import re



GRANT_KEYWORDS = [

    "research grant",

    "grant program",

    "funding opportunity",

    "research funding",

    "call for proposal",

    "call for proposals",

    "request for proposal",

    "rfp",

    "grants-in-aid",

    "project funding",

    "financial support",

]



GRANT_ORGANIZATIONS = [

    "dost",

    "pcieerd",

    "pchrd",

    "pcaarrd",

    "ched",

    "commission on higher education",

    "department of agriculture",

    "denr",

    "tapi",

    "nih",

    "nsf",

    "horizon europe",

    "world bank",

]



INTERNATIONAL_CFP = [

    "scopus",

    "web of science",

    "wos",

    "clarivate",

    "ieee",

    "acm",

    "springer",

    "elsevier",

    "wiley",

    "mdpi",

    "international conference",

    "call for papers",

    "paper submission",

    "abstract submission",

]



NATIONAL_CFP = [

    "philippine conference",

    "philippines conference",

    "national conference",

    "university research conference",

    "philippine journal",

    "research conference",

    "call for papers",

]




def normalize(text):

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

    text = normalize(
        f"""
        {title}
        {content}
        {source_name}
        """
    )



    # Grants first

    for word in GRANT_KEYWORDS:

        if word in text:

            return "GRANT"



    for org in GRANT_ORGANIZATIONS:

        if org in text:

            if any(
                x in text
                for x in GRANT_KEYWORDS
            ):

                return "GRANT"




    # International CFP

    for word in INTERNATIONAL_CFP:

        if word in text:

            return "CALL_FOR_PAPER_INTERNATIONAL"




    # National CFP

    for word in NATIONAL_CFP:

        if word in text:

            return "CALL_FOR_PAPER_NATIONAL"



    return None