-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE enum_option (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  enum_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  value TEXT NOT NULL,
  label TEXT,
  description TEXT,
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, enum_config_id, value),
  FOREIGN KEY (branch_id, projection_hash, enum_config_id) REFERENCES enum_config(branch_id, projection_hash, id)
);
