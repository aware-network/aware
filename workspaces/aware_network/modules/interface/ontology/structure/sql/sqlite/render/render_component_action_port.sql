-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE render_component_action_port (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  render_component_contract_id TEXT NOT NULL,
  -- ATTRIBUTES
  port_key TEXT NOT NULL,
  event TEXT NOT NULL,
  is_required INTEGER NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, render_component_contract_id, port_key)
);
