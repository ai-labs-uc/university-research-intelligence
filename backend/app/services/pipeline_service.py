from datetime import datetime
from sqlalchemy import text


def process_opportunity(
    db,
    source_id,
    item,
    classify_type
):

    combined_text = " ".join([
        item.get("title",""),
        item.get("summary",""),
        item.get("organization",""),
        item.get("keywords","")
    ])


    opportunity_type = classify_type(combined_text)


    # Ignore unknown records
    if opportunity_type is None:
        return


    scope_type = opportunity_type


    discipline = item.get(
        "discipline",
        ""
    )


    indexing_database = item.get(
        "indexing_database",
        ""
    )


    now = datetime.utcnow()


    sql = text("""
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

        :created,
        :updated
    )

    ON DUPLICATE KEY UPDATE

        title=:title,
        summary=:summary,
        deadline=:deadline,

        is_current=1,
        last_seen=:last_seen,

        updated_at=:updated

    """)


    db.execute(
        sql,
        {

        "source_id":source_id,

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
            discipline,


        "indexing_database":
            indexing_database,


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


        "created":
            now,


        "updated":
            now
        }
    )

    db.commit()