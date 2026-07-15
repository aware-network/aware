-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE render_component_capability (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  render_component_contract_id UUID NOT NULL,
  -- ATTRIBUTES
  capability_kind TEXT NOT NULL,
  capability_key TEXT NOT NULL,
  is_required BOOLEAN NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, render_component_contract_id, capability_kind, capability_key)
);
