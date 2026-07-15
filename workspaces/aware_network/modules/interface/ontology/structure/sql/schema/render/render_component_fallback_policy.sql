-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE render_component_fallback_policy (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  render_component_contract_id UUID NOT NULL,
  -- ATTRIBUTES
  policy_key TEXT NOT NULL,
  fallback_kind TEXT NOT NULL,
  fallback_component_ref TEXT,
  fallback_node_kind pane_render_node_kind,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, render_component_contract_id, policy_key)
);
