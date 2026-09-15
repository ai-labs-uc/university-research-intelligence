# University Research Call for Paper Opportunity and Grants & Automation Platform — Simple v1

A simplified university research opportunity platform built around one clear idea:

```text
Python = ENGINE
MySQL  = SYSTEM OF RECORD
React  = USER INTERFACE
```

## What it does

The system's scope is deliberately narrow: two kinds of opportunity,
tracked well, rather than many kinds tracked shallowly.

- Grants
- Calls for Papers

Ten sources are configured out of the box — DOST-PCIEERD, DOST-PCHRD,
DOST-PCAARRD, the National Research Council of the Philippines, CHED,
DOST-SEI, the official Startup Innovations Portal, DOST-TAPI Technology
Transfer, ACM, and WikiCFP — scanned for grant funding calls and calls
for papers/publication. Anything a source publishes outside those two
categories (conferences, fellowships, scholarships, startup challenges,
etc.) is discovered but deliberately left out of the system — see
`docs/PIPELINE.md`. See `docs/SOURCES.md` for the full source list and
how to add another one (and why social media search isn't, and won't
be, one of them).

It can:

1. Collect opportunities from configured sources.
2. Normalize and store them in MySQL.
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
Python ETL (run manually, via the API, or on a schedule with cron/Task Scheduler)
  ↓
Classifier (call for paper / grant / out of scope)
  ↓
MySQL
  ↓
FastAPI
  ↓
React + Tailwind
  ↓
Researchers / Research Office
```

## Main folders

```text
backend/     FastAPI, ETL, classification
frontend/    React + Vite + Tailwind
database/    MySQL schema + seed
docs/        installation and operating guides
```

Start with:

```text
docs/BEGINNER_SETUP.md
```
