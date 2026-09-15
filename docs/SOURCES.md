# Configured Sources

All sources live in `backend/app/etl/sources.py`. Each entry needs to be
registered in `database/002_seed.sql` too (matching `code`), or the
pipeline will silently skip it — `run_pipeline()` only crawls a source
it can find by code in the `opportunity_sources` table.

| Code | Publisher | Covers | Listing page |
|---|---|---|---|
| PCIEERD | DOST-PCIEERD | Grants, calls for proposals | pcieerd.dost.gov.ph/work-with-us |
| PCHRD | DOST-PCHRD | Health research grants, calls | pchrd.dost.gov.ph/calls_and_events |
| PCAARRD | DOST-PCAARRD | Grants, calls, startup grant fund | pcaarrd.dost.gov.ph (QID articles) |
| NRCP | National Research Council of the Philippines | Basic research grants-in-aid | nrcp.dost.gov.ph |
| CHED | Commission on Higher Education | Scholarships, memorandum orders | legacy.ched.gov.ph/issuances |
| SEI | DOST Science Education Institute | Scholarships | sei.dost.gov.ph |
| STARTUPGOVPH | Startup Innovations Portal (DICT) | Startup grants & challenges | startup.gov.ph |
| TAPI | DOST-TAPI Technology Transfer | Spin-offs, tech transfer, commercialization | tapitechtransfer.dost.gov.ph/news-archive |
| ACM | Association for Computing Machinery | Calls for papers, conferences | acm.org/conferences |
| WIKICFP | WikiCFP | Calls for papers (all fields) | wikicfp.com/cfp |

## Why there's no Facebook / social media source

It was asked for, and deliberately left out. Two independent reasons,
either one would be disqualifying on its own:

1. **It's against the platform's rules.** Facebook's Terms of Service
   prohibit automated scraping, and its search results require a
   logged-in session — there's no way to add it here without either
   violating that policy or wiring a personal login into a university
   system. Neither is something to build into shared infrastructure.
2. **It's not technically reachable by this pipeline anyway.** The ETL
   is a plain HTTP client (`requests` + BeautifulSoup) — no browser, no
   JavaScript execution. Facebook's search UI is a client-rendered app
   that returns nothing useful to a plain GET request even when logged
   in.

If a call for papers, grant, or startup challenge is *only* ever posted
on social media, the fix that actually scales is asking the organizer
to also list it somewhere crawlable — most legitimate ones already do,
on their own site, on `startup.gov.ph`, or on WikiCFP for CFPs. Adding
a source below is then a five-line change.

## Adding a new source

```python
{
    "code": "SOMEAGENCY",
    "name": "Some Agency",
    "listing_url": "https://example.gov.ph/announcements/",
    "keywords": ["grant", "call for proposal"],  # matched against link text
},
```

Rules of thumb before adding one:

- It must be a public page reachable with a plain GET (view source in
  your browser — if the announcements only appear after the page runs
  JavaScript, this ETL won't see them).
- `keywords` filters which same-host links get followed by matching
  their visible link text. Leave it `[]` only for a page that is
  *entirely* about one topic already (like a CFP aggregator's category
  page) — otherwise you'll pull in every nav/footer link on the site.
- Add the matching row to `database/002_seed.sql` with the same `code`.
- Run `POST /api/pipeline/run` (or `python -m app.etl.run_once`) and
  check `pipeline_runs.discovered_count` — zero usually means the
  `keywords` list doesn't match how that site phrases its links, not
  that the pipeline is broken.
