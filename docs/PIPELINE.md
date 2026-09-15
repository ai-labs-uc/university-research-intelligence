# Research Opportunity Pipeline

```text
STEP 1
Triggered manually, from the dashboard, or by a scheduled task
(cron / Task Scheduler running `python -m app.etl.run_once`)
    ↓

STEP 2
Python checks configured official sources
    ↓

STEP 3
Discover likely opportunity URLs
    ↓

STEP 4
Download source page
    ↓

STEP 5
Normalize URL + create hash
    ↓

STEP 6
Rule-based classification:
- classify as CALL_FOR_PAPER, GRANT, or out of scope
- out-of-scope items are skipped — not stored
- extract topic keywords
- detect Scopus/WoS/other indexing phrases, if literally present
    ↓

STEP 7
Store/update MySQL
    ↓

STEP 8
React dashboard displays results, with Call for Papers / Grants tabs
and indexing badges
```

## Critical rule

The classifier (`backend/app/etl/classifier.py`) is allowed to:

```text
assign a type from the scraped title/text (keyword match)
extract topic keywords already present in the scraped text
detect an indexing/database label (Scopus, Web of Science, etc.) only
  when that literal phrase appears in the scraped text
```

It must NOT invent:

```text
deadline
eligibility
funding amount
an indexing status the source page never stated
official requirements
```

`detect_indexing()` (see `docs/PIPELINE.md#indexing-detection` below)
never infers an index from a journal's name or reputation — only from
the words actually on the page, and an empty result means "not stated
on the source page," not "not indexed." Those facts must come from the
source, exactly as before — the only thing that changed is that
classification is done with a keyword list instead of a call to an
external AI model.

## Indexing detection

`detect_indexing(text)` scans the same combined title+page text used
for `classify_type()`/`extract_topics()` and returns every label whose
literal phrasing it finds: `SCOPUS`, `WEB_OF_SCIENCE` (also matches
"Clarivate", "ISI-indexed", "Science Citation Index"),
`ASEAN_CITATION_INDEX`, `PUBMED`, `IEEE_XPLORE`, `DOAJ`,
`CHED_ACCREDITED`, `PEER_REVIEWED`. A call for papers can carry more
than one (a journal can be both Scopus- and WoS-indexed), so every match
is kept rather than picking the first. Results are stored as JSON in
`research_opportunities.indexing_flags` and surfaced as badges on the
Opportunities page. Extend `INDEXING_KEYWORDS` in `classifier.py` the
same way you'd extend `TYPE_KEYWORDS` — add a phrase, it applies on the
next pipeline run.

## Scope: why some discovered items never appear

`classify_type()` only recognizes two categories now — `CALL_FOR_PAPER`
and `GRANT` (see `TYPE_KEYWORDS` in `classifier.py`) — and returns
`None` for anything else. `run_pipeline()` in `pipeline_service.py`
skips inserting those items entirely rather than mis-labeling a
conference, fellowship, scholarship, startup challenge, training, or
collaboration opportunity as one of the two remaining types. The
skipped count is recorded per run in `pipeline_runs.skipped_count`.
This system previously also matched opportunities against academic
units (colleges/programs) and individual researcher profiles; both were
removed as the system's focus narrowed to just calls for papers and
grants — see `database/ERD.md`.
