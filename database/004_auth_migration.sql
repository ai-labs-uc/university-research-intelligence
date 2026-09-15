-- Run against whichever database your connection is already pointed at
-- (e.g. `mysql -h <host> -u <user> -p <database> < 004_auth_migration.sql`)
-- — this file deliberately does not USE a hardcoded database name.
--
-- Run this ONLY if you already had this database set up before login
-- was added (i.e. `users` already existed with password_hash NOT
-- NULL and no google_sub/last_login_at columns). A brand-new install
-- via 001_schema.sql already has the final shape below and does not
-- need this file — CREATE TABLE IF NOT EXISTS in 001_schema.sql only
-- creates users on a database that doesn't have it yet, it does not
-- retrofit columns onto an existing table, which is exactly what this
-- migration does instead.

ALTER TABLE users
  MODIFY COLUMN password_hash VARCHAR(255) NULL;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS google_sub VARCHAR(255) NULL UNIQUE;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS last_login_at DATETIME NULL;

-- Older installs that had the now-removed researcher-level matching
-- feature (see database/ERD.md) also had these two tables and this
-- column. Safe to run even if they were already dropped.
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS opportunity_matches;
ALTER TABLE pipeline_runs DROP COLUMN IF EXISTS matched_count;
