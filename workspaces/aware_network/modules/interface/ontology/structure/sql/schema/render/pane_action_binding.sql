-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_action_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  pane_render_node_id UUID NOT NULL,
  projection_experience_view_invocation_action_id UUID,
  -- ATTRIBUTES
  binding_key TEXT NOT NULL,
  event pane_action_event NOT NULL,
  action_key TEXT NOT NULL,
  label TEXT,
  confirmation_policy TEXT,
  optimistic_policy TEXT,
  receipt_policy TEXT,
  component_action_port_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, pane_render_node_id, binding_key),
  FOREIGN KEY (branch_id, projection_hash, pane_render_node_id) REFERENCES pane_render_node(branch_id, projection_hash, id)
);
