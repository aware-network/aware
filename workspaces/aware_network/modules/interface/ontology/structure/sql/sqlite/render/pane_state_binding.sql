-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_state_binding (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_render_node_id TEXT NOT NULL,
  state_model_id TEXT,
  state_attribute_config_id TEXT,
  -- ATTRIBUTES
  binding_key TEXT NOT NULL,
  target_property TEXT NOT NULL,
  json_path TEXT NOT NULL,
  transform TEXT NOT NULL,
  fallback_value TEXT,
  component_input_port_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_render_node_id, binding_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_node_id) REFERENCES pane_render_node(branch_id, projection_hash, id)
);
