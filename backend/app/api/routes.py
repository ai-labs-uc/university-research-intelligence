import json
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.pipeline_service import run_pipeline

# dependencies=[...] applies to every route below — everything except
# /health and /api/auth/* (registered on their own router in
# auth_routes.py) requires a valid session token. See docs/AUTH.md.
router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.execute(
        text("SELECT COUNT(*) FROM research_opportunities")
    ).scalar_one()

    open_count = db.execute(
        text("SELECT COUNT(*) FROM research_opportunities WHERE status='OPEN'")
    ).scalar_one()

    call_for_paper_count = db.execute(text('''
        SELECT COUNT(*) FROM research_opportunities
        WHERE category LIKE 'CALL_FOR_PAPER%'
    ''')).scalar_one()

    grant_count = db.execute(text('''
        SELECT COUNT(*) FROM research_opportunities
        WHERE category LIKE 'GRANT%'
    ''')).scalar_one()

    active_sources = db.execute(
        text("SELECT COUNT(*) FROM opportunity_sources WHERE enabled=TRUE")
    ).scalar_one()

    return {
        "total_opportunities": total,
        "open_opportunities": open_count,
        "call_for_paper_count": call_for_paper_count,
        "grant_count": grant_count,
        "active_sources": active_sources,
    }

@router.get("/opportunities")
def opportunities(
    db: Session = Depends(get_db)
):

    result = db.execute(text("""
    
    SELECT
        o.*,
        s.name AS source_name

    FROM research_opportunities o

    LEFT JOIN opportunity_sources s

    ON s.id=o.source_id


    WHERE

    (
        o.opportunity_type != 'GRANT'
    )

    OR

    (
        o.opportunity_type='GRANT'
        AND o.deadline >= CURDATE()
    )


    ORDER BY o.id DESC

    LIMIT 500

    """))

    return result.mappings().all()

@router.get("/sources")
def sources(db: Session = Depends(get_db)):
    return [
        dict(row)
        for row in db.execute(
            text("SELECT * FROM opportunity_sources ORDER BY name")
        ).mappings().all()
    ]

@router.post("/pipeline/run")
def pipeline(db: Session = Depends(get_db)):
    return run_pipeline(db)


@router.get("/grants")
def grants(
    db: Session = Depends(get_db)
):

    result=db.execute(text("""

    SELECT *

    FROM research_opportunities

    WHERE opportunity_type='GRANT'

    AND deadline >= CURDATE()

    ORDER BY deadline ASC

    """))

    return result.mappings().all()


@router.get("/call-for-papers")
def call_for_papers(
    scope:str=None,
    db:Session=Depends(get_db)
):


    query="""

    SELECT *

    FROM research_opportunities

    WHERE opportunity_type LIKE 'CALL_FOR_PAPER%'

    """


    params={}


    if scope:

        query += """
        AND opportunity_type=:scope
        """

        params["scope"] = (
            "CALL_FOR_PAPER_"+scope
        )


    query += """

    ORDER BY deadline ASC

    """


    result=db.execute(
        text(query),
        params
    )


    return result.mappings().all()