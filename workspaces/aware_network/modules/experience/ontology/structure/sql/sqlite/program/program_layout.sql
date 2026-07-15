-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_layout (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_id TEXT NOT NULL,
  config_id TEXT,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  is_active INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_id, key),
  FOREIGN KEY (branch_id, projection_hash, program_id) REFERENCES program(branch_id, projection_hash, id)
);
