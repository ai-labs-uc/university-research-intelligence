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



def create_hash(value: str):

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()



def run_pipeline(db):

    started_at = datetime.utcnow()


    discovered_count = 0
    inserted_count = 0
    updated_count = 0


    sources = (
        enabled_default_sources()
        +
        INTERNATIONAL_CFP_SOURCES
    )


    try:


        for source in sources:


            try:

                links = discover_links(source)


            except Exception as e:

                print(
                    "Source discovery error:",
                    source.get("name"),
                    str(e)
                )

                continue



            for url in links:


                try:

                    title, content = fetch_page(url)


                except Exception as e:

                    print(
                        "Fetch error:",
                        url,
                        str(e)
                    )

                    continue



                discovered_count += 1



                combined_text = (
                    title
                    + " "
                    + content
                )



                opportunity_type = classify_type(
                    combined_text
                )



                if opportunity_type is None:

                    continue



                now = datetime.utcnow()



                indexing_database = ""

                lower_text = combined_text.lower()



                if "scopus" in lower_text:

                    indexing_database = "SCOPUS"


                elif (
                    "web of science" in lower_text
                    or "wos" in lower_text
                    or "clarivate" in lower_text
                ):

                    indexing_database = "WEB_OF_SCIENCE"



                content_hash = create_hash(url)



                values = {

                    "opportunity_type":
                        opportunity_type,


                    "scope_type":
                        opportunity_type,


                    "title":
                        title,


                    "organization":
                        source.get("name"),


                    "summary":
                        content[:3000],


                    "topics":
                        "",


                    "discipline":
                        "",


                    "indexing_database":
                        indexing_database,


                    "source_url":
                        url,


                    "canonical_url":
                        url,


                    "content_hash":
                        content_hash,


                    "status":
                        "OPEN",


                    "verification_status":
                        "UNVERIFIED",


                    "is_current":
                        1,


                    "last_seen":
                        now,


                    "discovered_at":
                        now,


                    "updated_at":
                        now

                }



                query = text(
                """

                INSERT INTO research_opportunities

                (

                    opportunity_type,

                    scope_type,

                    title,

                    organization,

                    summary,

                    topics,

                    discipline,

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

                    :opportunity_type,

                    :scope_type,

                    :title,

                    :organization,

                    :summary,

                    :topics,

                    :discipline,

                    :indexing_database,

                    :source_url,

                    :canonical_url,

                    :content_hash,

                    :status,

                    :verification_status,

                    :is_current,

                    :last_seen,

                    :discovered_at,

                    :updated_at

                )


                ON DUPLICATE KEY UPDATE


                    title = VALUES(title),

                    summary = VALUES(summary),

                    status = VALUES(status),

                    is_current = 1,

                    last_seen = VALUES(last_seen),

                    updated_at = VALUES(updated_at)

                """
                )



                result = db.execute(
                    query,
                    values
                )



                if result.rowcount:

                    updated_count += 1

                else:

                    inserted_count += 1




            db.commit()





        # Hide expired grants only

        db.execute(
            text(
            """

            UPDATE research_opportunities

            SET is_current = 0

            WHERE opportunity_type = 'GRANT'

            AND deadline IS NOT NULL

            AND deadline < CURDATE()

            """
            )
        )


        db.commit()



        return {


            "status":
                "SUCCESS",


            "started_at":
                started_at.isoformat(),


            "finished_at":
                datetime.utcnow().isoformat(),


            "discovered":
                discovered_count,


            "inserted":
                inserted_count,


            "updated":
                updated_count

        }





    except Exception as e:


        db.rollback()


        return {

            "status":
                "FAILED",

            "error":
                str(e)

        }