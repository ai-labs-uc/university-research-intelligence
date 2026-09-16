from datetime import datetime

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

from app.etl.utils import clean_text


def run_pipeline(db):

    started = datetime.utcnow()

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
                    "Source discovery failed:",
                    source.get("name"),
                    e
                )

                continue



            for url in links:

                try:

                    title, content = fetch_page(url)


                except Exception as e:

                    print(
                        "Page fetch failed:",
                        url,
                        e
                    )

                    continue



                discovered_count += 1



                combined_text = clean_text(
                    f"""
                    {title}
                    {content}
                    """
                )



                opportunity_type = classify_type(
                    combined_text
                )



                if opportunity_type is None:

                    continue



                scope_type = opportunity_type



                if "scopus" in combined_text.lower():

                    indexing_database = "SCOPUS"

                elif "web of science" in combined_text.lower():

                    indexing_database = "WEB_OF_SCIENCE"

                elif "wos" in combined_text.lower():

                    indexing_database = "WEB_OF_SCIENCE"

                else:

                    indexing_database = ""



                now = datetime.utcnow()



                values = {

                    "source_id": None,

                    "opportunity_type":
                        opportunity_type,

                    "scope_type":
                        scope_type,


                    "title":
                        title,


                    "organization":
                        source.get("name"),


                    "summary":
                        content[:3000],


                    "eligibility":
                        "",


                    "topics":
                        "",


                    "discipline":
                        "",


                    "indexing_database":
                        indexing_database,


                    "country":
                        "",


                    "deadline":
                        None,


                    "source_url":
                        url,


                    "canonical_url":
                        url,


                    "content_hash":
                        None,


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



                db.execute(
                    text(
                    """

                    INSERT INTO research_opportunities

                    (

                    source_id,
                    opportunity_type,
                    scope_type,

                    title,
                    organization,

                    summary,
                    eligibility,

                    topics,
                    discipline,
                    indexing_database,

                    country,
                    deadline,

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

                    :source_id,
                    :opportunity_type,
                    :scope_type,

                    :title,
                    :organization,

                    :summary,
                    :eligibility,

                    :topics,
                    :discipline,
                    :indexing_database,

                    :country,
                    :deadline,

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

                    """
                    ),
                    values
                )


                inserted_count += 1



            db.commit()



        # Hide expired grants only

        db.execute(
            text(
            """

            UPDATE research_opportunities

            SET is_current = 0

            WHERE opportunity_type='GRANT'

            AND deadline IS NOT NULL

            AND deadline < CURDATE()

            """
            )
        )


        db.commit()



        return {

            "status": "SUCCESS",

            "started_at":
                started.isoformat(),

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

            "status": "FAILED",

            "error": str(e)

        }