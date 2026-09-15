# Simplified Database Relationship Map

```text
users
  │
  └── researchers
        │
        └── research_projects

opportunity_sources
  │
  └── research_opportunities

pipeline_runs
  └── logs each automation cycle
```

## Core tables

- `users` — login (email/password and/or Google — `password_hash` and
  `google_sub` are each nullable, a row can have one or both) and role.
  See `docs/AUTH.md`.
- `researchers` — researcher profile (kept as a directory for future
  use — e.g. Phase 2's researcher profile editor in
  `docs/NEXT_STEPS.md` — but nothing currently matches opportunities
  against it; see "Why there's no matching engine" below)
- `research_projects` — active research/project ideas
- `opportunity_sources` — agencies/publishers/sites
- `research_opportunities` — grants and calls for papers only
  (`opportunity_type ENUM('GRANT','CALL_FOR_PAPER')`). Carries
  `indexing_flags` (JSON array such as `["SCOPUS"]`) detected from the
  source page text for calls for papers/publication.
- `pipeline_runs` — automation audit/history, including `skipped_count`
  (items discovered but classified as neither a grant nor a call for
  papers, so left out of `research_opportunities` entirely)

## Why the system's scope is grants + calls for papers only

The system originally tracked eleven opportunity types (grants, calls
for proposals, calls for papers, conferences, journal special issues,
fellowships, scholarships, research competitions, startup challenges,
collaboration opportunities, training). The scope was deliberately
narrowed to two — `GRANT` and `CALL_FOR_PAPER` — to match what the
research office actually asked this system to track. "Call for
proposal" and "special issue" phrasing now fold into `GRANT` and
`CALL_FOR_PAPER` respectively rather than getting their own category,
since both are, in substance, the same thing under another name; the
other eight types are simply out of scope — `classify_type()` returns
`None` for them and the pipeline skips ingesting the item (see
`docs/PIPELINE.md`). `database/005_remove_programs_narrow_scope.sql` is
the migration that narrows an existing installation's
`opportunity_type` column and deletes any rows outside the two
remaining categories.

## Why there's no matching engine

Two matching mechanisms existed at different points, and both were
removed.

An earlier version matched opportunities to individual researcher
profiles (`opportunity_matches`) and raised per-researcher `alerts`
above a score threshold. Both were removed: the UI had nowhere to pick
which researcher you were (it hardcoded one demo profile), which made
that page redundant with what Opportunities already showed.

A later version added college/program-level matching instead —
`academic_units` and `opportunity_program_matches`, scored with a
token-overlap engine, surfaced on a dedicated Programs page. That was
also removed once the system's scope narrowed to grants and calls for
papers only: with just two categories and a research office reading the
list directly, a separate scored-matching view stopped earning its
keep, and `database/005_remove_programs_narrow_scope.sql` drops both
tables on an existing installation.

If matching is wanted again later — either kind — `researchers` is
still there to match against, real login now exists (`docs/AUTH.md`,
which was the missing piece for researcher-level matching to work this
time), and the token-overlap approach used by both earlier attempts —
a `tokens()`/`score_match()`/`band()` scorer, last living in the
now-deleted `matching_service.py` — is a reasonable starting point to
rebuild from if a copy of it was kept before removal.
