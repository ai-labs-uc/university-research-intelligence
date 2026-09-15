-- Run against whichever database your connection is already pointed at
-- (e.g. `mysql -h <host> -u <user> -p <database> < 005_remove_programs_narrow_scope.sql`)
-- — this file deliberately does not USE a hardcoded database name.
--
-- Run this ONLY if you already had this database set up before the
-- program/college matching feature and the wider opportunity_type list
-- were removed. A brand-new install via 001_schema.sql already has the
-- final shape below and does not need this file.
--
-- This migration does two things:
--   1. Drops the program/college matching feature entirely (Programs
--      page, academic_units, opportunity_program_matches) — see
--      database/ERD.md for why.
--   2. Narrows opportunity_type down to GRANT and CALL_FOR_PAPER only,
--      matching the system's new, deliberately narrow scope. Existing
--      rows of any other type are deleted rather than force-fit into
--      one of the two remaining categories, since a silent relabel
--      would misrepresent what the source page actually said.

-- --- 1. Program/college matching -------------------------------------

DROP TABLE IF EXISTS opportunity_program_matches;
DROP TABLE IF EXISTS academic_units;

ALTER TABLE pipeline_runs DROP COLUMN IF EXISTS program_matched_count;
ALTER TABLE pipeline_runs ADD COLUMN IF NOT EXISTS skipped_count INT DEFAULT 0;

-- --- 2. Narrow opportunity_type ---------------------------------------

DELETE FROM research_opportunities
WHERE opportunity_type NOT IN ('GRANT', 'CALL_FOR_PAPER');

ALTER TABLE research_opportunities
  MODIFY COLUMN opportunity_type ENUM('GRANT', 'CALL_FOR_PAPER') NOT NULL;
