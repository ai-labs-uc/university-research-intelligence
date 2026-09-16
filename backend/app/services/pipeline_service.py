from datetime import datetime
import hashlib

from sqlalchemy import text

from app.etl.collector import (
    discover_links,
    fetch_page,
)

from app.etl.sources import (
    enabled_default_sources,
    INTERNATIONAL_CFP_SOURCES,
)

from app.etl.classifier import classify_type



BAD_TITLES = [

    "calls and events",

    "news",

    "announcement",

    "announcements",

    "memorandum",

    "issuance",

    "home",

    "contact",

    "about us",

]



def make_hash(url):

    return hashlib.sha256(
        url.encode()
    ).hexdigest()



def get_category(opportunity_type):


    if opportunity_type == "GRANT":

        return "GRANT_PHILIPPINES"



    if opportunity_type == "CALL_FOR_PAPER_NATIONAL":

        return "CALL_FOR_PAPER_NATIONAL"



    if opportunity_type == "CALL_FOR_PAPER_INTERNATIONAL":

        return "CALL_FOR_PAPER_INTERNATIONAL"



    return "OTHER"





def has_opportunity_content(content):


    content = content.lower()


    keywords = [

        "deadline",

        "submission",

        "proposal",

        "application",

        "funding",

        "grant",

        "research",

        "paper",

        "abstract",

        "manuscript",

        "conference"

    ]


    return any(
        word in content
        for word in keywords
    )





def run_pipeline(db):


    print(
        "=== PIPELINE START ==="
    )


    discovered = 0

    inserted = 0

    updated = 0



    sources = (

        enabled_default_sources()

        +

        INTERNATIONAL_CFP_SOURCES

    )


    print(
        "TOTAL SOURCES:",
        len(sources)
    )



    try:


        for source in sources:


            source_name = source.get(
                "name",
                ""
            )


            print(
                "SOURCE:",
                source_name
            )



            try:

                links = discover_links(
                    source
                )


            except Exception as e:

                print(
                    "SOURCE FAILED:",
                    e
                )

                continue



            print(
                "LINK COUNT:",
                len(links)
            )



            for url in links[:20]:


                try:

                    title, content = fetch_page(
                        url
                    )


                except Exception as e:

                    print(
                        "FETCH FAILED:",
                        url,
                        e
                    )

                    continue



                if not title:

                    continue



                if title.lower() in BAD_TITLES:

                    print(
                        "SKIP PAGE:",
                        title
                    )

                    continue



                if not has_opportunity_content(
                    content
                ):

                    print(
                        "SKIP NON OPPORTUNITY:",
                        title
                    )

                    continue



                discovered += 1



                opportunity_type = classify_type(

                    title,

                    content,

                    source_name

                )



                if opportunity_type is None:

                    continue



                category = get_category(
                    opportunity_type
                )



                now = datetime.utcnow()



                db.execute(

                    text(

                    """

                    INSERT INTO research_opportunities

                    (

                    opportunity_type,

                    scope_type,

                    category,

                    title,

                    organization,

                    summary,

                    source_url,

                    canonical_url,

                    content_hash,

                    status,

                    verification_status,

                    is_current,

                    last_seen,

                    discovered_at,

                    updated_at

                    )


                    VALUES

                    (

                    :type,

                    :scope,

                    :category,

                    :title,

                    :organization,

                    :summary,

                    :url,

                    :canonical,

                    :hash,

                    'OPEN',

                    'UNVERIFIED',

                    1,

                    :seen,

                    :created,

                    :updated

                    )


                    ON DUPLICATE KEY UPDATE


                    category =
                    VALUES(category),


                    summary =
                    VALUES(summary),


                    last_seen =
                    VALUES(last_seen),


                    updated_at =
                    VALUES(updated_at)

                    """

                    ),

                    {


                    "type":
                    opportunity_type,


                    "scope":
                    opportunity_type,


                    "category":
                    category,


                    "title":
                    title,


                    "organization":
                    source_name,


                    "summary":
                    content[:3000],


                    "url":
                    url,


                    "canonical":
                    url,


                    "hash":
                    make_hash(url),


                    "seen":
                    now,


                    "created":
                    now,


                    "updated":
                    now

                    }

                )



                inserted += 1



            db.commit()



        print(
            "=== PIPELINE COMPLETE ==="
        )



        return {


            "status":
            "SUCCESS",


            "discovered":
            discovered,


            "inserted":
            inserted,


            "updated":
            updated

        }



    except Exception as e:


        db.rollback()


        print(
            "PIPELINE ERROR:",
            str(e)
        )


        return {

            "status":
            "FAILED",

            "error":
            str(e)

        }