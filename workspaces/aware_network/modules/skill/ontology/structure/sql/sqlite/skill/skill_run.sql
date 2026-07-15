-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_run (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  skill_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  error TEXT,
  finished_at_utc TEXT,
  run_key TEXT NOT NULL,
  started_at_utc TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, skill_config_id, run_key)
);
