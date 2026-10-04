# University Research Call for Paper Opportunity and Grants & Automation Platform — Simple v1

A simplified university research opportunity platform built around one clear idea:

```text
Python  = ENGINE
MongoDB = SYSTEM OF RECORD
React   = USER INTERFACE
```

## What it does

The system's scope is deliberately narrow: two kinds of opportunity,
tracked well, rather than many kinds tracked shallowly.

- Grants
- Calls for Papers

Sixteen sources are configured and enabled out of the box — nine
Philippine government agencies (DOST-PCIEERD, DOST-PCHRD, DOST-PCAARRD,
the National Research Council of the Philippines, DOST itself, the
DA Bureau of Agricultural Research, the Department of Agriculture, the
DENR, and CHED), four Philippine academic/CFP sources (UP-CIDS, UP,
the Philippine Social Science Council, and Philippine OJS journals),
and three international sources (MDPI, Springer Nature, and UK
Research and Innovation) — scanned for grant funding calls and calls
for papers/publication. Two more sources (WikiCFP, IEEE Author Center)
are defined in code but currently disabled. Anything a source publishes
outside those two categories (conferences, fellowships, scholarships,
startup challenges, etc.) is discovered but deliberately left out of
the system — see `docs/PIPELINE.md`. The authoritative, current source
list lives in `backend/app/etl/sources.py`; see `docs/SOURCES.md` for
background on how to add another one (and why social media search
isn't, and won't be, one of them).

It can:

1. Collect opportunities from configured sources.
2. Normalize and store them in MongoDB.
3. Classify each opportunity as a call for papers or a grant (or skip
it as out of scope), pull out topic keywords, and detect Scopus/Web
of Science/other indexing labels — all with plain rule-based
matching (no external AI service required). See `docs/PIPELINE.md`.
4. Expose everything through FastAPI, behind real login — email/password
or Google sign-in. See `docs/AUTH.md`.
5. Display calls for papers, grants, and source status in React, with
tabs to switch between the two.

## Simplified architecture

```text
Sources
↓
Python ETL (run manually, via the API, or on a schedule with cron/a Render Cron Job)
↓
Classifier (call for paper / grant / out of scope)
↓
MongoDB (Atlas)
↓
FastAPI
↓
React + Tailwind
↓
Researchers / Research Office
```

## Main folders

```text
backend/  FastAPI, ETL, classification
frontend/ React + Vite + Tailwind
database/ MongoDB reference/demo seed data (seed.js)
docs/     installation and operating guides
```

Start with:

```text
docs/BEGINNER_SETUP.md
```
