/**
 * seed.js — reference/demo data for the MongoDB Atlas database behind
 * "University Research Call for Paper Opportunity and Grants".
 *
 * Run with mongosh, pointed at your Atlas connection string (the same
 * MONGODB_URI used by the backend — it already includes the database
 * name, so no `use <db>` is needed):
 *
 *   mongosh "mongodb+srv://USER:PASSWORD@cluster0.lxatequ.mongodb.net/research_intelligence?retryWrites=true&w=majority&appName=Cluster0" database/seed.js
 *
 * WHY THIS EXISTS
 * ----------------
 * The old MySQL database/002_seed.sql only seeded `opportunity_sources`
 * (the list of sites the scraper reads). That list now lives in code
 * (backend/app/etl/sources.py) — the pipeline doesn't need a database
 * row to know what to scrape, so there is nothing to migrate there.
 *
 * This script instead seeds the things that are genuinely useful to
 * have in a fresh database before you've run the ETL pipeline or
 * registered through the UI:
 *
 *   1. One demo login user, so you can sign in immediately without
 *      going through /register.
 *   2. A handful of sample research_opportunities across both
 *      categories (grants / calls for papers), both scopes (national /
 *      international), and a mix of deadlines — some soon, one already
 *      expired — so the dashboard, opportunity lists, and deadline
 *      notifications all have something to show.
 *   3. opportunity_sources rows mirroring the current source list in
 *      app/etl/sources.py, with last_checked_at left unset — exactly
 *      the state a brand-new database is in before the pipeline has
 *      run for the first time.
 *
 * SAFETY / IDEMPOTENCY
 * ---------------------
 * Every insert here is an upsert keyed on a natural field (email,
 * content_hash, or source code), not a hardcoded _id collision, so
 * running this script more than once will not create duplicates or
 * throw errors. The `counters` collection (which the app's next_id()
 * helper reads) is advanced with $max rather than overwritten, so this
 * is also safe to run after real users/opportunities already exist.
 *
 * IMPORTANT — DEMO CREDENTIAL
 * -----------------------------
 * The seeded account's password is plaintext right here in version
 * control (demo.tester@uc-bcf.edu.ph / ChangeMe123!). That's fine for
 * a local/testing database, but if this script is ever run against a
 * database other people can reach, change the password immediately
 * after logging in once, or delete the account from `users` entirely.
 */

const now = new Date();

function upsert(collectionName, filter, doc) {
  db[collectionName].updateOne(
    filter,
    { $setOnInsert: doc },
    { upsert: true }
  );
}

function bumpCounter(sequenceName, atLeast) {
  db.counters.updateOne(
    { _id: sequenceName },
    { $max: { seq: atLeast } },
    { upsert: true }
  );
}

// ------------------------------------------------------------------
// 1. Demo login user
// ------------------------------------------------------------------
// Password: ChangeMe123!  (bcrypt hash below, cost factor 12 — same
// scheme app/core/security.py uses, so it verifies with the real app.)
const DEMO_USER_ID = 1;

upsert(
  "users",
  { email: "demo.tester@uc-bcf.edu.ph" },
  {
    _id: DEMO_USER_ID,
    name: "Demo Tester",
    email: "demo.tester@uc-bcf.edu.ph",
    password_hash: "$2b$12$IyQjgD1kgr4vXoT4RaQ8Qe7H2WthnSFB8Px2lz.ffRaWbVZ4GcPty",
    google_sub: null,
    role: "RESEARCHER",
    active: true,
    last_login_at: null,
    created_at: now,
  }
);
bumpCounter("users", DEMO_USER_ID);

print("Seeded demo user: demo.tester@uc-bcf.edu.ph / ChangeMe123!");

// ------------------------------------------------------------------
// 2. Sample research opportunities
// ------------------------------------------------------------------
// Dates are relative to when this script runs isn't practical in a
// static file, so they're fixed calendar dates near "today" as of
// when this was written (Oct 2026). Adjust freely — what matters for
// testing is the mix: some open with near deadlines (to exercise the
// 30/14/7/3/1-day alert thresholds), one with a far-off deadline, and
// one already closed.
const opportunities = [
  {
    content_hash: "seed-pcieerd-grant-2026",
    opportunity_type: "GRANT",
    scope_type: "NATIONAL",
    category: "GRANT_PHILIPPINES",
    title: "[SEED DATA] DOST-PCIEERD Research Grant Call",
    organization: "DOST-PCIEERD",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://pcieerd.dost.gov.ph/ for actual postings.",
    country: "Philippines",
    currency: null,
    opening_date: new Date("2026-09-01T00:00:00Z"),
    deadline: new Date("2026-10-09T00:00:00Z"),
    source_url: "https://pcieerd.dost.gov.ph/work-with-us/",
    canonical_url: "https://pcieerd.dost.gov.ph/work-with-us/",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: null,
    is_current: true,
  },
  {
    content_hash: "seed-pchrd-grant-2026",
    opportunity_type: "GRANT",
    scope_type: "NATIONAL",
    category: "GRANT_PHILIPPINES",
    title: "[SEED DATA] DOST-PCHRD Health Research Grant",
    organization: "DOST-PCHRD",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://www.pchrd.dost.gov.ph/ for actual postings.",
    country: "Philippines",
    currency: null,
    opening_date: new Date("2026-09-10T00:00:00Z"),
    deadline: new Date("2026-10-24T00:00:00Z"),
    source_url: "https://www.pchrd.dost.gov.ph/calls_and_events/",
    canonical_url: "https://www.pchrd.dost.gov.ph/calls_and_events/",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: null,
    is_current: true,
  },
  {
    content_hash: "seed-nrcp-grant-2026",
    opportunity_type: "GRANT",
    scope_type: "NATIONAL",
    category: "GRANT_PHILIPPINES",
    title: "[SEED DATA] National Research Council Grants-in-Aid Program",
    organization: "National Research Council of the Philippines",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://nrcp.dost.gov.ph/ for actual postings.",
    country: "Philippines",
    currency: null,
    opening_date: new Date("2026-09-01T00:00:00Z"),
    deadline: new Date("2026-11-18T00:00:00Z"),
    source_url: "https://nrcp.dost.gov.ph/news-and-updates/",
    canonical_url: "https://nrcp.dost.gov.ph/news-and-updates/",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: null,
    is_current: true,
  },
  {
    content_hash: "seed-mdpi-sustainability-2026",
    opportunity_type: "CALL_FOR_PAPER",
    scope_type: "INTERNATIONAL",
    category: "CALL_FOR_PAPER_INTERNATIONAL",
    title: "[SEED DATA] MDPI Sustainability — Special Issue Call for Papers",
    organization: "MDPI Special Issues",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://www.mdpi.com/journal/sustainability/special_issues for actual postings.",
    country: null,
    currency: null,
    opening_date: new Date("2026-09-15T00:00:00Z"),
    deadline: new Date("2026-10-14T00:00:00Z"),
    source_url: "https://www.mdpi.com/journal/sustainability/special_issues",
    canonical_url: "https://www.mdpi.com/journal/sustainability/special_issues",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: ["Scopus", "Web of Science"],
    is_current: true,
  },
  {
    content_hash: "seed-springer-collection-2026",
    opportunity_type: "CALL_FOR_PAPER",
    scope_type: "INTERNATIONAL",
    category: "CALL_FOR_PAPER_INTERNATIONAL",
    title: "[SEED DATA] Springer Nature Collection — Call for Submissions",
    organization: "Springer Nature Collections",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://link.springer.com/ for actual postings.",
    country: null,
    currency: null,
    opening_date: new Date("2026-09-20T00:00:00Z"),
    deadline: new Date("2026-11-03T00:00:00Z"),
    source_url: "https://link.springer.com/",
    canonical_url: "https://link.springer.com/",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: ["Scopus"],
    is_current: true,
  },
  {
    content_hash: "seed-ukri-grant-2026",
    opportunity_type: "GRANT",
    scope_type: "INTERNATIONAL",
    category: "GRANT_INTERNATIONAL",
    title: "[SEED DATA] UKRI Research Funding Opportunity",
    organization: "UK Research and Innovation",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://www.ukri.org/opportunity/ for actual postings.",
    country: null,
    currency: "GBP",
    opening_date: new Date("2026-09-01T00:00:00Z"),
    deadline: new Date("2026-12-03T00:00:00Z"),
    source_url: "https://www.ukri.org/opportunity/",
    canonical_url: "https://www.ukri.org/opportunity/",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: null,
    is_current: true,
  },
  {
    content_hash: "seed-upcids-cfp-2026",
    opportunity_type: "CALL_FOR_PAPER",
    scope_type: "NATIONAL",
    category: "CALL_FOR_PAPER_NATIONAL",
    title: "[SEED DATA] UP CIDS Call for Papers — Policy Studies",
    organization: "UP Center for Integrative and Development Studies",
    summary: "Placeholder opportunity inserted by seed.js for testing. Not a real, currently open call — check https://cids.up.edu.ph/ for actual postings.",
    country: "Philippines",
    currency: null,
    opening_date: new Date("2026-09-15T00:00:00Z"),
    deadline: new Date("2026-10-19T00:00:00Z"),
    source_url: "https://cids.up.edu.ph/",
    canonical_url: "https://cids.up.edu.ph/",
    status: "OPEN",
    verification_status: "UNVERIFIED",
    indexing_flags: null,
    is_current: true,
  },
  {
    content_hash: "seed-ched-grant-expired-2026",
    opportunity_type: "GRANT",
    scope_type: "NATIONAL",
    category: "GRANT_PHILIPPINES",
    title: "[SEED DATA] CHED Research Grant (expired example)",
    organization: "Commission on Higher Education",
    summary: "Placeholder opportunity inserted by seed.js for testing the CLOSED/expired display path. Not a real call.",
    country: "Philippines",
    currency: null,
    opening_date: new Date("2026-08-01T00:00:00Z"),
    deadline: new Date("2026-09-24T00:00:00Z"),
    source_url: "https://ovcre.uplb.edu.ph/announcements/",
    canonical_url: "https://ovcre.uplb.edu.ph/announcements/",
    status: "CLOSED",
    verification_status: "PARTIALLY_VERIFIED",
    indexing_flags: null,
    is_current: false,
  },
];

let nextOppId = 1;
opportunities.forEach((opp) => {
  const id = nextOppId++;
  upsert(
    "research_opportunities",
    { content_hash: opp.content_hash },
    Object.assign({ _id: id, discovered_at: now, last_seen: now, updated_at: now }, opp)
  );
});
bumpCounter("research_opportunities", opportunities.length);

print("Seeded " + opportunities.length + " sample research_opportunities.");

// ------------------------------------------------------------------
// 3. opportunity_sources — mirrors backend/app/etl/sources.py
// ------------------------------------------------------------------
// last_checked_at / last_status are left null: that's the real state
// of a fresh database before the pipeline has run even once. Once you
// trigger /api/pipeline/run (or the ETL cron job), these rows will be
// updated in place with real health data.
const sources = [
  { code: "PCIEERD", name: "DOST-PCIEERD", base_url: "https://pcieerd.dost.gov.ph/work-with-us/", source_type: "API", trust_level: "OFFICIAL_AGENCY" },
  { code: "NRCP", name: "National Research Council of the Philippines", base_url: "https://nrcp.dost.gov.ph/news-and-updates/", source_type: "RSS", trust_level: "OFFICIAL_AGENCY" },
  { code: "DOST", name: "Department of Science and Technology", base_url: "https://www.dost.gov.ph/23-announcements/", source_type: "RSS", trust_level: "OFFICIAL_AGENCY" },
  { code: "PCAARRD", name: "DOST-PCAARRD", base_url: "https://www.pcaarrd.dost.gov.ph/index.php/news-archive", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "PCHRD", name: "DOST-PCHRD", base_url: "https://www.pchrd.dost.gov.ph/calls_and_events/", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "DABAR", name: "DA-Bureau of Agricultural Research", base_url: "https://www.bar.gov.ph/media-resources/news-and-events", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "DA", name: "Department of Agriculture", base_url: "https://www.da.gov.ph/news/", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "DENR", name: "Department of Environment and Natural Resources", base_url: "https://denr.gov.ph/news-events/", source_type: "RSS", trust_level: "OFFICIAL_AGENCY" },
  { code: "CHED", name: "Commission on Higher Education", base_url: "https://ovcre.uplb.edu.ph/announcements/", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "UPCIDS", name: "UP Center for Integrative and Development Studies", base_url: "https://cids.up.edu.ph/", source_type: "RSS", trust_level: "OFFICIAL_AGENCY" },
  { code: "UPMAIN", name: "University of the Philippines", base_url: "https://up.edu.ph/", source_type: "RSS", trust_level: "OFFICIAL_AGENCY" },
  { code: "PSSC", name: "Philippine Social Science Council", base_url: "https://pssc.org.ph/latest-news-and-events/3/", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "OJS_PH", name: "Philippine OJS Journals", base_url: "https://phjlis.org/index.php/phjlis/announcement", source_type: "HTML", trust_level: "OFFICIAL_AGENCY" },
  { code: "MDPI", name: "MDPI Special Issues", base_url: "https://www.mdpi.com/", source_type: "HTML", trust_level: "OFFICIAL_PUBLISHER" },
  { code: "SPRINGER", name: "Springer Nature Collections", base_url: "https://link.springer.com/", source_type: "HTML", trust_level: "OFFICIAL_PUBLISHER" },
  { code: "UKRI", name: "UK Research and Innovation", base_url: "https://www.ukri.org/opportunity/?filter_order=closing_date", source_type: "HTML", trust_level: "OFFICIAL_PUBLISHER" },
];

let nextSourceId = 1;
sources.forEach((source) => {
  const id = nextSourceId++;
  upsert(
    "opportunity_sources",
    { code: source.code },
    Object.assign(
      {
        _id: id,
        enabled: true,
        last_checked_at: null,
        last_status: null,
        created_at: now,
      },
      source
    )
  );
});
bumpCounter("opportunity_sources", sources.length);

print("Seeded " + sources.length + " opportunity_sources rows.");

print("Done. Log in with demo.tester@uc-bcf.edu.ph / ChangeMe123!");
