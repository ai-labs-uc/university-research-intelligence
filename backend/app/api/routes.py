@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    total = db.execute(
        text(
        """
        SELECT COUNT(*)
        FROM research_opportunities
        """
        )
    ).scalar()



    grants = db.execute(
        text(
        """
        SELECT COUNT(*)
        FROM research_opportunities
        WHERE category LIKE 'GRANT%'
        """
        )
    ).scalar()



    national = db.execute(
        text(
        """
        SELECT COUNT(*)
        FROM research_opportunities
        WHERE category='CALL_FOR_PAPER_NATIONAL'
        """
        )
    ).scalar()



    international = db.execute(
        text(
        """
        SELECT COUNT(*)
        FROM research_opportunities
        WHERE category='CALL_FOR_PAPER_INTERNATIONAL'
        """
        )
    ).scalar()



    return {

        "total_opportunities": total,

        "grants": grants,

        "national_call_for_papers": national,

        "international_call_for_papers": international

    }