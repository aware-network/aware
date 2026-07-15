-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  program_impl_id TEXT NOT NULL,
  -- RELATIONSHIPS
  active_turn_id TEXT,
  -- ATTRIBUTES
  title TEXT,
  description TEXT,
  status TEXT NOT NULL,
  result_summary TEXT,
  started_at_unix_ms INTEGER,
  terminal_at_unix_ms INTEGER,
  terminal_status TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, program_impl_id),
  FOREIGN KEY (branch_id, projection_hash, active_turn_id) REFERENCES program_turn(branch_id, projection_hash, id)
);
