from datetime import datetime

from sqlalchemy import text

from app.etl.collector import collect_source
from app.etl.sources import SOURCES
from app.etl.classifier import classify_type



def run_pipeline(db):

    """
    Main ETL pipeline.

    Collect:
        - Grants
        - National CFP
        - International CFP

    Update database:
        - Grants update existing records
        - CFP records remain searchable
    """


    started = datetime.utcnow()


    discovered_count = 0
    inserted_count = 0
    updated_count = 0



    try:


        for source in SOURCES:


            try:


                source_items = collect_source(source)



            except Exception as e:


                print(
                    "Collector failed:",
                    source,
                    e
                )

                continue





            for item in source_items:


                discovered_count += 1



                combined_text = " ".join(
                    [

                    str(item.get("title","")),

                    str(item.get("summary","")),

                    str(item.get("organization","")),

                    str(item.get("keywords",""))

                    ]
                )



                opportunity_type = classify_type(
                    combined_text
                )



                # Ignore unrelated pages

                if opportunity_type is None:

                    continue



                scope_type = opportunity_type



                now = datetime.utcnow()



                values = {


                    "source_id":
                        source.get("id"),


                    "opportunity_type":
                        opportunity_type,


                    "scope_type":
                        scope_type,


                    "title":
                        item.get("title"),


                    "organization":
                        item.get("organization"),


                    "summary":
                        item.get("summary"),


                    "eligibility":
                        item.get("eligibility"),


                    "topics":
                        item.get("topics"),


                    "discipline":
                        item.get(
                            "discipline",
                            ""
                        ),


                    "indexing_database":
                        item.get(
                            "indexing_database",
                            ""
                        ),


                    "country":
                        item.get("country"),


                    "deadline":
                        item.get("deadline"),


                    "source_url":
                        item.get("source_url"),


                    "canonical_url":
                        item.get(
                            "canonical_url",
                            item.get("source_url")
                        ),


                    "content_hash":
                        item.get("content_hash"),


                    "status":
                        "OPEN",


                    "verification_status":
                        "VERIFIED",


                    "is_current":
                        1,


                    "last_seen":
                        now,


                    "discovered_at":
                        now,


                    "updated_at":
                        now

                }



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


                ON DUPLICATE KEY UPDATE


                    title = VALUES(title),

                    summary = VALUES(summary),

                    deadline = VALUES(deadline),

                    status = VALUES(status),

                    verification_status =
                        VALUES(verification_status),

                    is_current = 1,

                    last_seen =
                        VALUES(last_seen),

                    updated_at =
                        VALUES(updated_at)

                """
                )



                result = db.execute(
                    sql,
                    values
                )



                if result.rowcount == 1:

                    inserted_count += 1

                else:

                    updated_count += 1





            db.commit()





        # hide expired grants

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





        finished = datetime.utcnow()



        return {


            "status":
                "SUCCESS",


            "started_at":
                started.isoformat(),


            "finished_at":
                finished.isoformat(),


            "discovered":
                discovered_count,


            "inserted":
                inserted_count,


            "updated":
                updated_count

        }





    except Exception as e:


        db.rollback()


        print(
            "Pipeline failed:",
            e
        )


        return {


            "status":
                "FAILED",


            "error":
                str(e)

        }