-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_layout (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  -- RELATIONSHIPS
  program_config_id TEXT NOT NULL,
  layout_id TEXT NOT NULL,
  -- ATTRIBUTES
  is_default INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key),
  FOREIGN KEY (branch_id, projection_hash, program_config_id) REFERENCES program_config(branch_id, projection_hash, id)
);
