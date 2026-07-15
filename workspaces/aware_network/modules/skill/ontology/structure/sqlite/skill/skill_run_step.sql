-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_run_step (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  skill_config_step_id TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_run_id TEXT NOT NULL,
  api_call_id TEXT UNIQUE,
  -- ATTRIBUTES
  error TEXT,
  finished_at_utc TEXT,
  started_at_utc TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, skill_config_step_id),
  FOREIGN KEY (branch_id, projection_hash, skill_run_id) REFERENCES skill_run(branch_id, projection_hash, id)
);
