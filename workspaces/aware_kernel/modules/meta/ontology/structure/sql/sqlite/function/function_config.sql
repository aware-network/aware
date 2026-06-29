-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_function_id TEXT,
  -- ATTRIBUTES
  owner_key TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  verb TEXT,
  is_async INTEGER NOT NULL,
  kind TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, owner_key, name, kind)
);
