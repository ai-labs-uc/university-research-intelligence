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



def generate_hash(value):

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()



def determine_category(opportunity_type):

    if opportunity_type == "GRANT":

        return "GRANT_PHILIPPINES"



    if opportunity_type == "CALL_FOR_PAPER_NATIONAL":

        return "CALL_FOR_PAPER_NATIONAL"



    if opportunity_type == "CALL_FOR_PAPER_INTERNATIONAL":

        return "CALL_FOR_PAPER_INTERNATIONAL"



    return "OTHER"





def detect_indexing(text):

    value = text.lower()

    indexes = []


    if "scopus" in value:

        indexes.append("SCOPUS")


    if (
        "web of science" in value
        or "wos" in value
        or "clarivate" in value
    ):

        indexes.append(
            "WEB_OF_SCIENCE"
        )


    if "ieee" in value:

        indexes.append(
            "IEEE"
        )


    if "acm" in value:

        indexes.append(
            "ACM"
        )


    return ",".join(indexes)





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



    try:


        for source in sources:


            print(
                "SOURCE:",
                source.get("name")
            )


            try:

                links = discover_links(
                    source
                )


            except Exception as e:


                print(
                    "SOURCE ERROR:",
                    e
                )

                continue



            for url in links[:20]:


                try:

                    title, content = fetch_page(
                        url
                    )


                except Exception as e:


                    print(
                        "FETCH ERROR:",
                        e
                    )

                    continue



                discovered += 1



                full_text = (
                    title
                    +
                    " "
                    +
                    content
                )



                opportunity_type = classify_type(
                    full_text
                )



                if opportunity_type is None:

                    continue



                category = determine_category(
                    opportunity_type
                )



                indexing_database = detect_indexing(
                    full_text
                )



                now = datetime.utcnow()



                content_hash = generate_hash(
                    url
                )



                sql = text("""

                INSERT INTO research_opportunities

                (

                opportunity_type,

                scope_type,

                category,


                title,

                organization,

                summary,


                indexing_database,


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


                :indexing_database,


                :source_url,

                :canonical_url,


                :hash,


                'OPEN',

                'UNVERIFIED',


                1,

                :last_seen,


                :created,

                :updated

                )


                ON DUPLICATE KEY UPDATE


                category = VALUES(category),

                title = VALUES(title),

                summary = VALUES(summary),

                indexing_database =
                    VALUES(indexing_database),

                last_seen =
                    VALUES(last_seen),

                updated_at =
                    VALUES(updated_at)

                """)



                db.execute(
                    sql,
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
                        source.get("name"),


                    "summary":
                        content[:3000],


                    "indexing_database":
                        indexing_database,


                    "source_url":
                        url,


                    "canonical_url":
                        url,


                    "hash":
                        content_hash,


                    "last_seen":
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


        return {

            "status":
                "FAILED",

            "error":
                str(e)

        }