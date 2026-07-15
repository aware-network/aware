-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_run (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  run_key TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_config_id UUID NOT NULL,
  -- ATTRIBUTES
  error TEXT,
  finished_at_utc TIMESTAMPTZ,
  started_at_utc TIMESTAMPTZ,
  status skill_run_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, run_key)
);
