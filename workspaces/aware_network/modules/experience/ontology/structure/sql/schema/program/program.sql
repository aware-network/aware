-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_impl_id UUID NOT NULL,
  active_turn_id UUID,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  title TEXT,
  description TEXT,
  status program_run_status NOT NULL,
  result_summary TEXT,
  started_at_unix_ms INTEGER,
  terminal_at_unix_ms INTEGER,
  terminal_status TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key, program_impl_id),
  FOREIGN KEY (branch_id, projection_hash, active_turn_id) REFERENCES program_turn(branch_id, projection_hash, id)
);
