-- Deliberately does NOT create or USE a database by name. Run this
-- against whichever database your connection is already pointed at
-- (see docs/BEGINNER_SETUP.md for a local install, or the hosting
-- guide for a managed database like Railway's, which assigns its own
-- database name that you don't control). Hardcoding a database name
-- here would silently create tables in the wrong place on any host
-- that doesn't name its database "research_intelligence".

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    -- NULL for a Google-only account (no local password ever set).
    password_hash VARCHAR(255) NULL,
    -- Google's stable per-account "sub" claim. NULL for a
    -- password-only account. A row can have both set if a
    -- password-registered user later signs in with Google on the same
    -- email (accounts are linked by email, not merged/duplicated).
    google_sub VARCHAR(255) NULL UNIQUE,
    role ENUM('RESEARCHER','RESEARCH_ADMIN','SYSTEM_ADMIN')
         NOT NULL DEFAULT 'RESEARCHER',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS researchers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    employee_no VARCHAR(100) UNIQUE NULL,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    college VARCHAR(200) NULL,
    department VARCHAR(200) NULL,
    expertise_keywords JSON NULL,
    research_interests JSON NULL,
    preferred_countries JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS research_projects (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    researcher_id BIGINT NOT NULL,
    title VARCHAR(500) NOT NULL,
    abstract TEXT NULL,
    keywords JSON NULL,
    status ENUM('IDEA','PROPOSED','ONGOING','COMPLETED')
           DEFAULT 'IDEA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (researcher_id) REFERENCES researchers(id)
);

CREATE TABLE IF NOT EXISTS opportunity_sources (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    base_url VARCHAR(1000) NOT NULL,
    source_type ENUM('HTML','API','RSS','MANUAL') DEFAULT 'HTML',
    trust_level ENUM(
        'OFFICIAL_AGENCY',
        'OFFICIAL_PUBLISHER',
        'VERIFIED_PARTNER',
        'AGGREGATOR'
    ) DEFAULT 'OFFICIAL_AGENCY',
    enabled BOOLEAN DEFAULT TRUE,
    last_checked_at DATETIME NULL,
    last_status VARCHAR(50) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_opportunities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_id BIGINT NULL,
    -- Scope is deliberately narrow: calls for papers and grants only.
    -- See app.etl.classifier and database/ERD.md for why the broader
    -- type list (conferences, fellowships, scholarships, startup
    -- challenges, etc.) was removed.
    opportunity_type ENUM(
        'GRANT',
        'CALL_FOR_PAPER'
    ) NOT NULL,
    title VARCHAR(1000) NOT NULL,
    organization VARCHAR(255) NULL,
    summary TEXT NULL,
    eligibility TEXT NULL,
    topics JSON NULL,
    country VARCHAR(150) NULL,
    amount_min DECIMAL(18,2) NULL,
    amount_max DECIMAL(18,2) NULL,
    currency VARCHAR(20) NULL,
    opening_date DATE NULL,
    deadline DATE NULL,
    source_url VARCHAR(1000) NOT NULL,
    canonical_url VARCHAR(1000) NULL,
    content_hash CHAR(64) NULL,
    status ENUM('OPEN','UPCOMING','CLOSED','UNKNOWN') DEFAULT 'UNKNOWN',
    verification_status ENUM(
        'VERIFIED',
        'PARTIALLY_VERIFIED',
        'UNVERIFIED'
    ) DEFAULT 'UNVERIFIED',
    -- Indexing/database labels detected in the scraped text for
    -- CALL_FOR_PAPER / JOURNAL_SPECIAL_ISSUE opportunities, e.g.
    -- ["SCOPUS", "WEB_OF_SCIENCE"]. Populated by
    -- app.etl.classifier.detect_indexing() from literal phrasing on the
    -- source page only — never inferred. Empty/NULL means the source
    -- page didn't state an index, not that the venue is unindexed.
    indexing_flags JSON NULL,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
               ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_content_hash (content_hash),
    FOREIGN KEY (source_id) REFERENCES opportunity_sources(id)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL,
    status ENUM('RUNNING','SUCCESS','PARTIAL','FAILED')
           DEFAULT 'RUNNING',
    discovered_count INT DEFAULT 0,
    inserted_count INT DEFAULT 0,
    updated_count INT DEFAULT 0,
    classified_count INT DEFAULT 0,
    -- Discovered items that didn't classify as a call for papers or a
    -- grant, and so were left out of research_opportunities entirely.
    skipped_count INT DEFAULT 0,
    error_message TEXT NULL
);
