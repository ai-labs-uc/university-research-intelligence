from datetime import datetime
import hashlib

from sqlalchemy import text

from app.etl.collector import (
    discover_links,
    fetch_page
)

from app.etl.sources import (
    enabled_default_sources,
    INTERNATIONAL_CFP_SOURCES
)

from app.etl.classifier import classify_type



def make_hash(url):

    return hashlib.sha256(
        url.encode()
    ).hexdigest()



def category(type_value):

    if type_value == "GRANT":

        return "GRANT_PHILIPPINES"


    if type_value == "CALL_FOR_PAPER_NATIONAL":

        return "CALL_FOR_PAPER_NATIONAL"


    if type_value == "CALL_FOR_PAPER_INTERNATIONAL":

        return "CALL_FOR_PAPER_INTERNATIONAL"


    return "OTHER"




def run_pipeline(db):


    sources = (
        enabled_default_sources()
        +
        INTERNATIONAL_CFP_SOURCES
    )


    inserted = 0


    for source in sources:


        source_name = source.get(
            "name",
            ""
        )


        try:

            links = discover_links(
                source
            )


        except Exception as e:

            print(
                "SOURCE ERROR",
                e
            )

            continue




        for url in links[:20]:


            try:

                title, content = fetch_page(
                    url
                )


            except Exception:

                continue



            if not title:

                continue



            result = classify_type(

                title,

                content,

                source_name

            )



            if not result:

                continue



            cat = category(
                result
            )



            now = datetime.utcnow()



            db.execute(

                text("""

                INSERT INTO research_opportunities

                (

                opportunity_type,

                scope_type,

                category,

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

                :category,

                :title,

                :organization,

                :summary,

                :url,

                :url,

                :hash,

                'OPEN',

                'UNVERIFIED',

                1,

                :now,

                :now,

                :now

                )


                ON DUPLICATE KEY UPDATE

                category =
                VALUES(category),

                updated_at =
                VALUES(updated_at)

                """),

                {

                "type": result,

                "scope": result,

                "category": cat,

                "title": title,

                "organization": source_name,

                "summary": content[:3000],

                "url": url,

                "hash": make_hash(url),

                "now": now

                }

            )


            inserted += 1



        db.commit()



    return {

        "status":"SUCCESS",

        "inserted":inserted

    }