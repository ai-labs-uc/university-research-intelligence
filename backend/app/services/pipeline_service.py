import json
from datetime import datetime
from sqlalchemy import text

from app.etl.sources import enabled_default_sources
from app.etl.collector import discover_links, fetch_page
from app.etl.utils import canonicalize_url, make_hash
from app.etl.classifier import classify_type, detect_indexing, extract_topics

def run_pipeline(db):
    run_id = db.execute(
        text("INSERT INTO pipeline_runs(status) VALUES('RUNNING')")
    ).lastrowid

    discovered = inserted = updated = classified = skipped = 0

    try:
        source_rows = {
            row["code"]: row["id"]
            for row in db.execute(
                text("SELECT id,code FROM opportunity_sources")
            ).mappings().all()
        }

        for source in enabled_default_sources():
            source_id = source_rows.get(source["code"])
            if not source_id:
                continue

            try:
                urls = discover_links(source)
                discovered += len(urls)
            except Exception:
                urls = []

            for url in urls[:20]:
                try:
                    title, raw_text = fetch_page(url)
                    canonical = canonicalize_url(url)
                    content_hash = make_hash(
                        canonical,
                        title,
                    )

                    existing = db.execute(text('''
                        SELECT id
                        FROM research_opportunities
                        WHERE content_hash=:h
                    '''), {"h": content_hash}).scalar()

                    combined_text = f"{title}\n{raw_text}"
                    opportunity_type = classify_type(combined_text)

                    # Out of scope — this system only tracks calls for
                    # papers and grants now (see docs/ARCHITECTURE.md).
                    # Skip rather than mis-labeling it as one or the other.
                    if opportunity_type is None:
                        skipped += 1
                        continue

                    topics = extract_topics(combined_text)
                    indexing_flags = detect_indexing(combined_text)
                    classified += 1

                    payload = {
                        "source_id": source_id,
                        "type": opportunity_type,
                        "title": title,
                        "summary": raw_text[:1000],
                        "source_url": url,
                        "canonical": canonical,
                        "hash": content_hash,
                        "topics": json.dumps(topics),
                        "indexing_flags": json.dumps(indexing_flags),
                    }

                    if existing:
                        payload["id"] = existing
                        db.execute(text('''
                            UPDATE research_opportunities
                            SET
                                opportunity_type=:type,
                                title=:title,
                                summary=:summary,
                                source_url=:source_url,
                                canonical_url=:canonical,
                                topics=:topics,
                                indexing_flags=:indexing_flags,
                                updated_at=NOW()
                            WHERE id=:id
                        '''), payload)
                        updated += 1
                    else:
                        db.execute(text('''
                            INSERT INTO research_opportunities
                            (
                                source_id,
                                opportunity_type,
                                title,
                                summary,
                                source_url,
                                canonical_url,
                                content_hash,
                                status,
                                topics,
                                indexing_flags,
                                verification_status
                            )
                            VALUES
                            (
                                :source_id,
                                :type,
                                :title,
                                :summary,
                                :source_url,
                                :canonical,
                                :hash,
                                'UNKNOWN',
                                :topics,
                                :indexing_flags,
                                'UNVERIFIED'
                            )
                        '''), payload)
                        inserted += 1

                    db.commit()

                except Exception:
                    db.rollback()

        db.execute(text('''
            UPDATE pipeline_runs
            SET
                finished_at=NOW(),
                status='SUCCESS',
                discovered_count=:d,
                inserted_count=:i,
                updated_count=:u,
                classified_count=:c,
                skipped_count=:s
            WHERE id=:id
        '''), {
            "d": discovered,
            "i": inserted,
            "u": updated,
            "c": classified,
            "s": skipped,
            "id": run_id,
        })
        db.commit()

        return {
            "run_id": run_id,
            "status": "SUCCESS",
            "discovered": discovered,
            "inserted": inserted,
            "updated": updated,
            "classified": classified,
            "skipped_out_of_scope": skipped,
        }

    except Exception as exc:
        db.rollback()
        db.execute(text('''
            UPDATE pipeline_runs
            SET
                finished_at=NOW(),
                status='FAILED',
                error_message=:error
            WHERE id=:id
        '''), {
            "id": run_id,
            "error": str(exc)[:2000],
        })
        db.commit()
        raise
