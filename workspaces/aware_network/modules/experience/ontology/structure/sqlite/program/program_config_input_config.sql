-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_input_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  name TEXT NOT NULL,
  source TEXT NOT NULL,
  -- RELATIONSHIPS
  program_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  required INTEGER NOT NULL,
  default_expr TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name, source),
  FOREIGN KEY (branch_id, projection_hash, program_config_id) REFERENCES program_config(branch_id, projection_hash, id)
);
