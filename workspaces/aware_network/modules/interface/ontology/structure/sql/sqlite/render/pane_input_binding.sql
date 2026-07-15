-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_input_binding (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_action_binding_id TEXT NOT NULL,
  -- ATTRIBUTES
  payload_path TEXT NOT NULL,
  source_node_key TEXT,
  source_json_path TEXT,
  literal_value TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_action_binding_id, payload_path),
  FOREIGN KEY (branch_id, projection_hash, pane_action_binding_id) REFERENCES pane_action_binding(branch_id, projection_hash, id)
);
