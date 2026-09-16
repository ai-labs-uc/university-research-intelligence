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



def generate_hash(value: str):

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()



def detect_indexing(content: str):

    text_value = content.lower()

    result = []


    if "scopus" in text_value:
        result.append("SCOPUS")


    if (
        "web of science" in text_value
        or "wos" in text_value
        or "clarivate" in text_value
    ):
        result.append("WEB_OF_SCIENCE")


    if "ieee xplore" in text_value:
        result.append("IEEE_XPLORE")


    return ",".join(result)



def run_pipeline(db):

    print("=== PIPELINE STARTED ===")


    started = datetime.utcnow()


    discovered = 0
    inserted = 0
    updated = 0



    try:


        sources = (
            enabled_default_sources()
            +
            INTERNATIONAL_CFP_SOURCES
        )


        print(
            "=== SOURCES LOADED ===",
            len(sources)
        )



        # Limit initial runs for Render free tier

        sources = sources[:5]



        for source in sources:


            print(
                "=== PROCESSING SOURCE ===",
                source.get("name")
            )


            try:


                links = discover_links(
                    source
                )


                print(
                    "=== LINKS FOUND ===",
                    len(links)
                )


            except Exception as e:


                print(
                    "SOURCE ERROR:",
                    source.get("name"),
                    str(e)
                )

                continue



            # limit pages per source

            for url in links[:10]:


                print(
                    "FETCHING:",
                    url
                )



                try:


                    title, content = fetch_page(
                        url
                    )


                except Exception as e:


                    print(
                        "FETCH ERROR:",
                        url,
                        str(e)
                    )

                    continue



                discovered += 1



                combined_text = (
                    title
                    +
                    " "
                    +
                    content
                )



                opportunity_type = classify_type(
                    combined_text
                )



                if opportunity_type is None:


                    print(
                        "SKIPPED - UNKNOWN TYPE:",
                        title
                    )

                    continue



                now = datetime.utcnow()



                content_hash = generate_hash(
                    url
                )



                indexing_database = detect_indexing(
                    combined_text
                )



                try:


                    result = db.execute(
                        text(
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

                        :type,

                        :scope,


                        :title,

                        :organization,


                        :summary,


                        :topics,

                        :discipline,


                        :indexing_database,


                        :source_url,

                        :canonical_url,


                        :hash,


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


                        "type":
                            opportunity_type,


                        "scope":
                            opportunity_type,


                        "title":
                            title,


                        "organization":
                            source.get(
                                "name"
                            ),


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


                        "hash":
                            content_hash,


                        "last_seen":
                            now,


                        "discovered_at":
                            now,


                        "updated_at":
                            now

                        }
                    )



                    if result.rowcount:

                        updated += 1

                    else:

                        inserted += 1



                    db.commit()



                except Exception as e:


                    print(
                        "DATABASE ERROR:",
                        str(e)
                    )

                    db.rollback()



        print(
            "=== HIDING EXPIRED GRANTS ==="
        )


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
            "=== PIPELINE FAILED ===",
            str(e)
        )


        return {


            "status":
                "FAILED",


            "error":
                str(e)

        }