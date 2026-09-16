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



BAD_PAGE_TITLES = [
    "calls and events",
    "news",
    "announcement",
    "announcements",
    "memorandum",
    "issuance",
    "home",
    "contact",
    "about us",
    "archive",
]


def generate_hash(value: str):

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()



def determine_category(
    opportunity_type,
    source_name,
    content
):

    text = (
        f"{source_name} {content}"
        .lower()
    )


    if opportunity_type == "GRANT":

        international_grants = [

            "nih",
            "nsf",
            "horizon europe",
            "world bank",
            "unesco",
            "european union",

        ]


        for item in international_grants:

            if item in text:

                return "GRANT_INTERNATIONAL"



        return "GRANT_PHILIPPINES"



    if opportunity_type == "CALL_FOR_PAPER_NATIONAL":

        return "CALL_FOR_PAPER_NATIONAL"



    if opportunity_type == "CALL_FOR_PAPER_INTERNATIONAL":

        return "CALL_FOR_PAPER_INTERNATIONAL"



    return "OTHER"



def is_bad_page(title):

    if not title:

        return True


    title = title.lower().strip()


    for item in BAD_PAGE_TITLES:

        if title == item:

            return True


    return False



def detect_indexing(content):

    text = content.lower()

    indexes = []


    if "scopus" in text:

        indexes.append("SCOPUS")


    if (
        "web of science" in text
        or "wos" in text
        or "clarivate" in text
    ):

        indexes.append("WEB_OF_SCIENCE")


    if "ieee" in text:

        indexes.append("IEEE")


    if "acm" in text:

        indexes.append("ACM")


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


    print(
        "Sources loaded:",
        len(sources)
    )


    try:


        for source in sources:


            source_name = source.get(
                "name",
                ""
            )


            print(
                "Processing source:",
                source_name
            )


            try:

                links = discover_links(
                    source
                )


                print(
                    "Links found:",
                    len(links)
                )


            except Exception as e:


                print(
                    "Source failed:",
                    source_name,
                    str(e)
                )

                continue



            # Limit per source for Render stability

            for url in links[:20]:


                try:

                    title, content = fetch_page(
                        url
                    )


                except Exception as e:


                    print(
                        "Fetch failed:",
                        url,
                        str(e)
                    )

                    continue



                discovered += 1



                if is_bad_page(title):

                    print(
                        "Skipping page:",
                        title
                    )

                    continue



                full_text = (
                    title
                    +
                    " "
                    +
                    content
                )



                opportunity_type = classify_type(
                    full_text,
                    source_name
                )



                if opportunity_type is None:

                    continue



                category = determine_category(
                    opportunity_type,
                    source_name,
                    full_text
                )



                indexing_database = detect_indexing(
                    full_text
                )



                now = datetime.utcnow()



                content_hash = generate_hash(
                    url
                )



                try:


                    result = db.execute(
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

                            :category,


                            :title,

                            :organization,

                            :summary,


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


                            category =
                            VALUES(category),


                            title =
                            VALUES(title),


                            summary =
                            VALUES(summary),


                            indexing_database =
                            VALUES(indexing_database),


                            is_current = 1,


                            last_seen =
                            VALUES(last_seen),


                            updated_at =
                            VALUES(updated_at)

                        """
                        ),

                        {


                        "opportunity_type":
                            opportunity_type,


                        "scope_type":
                            opportunity_type,


                        "category":
                            category,


                        "title":
                            title,


                        "organization":
                            source_name,


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
                            now,


                        }

                    )


                    if result.rowcount:

                        updated += 1

                    else:

                        inserted += 1



                    db.commit()



                except Exception as e:


                    db.rollback()


                    print(
                        "Database insert failed:",
                        str(e)
                    )



        # Hide expired grants

        db.execute(
            text(
            """

            UPDATE research_opportunities

            SET is_current = 0

            WHERE category LIKE 'GRANT%'

            AND deadline IS NOT NULL

            AND deadline < CURDATE()

            """
            )
        )


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
            "PIPELINE FAILED:",
            str(e)
        )


        return {

            "status":
                "FAILED",

            "error":
                str(e)

        }