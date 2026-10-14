# UC Research Registry

The Research Registry adds institutional research records to the existing
opportunities platform. It is intentionally separate from the ETL pipeline:
research records are created and maintained by authorized UC users, while
calls for papers and grants continue to be collected from configured sources.

## What it supports

- Create, search, update, and soft-delete research records for faculty,
  non-teaching staff, students, and other authorized users.
- Record ongoing or completed work, keywords, SDGs, researchers, college or
  unit, funding source, milestones, target dates, outputs, and progress.
- Upload a PDF, DOC, or DOCX research document up to 10 MB. Attachments are
  stored in MongoDB GridFS rather than local Render disk.
- Match a research record to live calls for papers and grants using transparent
  keyword overlap. Every match is labelled as a national or international
  grant / call for papers, and displays the matching terms and deadline cue.
- View and print a selected research record, including its metadata, progress,
  and matching opportunities.
- Show a role-aware progress summary for total, ongoing, completed, due-soon,
  and overdue records, plus a printable analytics report by status,
  researcher group, college or unit, and research start year.

## Access and governance

- A record owner may manage their own research records and attachments.
- `ADMIN` and `RESEARCH_OFFICE` users may manage and validate all records.
- `INSTITUTIONAL` records are visible to signed-in users; `RESTRICTED` records
  are visible only to their owner and Research Office administrators.
- Deletion is a soft delete so ordinary views no longer show the record while
  an approved retention process can govern eventual disposal.
- Recommendations are advisory. They do not rate researchers or make funding,
  promotion, ethics, or eligibility decisions.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| GET /api/research | Search and list visible records |
| POST /api/research | Create a record |
| GET/PUT/DELETE /api/research/{id} | View, update, or soft-delete a record |
| POST /api/research/{id}/progress | Add a documented progress update |
| POST /api/research/{id}/validate | Research Office validation |
| GET /api/research/{id}/recommendations | Explainable call-for-paper / grant matches |
| GET /api/research/analytics | Printable, role-aware registry analytics |
| GET/POST /api/research/{id}/attachments | List or upload an attachment |
| GET/DELETE /api/research/{id}/attachments/{attachment_id} | Download or delete an attachment |
| GET /api/research/dashboard | Progress monitoring summary |

Before production rollout, the Research Office should approve the metadata
dictionary, retention period, access classifications, document-upload policy,
and the user roles assigned in MongoDB.
