-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_render_spec (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  name TEXT NOT NULL,
  spec_version TEXT NOT NULL,
  pane_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  state_model_id UUID,
  -- ATTRIBUTES
  root_node_key TEXT NOT NULL,
  view_ref TEXT,
  projection_view_key TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name, spec_version, pane_config_id)
);
