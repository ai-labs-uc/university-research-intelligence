from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi import Depends, APIRouter

from app.db import get_db


router = APIRouter()



# ============================================================
# ALL OPPORTUNITIES
# ============================================================

@router.get("/opportunities")
def opportunities(
    db: Session = Depends(get_db)
):

    result = db.execute(
        text(
        """

        SELECT

            o.*,

            COALESCE(
                s.name,
                o.organization
            ) AS source_name


        FROM research_opportunities o


        LEFT JOIN opportunity_sources s

        ON s.id = o.source_id


        WHERE

            o.is_current = 1


        ORDER BY

            o.id DESC


        LIMIT 500


        """
        )
    )


    return result.mappings().all()





# ============================================================
# GRANTS
# ============================================================

@router.get("/grants")
def grants(
    db: Session = Depends(get_db)
):


    result = db.execute(
        text(
        """

        SELECT

            o.*,

            COALESCE(
                s.name,
                o.organization
            ) AS source_name


        FROM research_opportunities o


        LEFT JOIN opportunity_sources s

        ON s.id=o.source_id


        WHERE


            o.is_current = 1

            AND o.category LIKE 'GRANT%'


        ORDER BY

            o.id DESC


        LIMIT 500


        """
        )
    )


    return result.mappings().all()





# ============================================================
# CALL FOR PAPERS
# ============================================================

@router.get("/call-for-papers")
def call_for_papers(
    scope: str = None,
    db: Session = Depends(get_db)
):


    if scope:


        category = (
            "CALL_FOR_PAPER_" 
            + scope.upper()
        )


        result = db.execute(
            text(
            """

            SELECT

                o.*,

                COALESCE(
                    s.name,
                    o.organization
                ) AS source_name


            FROM research_opportunities o


            LEFT JOIN opportunity_sources s

            ON s.id=o.source_id


            WHERE


                o.is_current = 1


                AND o.category = :category


            ORDER BY

                o.id DESC


            LIMIT 500


            """
            ),

            {
                "category": category
            }

        )


    else:


        result = db.execute(
            text(
            """

            SELECT

                o.*,

                COALESCE(
                    s.name,
                    o.organization
                ) AS source_name


            FROM research_opportunities o


            LEFT JOIN opportunity_sources s

            ON s.id=o.source_id


            WHERE


                o.is_current = 1


                AND o.category LIKE
                'CALL_FOR_PAPER%'


            ORDER BY

                o.id DESC


            LIMIT 500


            """
            )
        )



    return result.mappings().all()