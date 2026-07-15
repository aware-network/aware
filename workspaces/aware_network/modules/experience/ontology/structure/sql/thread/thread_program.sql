-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_program (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  thread_id UUID NOT NULL,
  program_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  position INTEGER,
  is_default BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, thread_id, program_id)
);
