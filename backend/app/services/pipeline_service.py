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


def make_hash(value: str):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()



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
                        "Fetch failed:",
                        url,
                        e
                    )

                    continue



                discovered_count += 1


                combined_text = (
                    title
                    +
                    " "
                    +
                    content
                ).lower()



                opportunity_type = classify_type(
                    combined_text
                )


                # Ignore irrelevant pages

                if opportunity_type is None:
                    continue



                scope_type = opportunity_type



                indexing_database = ""


                if "scopus" in combined_text:

                    indexing_database = "SCOPUS"


                if (
                    "web of science" in combined_text
                    or "wos" in combined_text
                    or "clarivate" in combined_text
                ):

                    indexing_database = "WEB_OF_SCIENCE"



                content_hash = make_hash(url)



                now = datetime.utcnow()



                sql = text(
                """

                INSERT INTO research_opportunities

                (
                    source_id,

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

                    NULL,

                    :opportunity_type,

                    :scope_type,


                    :title,

                    :organization,

                    :summary,


                    '',

                    '',

                    :indexing_database,


                    :source_url,

                    :canonical_url,


                    :content_hash,


                    'OPEN',

                    'UNVERIFIED',


                    1,

                    :last_seen,


                    :discovered_at,

                    :updated_at

                )


                ON DUPLICATE KEY UPDATE


                    title = VALUES(title),

                    summary = VALUES(summary),

                    status = 'OPEN',

                    is_current = 1,

                    last_seen = VALUES(last_seen),

                    updated_at = VALUES(updated_at)

                """
                )



                result = db.execute(
                    sql,
                    {

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


                    "indexing_database":
                        indexing_database,


                    "source_url":
                        url,


                    "canonical_url":
                        url,


                    "content_hash":
                        content_hash,


                    "last_seen":
                        now,


                    "discovered_at":
                        now,


                    "updated_at":
                        now

                    }
                )


                if result.rowcount == 1:

                    inserted_count += 1

                else:

                    updated_count += 1



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