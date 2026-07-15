-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_render_spec (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_config_id TEXT NOT NULL,
  state_model_id TEXT,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  spec_version TEXT NOT NULL,
  root_node_key TEXT NOT NULL,
  view_ref TEXT,
  projection_view_key TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name, spec_version, pane_config_id)
);
