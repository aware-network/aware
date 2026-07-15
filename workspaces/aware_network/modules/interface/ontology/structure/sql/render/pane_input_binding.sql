-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_input_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  payload_path TEXT NOT NULL,
  -- RELATIONSHIPS
  pane_action_binding_id UUID NOT NULL,
  -- ATTRIBUTES
  source_node_key TEXT,
  source_json_path TEXT,
  literal_value TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, payload_path),
  FOREIGN KEY (branch_id, projection_hash, pane_action_binding_id) REFERENCES pane_action_binding(branch_id, projection_hash, id)
);
