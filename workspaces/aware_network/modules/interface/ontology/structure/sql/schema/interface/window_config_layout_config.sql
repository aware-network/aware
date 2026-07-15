-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE window_config_layout_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  window_config_id UUID NOT NULL,
  layout_config_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  is_default BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, window_config_id, layout_config_id),
  FOREIGN KEY (branch_id, projection_hash, window_config_id) REFERENCES window_config(branch_id, projection_hash, id)
);
