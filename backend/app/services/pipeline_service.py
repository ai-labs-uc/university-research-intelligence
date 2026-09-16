def run_pipeline(db):
    """
    Main ETL pipeline runner.

    Collects sources, classifies opportunities,
    updates grants, and stores CFP records.
    """

    from app.etl.collector import collect_source
    from app.etl.sources import SOURCES
    from app.etl.classifier import classify_type

    from datetime import datetime


    inserted = 0
    updated = 0


    for source in SOURCES:

        try:

            items = collect_source(source)


            for item in items:

                combined_text = " ".join([
                    item.get("title", ""),
                    item.get("summary", ""),
                    item.get("organization", "")
                ])


                opportunity_type = classify_type(
                    combined_text
                )


                # Ignore unknown content
                if opportunity_type is None:
                    continue


                scope_type = opportunity_type


                now = datetime.utcnow()


                db.execute(
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
                        1,
                        :last_seen,
                        :discovered_at,
                        :updated_at
                    )

                    ON DUPLICATE KEY UPDATE

                    title=:title,
                    summary=:summary,
                    deadline=:deadline,
                    last_seen=:last_seen,
                    updated_at=:updated_at

                    """,
                    {

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
                    item.get("discipline"),


                    "indexing_database":
                    item.get("indexing_database"),


                    "country":
                    item.get("country"),


                    "deadline":
                    item.get("deadline"),


                    "source_url":
                    item.get("source_url"),


                    "canonical_url":
                    item.get("canonical_url"),


                    "content_hash":
                    item.get("content_hash"),


                    "status":
                    "OPEN",


                    "verification_status":
                    "VERIFIED",


                    "last_seen":
                    now,


                    "discovered_at":
                    now,


                    "updated_at":
                    now

                    }
                )


                inserted += 1



            db.commit()



        except Exception as e:

            print(
                "Pipeline error:",
                source,
                e
            )


    return {

        "status": "completed",

        "inserted": inserted,

        "updated": updated

    }