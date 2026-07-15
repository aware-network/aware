-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE section_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  layout_config_section_config_id UUID NOT NULL UNIQUE,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key),
  FOREIGN KEY (branch_id, projection_hash, layout_config_section_config_id) REFERENCES layout_config_section_config(branch_id, projection_hash, id)
);
