-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE layout_config_section_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  layout_config_id UUID NOT NULL,
  -- ATTRIBUTES
  section_key TEXT NOT NULL,
  order_ INTEGER NOT NULL,
  flex NUMERIC NOT NULL,
  is_visible BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, layout_config_id, section_key),
  FOREIGN KEY (branch_id, projection_hash, layout_config_id) REFERENCES layout_config(branch_id, projection_hash, id)
);
