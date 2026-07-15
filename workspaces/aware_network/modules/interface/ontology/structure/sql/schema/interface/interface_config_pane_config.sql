-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_config_pane_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_config_id UUID NOT NULL,
  pane_config_id UUID NOT NULL,
  -- ATTRIBUTES
  narrative_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, interface_config_id, pane_config_id),
  FOREIGN KEY (branch_id, projection_hash, interface_config_id) REFERENCES interface_config(branch_id, projection_hash, id)
);
