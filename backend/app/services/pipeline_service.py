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



def generate_hash(url):

    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()



def run_pipeline(db):

    started = datetime.utcnow()

    discovered = 0
    inserted = 0


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
                    "Source error:",
                    e
                )

                continue



            for url in links:


                try:

                    title, content = fetch_page(url)

                except Exception as e:

                    print(
                        "Fetch error:",
                        e
                    )

                    continue



                discovered += 1



                text_content = (
                    title
                    +
                    " "
                    +
                    content
                )



                opportunity_type = classify_type(
                    text_content
                )


                if opportunity_type is None:

                    continue



                now = datetime.utcnow()



                db.execute(
                    text(
                    """

                    INSERT INTO research_opportunities

                    (
                        opportunity_type,
                        scope_type,
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
                        :title,
                        :org,
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

                    """
                    ),
                    {

                    "type":
                        opportunity_type,


                    "scope":
                        opportunity_type,


                    "title":
                        title,


                    "org":
                        source.get("name"),


                    "summary":
                        content[:3000],


                    "url":
                        url,


                    "canonical":
                        url,


                    "hash":
                        generate_hash(url),


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



        return {

            "status":
                "SUCCESS",

            "discovered":
                discovered,

            "inserted":
                inserted

        }



    except Exception as e:


        db.rollback()


        return {

            "status":
                "FAILED",

            "error":
                str(e)

        }