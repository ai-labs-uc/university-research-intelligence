-- ============================================================================
-- 006_deadlines_and_notifications.sql
-- ============================================================================
--
-- Adds the deadline-notification tables and the columns the application
-- already reads but that 001_schema.sql never defined.
--
-- WRITTEN FOR AN OLD MySQL ON SHARED HOSTING (freesqldatabase).
-- It deliberately avoids everything such a server tends to reject:
--
--   * NO stored procedures. Free shared hosts usually withhold the
--     CREATE ROUTINE privilege, so a procedure-based migration fails
--     outright with "access denied".
--   * NO "ADD COLUMN IF NOT EXISTS" / "CREATE INDEX IF NOT EXISTS".
--     Those need MySQL 8.0.29+.
--   * NO "DATETIME DEFAULT CURRENT_TIMESTAMP". Before MySQL 5.6.5 only
--     TIMESTAMP columns could have that default. The application always
--     passes NOW() explicitly, so no default is needed anywhere.
--   * Index widths stay well inside the 767-byte InnoDB limit that older
--     servers enforce on utf8mb4.
--
-- ============================================================================
-- HOW TO RUN IT (phpMyAdmin)
-- ============================================================================
--
--   1. Run STEP 0 first and read the result. It tells you exactly which
--      later steps you still need.
--   2. Run STEP 1 as one block. It is safe on any server and safe to
--      repeat.
--   3. Run each statement in STEP 2 and STEP 3 ONE AT A TIME.
--
--      If a statement fails with:
--          #1060 - Duplicate column name '...'
--          #1061 - Duplicate key name '...'
--      that column or index already exists. THAT IS FINE — skip it and
--      carry on to the next statement. Nothing is broken.
--
--      Any other error, stop and send it to me.
--   4. Run STEP 4, then STEP 5 to confirm.
--
-- Nothing here deletes data. The only UPDATEs set a flag on rows that are
-- already past their deadline.
--
-- ============================================================================


-- ============================================================================
-- STEP 0 — PRE-FLIGHT. Run this first, on its own.
-- ============================================================================
-- Shows your MySQL version and which pieces are already present.
-- Anything marked NEEDED means run that part below; ALREADY THERE means skip.

SELECT VERSION() AS mysql_version;

SELECT 'column: scope_type' AS item,
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED') AS state
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'scope_type'
UNION ALL
SELECT 'column: category',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'category'
UNION ALL
SELECT 'column: is_current',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'is_current'
UNION ALL
SELECT 'column: last_seen',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'last_seen'
UNION ALL
SELECT 'index: idx_opp_deadline_current',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.STATISTICS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND INDEX_NAME = 'idx_opp_deadline_current'
UNION ALL
SELECT 'table: alerts',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'alerts'
UNION ALL
SELECT 'table: notification_log',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'notification_log'
UNION ALL
SELECT 'table: notification_prefs',
       IF(COUNT(*) > 0, 'ALREADY THERE', 'NEEDED')
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'notification_prefs';


-- ============================================================================
-- STEP 1 — NEW TABLES. Safe to run as one block, and safe to repeat.
-- ============================================================================
-- "CREATE TABLE IF NOT EXISTS" works on every MySQL version, so this part
-- never errors even if you run it twice.
--
-- No foreign keys are declared. On shared hosting the engine or privileges
-- sometimes make FKs fail, and a failed FK would abort the whole table
-- creation. The application always writes valid ids, and ON DELETE
-- behaviour is handled in code.

CREATE TABLE IF NOT EXISTS notification_prefs (
    user_id           BIGINT       NOT NULL,
    lead_days         VARCHAR(50)  NOT NULL DEFAULT '30,14,7,3,1',
    email_enabled     TINYINT(1)   NOT NULL DEFAULT 1,
    inapp_enabled     TINYINT(1)   NOT NULL DEFAULT 1,
    digest_mode       TINYINT(1)   NOT NULL DEFAULT 1,
    categories_filter VARCHAR(200) NULL,
    updated_at        DATETIME     NULL,
    PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- The UNIQUE key is the point of this table: it is what stops the nightly
-- job re-sending an alert it already sent. Without it, every run would
-- email users about the same deadline again.
CREATE TABLE IF NOT EXISTS notification_log (
    id             BIGINT       NOT NULL AUTO_INCREMENT,
    user_id        BIGINT       NOT NULL,
    opportunity_id BIGINT       NOT NULL,
    lead_days      INT          NOT NULL,
    channel        VARCHAR(20)  NOT NULL DEFAULT 'email',
    sent_at        DATETIME     NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_send (user_id, opportunity_id, lead_days, channel),
    KEY idx_user_sent (user_id, sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS alerts (
    id             BIGINT     NOT NULL AUTO_INCREMENT,
    user_id        BIGINT     NOT NULL,
    opportunity_id BIGINT     NOT NULL,
    alert_type     VARCHAR(20) NOT NULL,
    message        TEXT       NOT NULL,
    lead_days      INT        NULL,
    is_read        TINYINT(1) NOT NULL DEFAULT 0,
    created_at     DATETIME   NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_alert (user_id, opportunity_id, alert_type, lead_days),
    KEY idx_user_unread (user_id, is_read, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================================
-- STEP 2 — COLUMNS. Run these ONE AT A TIME.
-- ============================================================================
-- Skip any that STEP 0 reported as ALREADY THERE.
-- Error #1060 "Duplicate column name" just means it already exists — ignore
-- it and move to the next statement.

ALTER TABLE research_opportunities
  ADD COLUMN scope_type VARCHAR(20) NULL;

ALTER TABLE research_opportunities
  ADD COLUMN category VARCHAR(50) NULL;

ALTER TABLE research_opportunities
  ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1;

ALTER TABLE research_opportunities
  ADD COLUMN last_seen DATETIME NULL;


-- If your `alerts` table already existed in the older pre-login shape
-- (keyed on researcher_id), these bring it up to date. If STEP 1 just
-- created the table, both will report #1060 — expected, skip them.

ALTER TABLE alerts ADD COLUMN user_id BIGINT NULL;

ALTER TABLE alerts ADD COLUMN lead_days INT NULL;


-- ============================================================================
-- STEP 3 — INDEXES. Run these ONE AT A TIME.
-- ============================================================================
-- The nightly notification job filters on (deadline, is_current) every run.
-- Without these it reads the whole table each time.
-- Error #1061 "Duplicate key name" means it already exists — ignore it.

CREATE INDEX idx_opp_deadline_current
    ON research_opportunities (deadline, is_current);

CREATE INDEX idx_opp_category_current
    ON research_opportunities (category, is_current);


-- ============================================================================
-- STEP 4 — BACKFILL. Safe to run as one block, and safe to repeat.
-- ============================================================================

-- Derive scope from category on rows written before this migration, so the
-- dashboard counters are not all zero on day one.
UPDATE research_opportunities
   SET scope_type = CASE
         WHEN category LIKE '%INTERNATIONAL%' THEN 'INTERNATIONAL'
         ELSE 'NATIONAL'
       END
 WHERE scope_type IS NULL
   AND category IS NOT NULL;

-- Make sure existing rows are visible to the API, which filters on
-- is_current = 1.
UPDATE research_opportunities
   SET is_current = 1
 WHERE is_current IS NULL;

-- Close out anything already past its deadline.
UPDATE research_opportunities
   SET is_current = 0,
       status = 'CLOSED'
 WHERE deadline IS NOT NULL
   AND deadline < CURDATE();


-- ============================================================================
-- STEP 5 — VERIFY. Every row should read OK.
-- ============================================================================

SELECT 'column: scope_type' AS item,
       IF(COUNT(*) = 1, 'OK', 'MISSING') AS state
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'scope_type'
UNION ALL
SELECT 'column: category',
       IF(COUNT(*) = 1, 'OK', 'MISSING')
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'category'
UNION ALL
SELECT 'column: is_current',
       IF(COUNT(*) = 1, 'OK', 'MISSING')
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'is_current'
UNION ALL
SELECT 'column: last_seen',
       IF(COUNT(*) = 1, 'OK', 'MISSING')
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'research_opportunities'
   AND COLUMN_NAME = 'last_seen'
UNION ALL
SELECT 'table: alerts',
       IF(COUNT(*) = 1, 'OK', 'MISSING')
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'alerts'
UNION ALL
SELECT 'table: notification_log',
       IF(COUNT(*) = 1, 'OK', 'MISSING')
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'notification_log'
UNION ALL
SELECT 'table: notification_prefs',
       IF(COUNT(*) = 1, 'OK', 'MISSING')
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME = 'notification_prefs';


-- Baseline. Note what `with_deadline` says now — it should currently be 0.
-- After the first harvest runs, that number moving above zero is the
-- clearest single proof that the deadline fix worked.

SELECT COUNT(*)                  AS total_rows,
       SUM(deadline IS NOT NULL) AS with_deadline,
       SUM(is_current = 1)       AS active_rows
  FROM research_opportunities;
