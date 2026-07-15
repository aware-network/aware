-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_run_step (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  skill_config_step_id UUID NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_run_id UUID NOT NULL,
  api_call_id UUID UNIQUE,
  -- ATTRIBUTES
  error TEXT,
  finished_at_utc TIMESTAMPTZ,
  started_at_utc TIMESTAMPTZ,
  status skill_run_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, skill_config_step_id),
  FOREIGN KEY (branch_id, projection_hash, skill_run_id) REFERENCES skill_run(branch_id, projection_hash, id)
);
