-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_program (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  program_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  position INTEGER,
  is_default INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, thread_id, program_id)
);
