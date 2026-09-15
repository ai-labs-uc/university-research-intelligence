# Recommended Next Steps

After Simple v1 runs successfully:

## Phase 2

1. ~~Add authentication~~ — done, see `docs/AUTH.md` (email/password +
   Google sign-in). Still open from this item: a researcher profile
   editor, password reset, email verification, and role-gated
   admin endpoints (role is stored per user but nothing checks it yet).
2. Add a Google Forms → FastAPI researcher/project intake endpoint.
3. Add email alerts (e.g. a small script run alongside the ETL job).
4. Add more official source adapters.
5. Improve deadline/eligibility extraction.
6. Add conference/indexing verification.
7. Add administrator source management UI.
8. Expand the keyword lists in `backend/app/etl/classifier.py`, or
   swap in a real NLP/AI classifier later without changing the schema.

## Phase 3

1. ORCID/Scopus publication import where permitted.
2. Vector embeddings / semantic search if scale requires it.
3. University SSO/LDAP.
4. Production deployment on Ubuntu.
5. Nginx + HTTPS.
6. Backup and monitoring.
7. Move the scheduled ETL run from cron/Task Scheduler to a proper job
   runner if you need retries, alerting, or a run history UI.
