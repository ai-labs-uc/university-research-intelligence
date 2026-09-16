-- ==========================
-- CREATE DATABASE
-- ==========================

CREATE DATABASE IF NOT EXISTS research_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE research_system;


-- ==========================
-- DROP EXISTING TABLES
-- ==========================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS pipeline_runs;
DROP TABLE IF EXISTS research_opportunities;
DROP TABLE IF EXISTS research_projects;
DROP TABLE IF EXISTS researchers;
DROP TABLE IF EXISTS opportunity_sources;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;


-- ==========================
-- USERS
-- ==========================

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    google_sub VARCHAR(255),
    role VARCHAR(50) DEFAULT 'RESEARCHER',
    active TINYINT DEFAULT 1,
    last_login_at DATETIME,
    created_at DATETIME
);


-- ==========================
-- RESEARCHERS
-- ==========================

CREATE TABLE researchers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    employee_no VARCHAR(100),
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    college VARCHAR(200),
    department VARCHAR(200),
    expertise_keywords TEXT,
    research_interests TEXT,
    preferred_countries TEXT,
    created_at DATETIME,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
);


-- ==========================
-- RESEARCH PROJECTS
-- ==========================

CREATE TABLE research_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    researcher_id INT NOT NULL,
    title VARCHAR(500) NOT NULL,
    abstract TEXT,
    keywords TEXT,
    status VARCHAR(50),
    created_at DATETIME,

    FOREIGN KEY (researcher_id)
        REFERENCES researchers(id)
);


-- ==========================
-- OPPORTUNITY SOURCES
-- ==========================

CREATE TABLE opportunity_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    base_url VARCHAR(1000) NOT NULL,
    source_type VARCHAR(50),
    trust_level VARCHAR(50),
    enabled TINYINT DEFAULT 1,
    last_checked_at DATETIME,
    last_status VARCHAR(50),
    created_at DATETIME
);


-- ==========================
-- RESEARCH OPPORTUNITIES
-- ==========================

CREATE TABLE research_opportunities (
    id INT AUTO_INCREMENT PRIMARY KEY,

    source_id INT,

    opportunity_type VARCHAR(50) NOT NULL,

    title VARCHAR(1000) NOT NULL,

    organization VARCHAR(255),

    summary TEXT,

    eligibility TEXT,

    topics TEXT,

    country VARCHAR(150),

    amount_min DECIMAL(18,2),

    amount_max DECIMAL(18,2),

    currency VARCHAR(20),

    opening_date DATE,

    deadline DATE,

    source_url VARCHAR(1000) NOT NULL,

    canonical_url VARCHAR(1000),

    content_hash CHAR(64),

    status VARCHAR(50),

    verification_status VARCHAR(50),

    indexing_flags TEXT,

    scope_type VARCHAR(50),

    indexing_database TEXT,

    discipline VARCHAR(255),
    
    category VARCHAR(50) NULL;

    is_current INT DEFAULT 1,

    last_seen DATETIME,

    discovered_at DATETIME,

    updated_at DATETIME,

    UNIQUE KEY uq_content_hash(content_hash),

    FOREIGN KEY (source_id)
        REFERENCES opportunity_sources(id)
);

-- ==========================
-- PIPELINE RUNS
-- ==========================

CREATE TABLE pipeline_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,

    started_at DATETIME,

    finished_at DATETIME,

    status VARCHAR(50),

    discovered_count INT DEFAULT 0,

    inserted_count INT DEFAULT 0,

    updated_count INT DEFAULT 0,

    classified_count INT DEFAULT 0
);