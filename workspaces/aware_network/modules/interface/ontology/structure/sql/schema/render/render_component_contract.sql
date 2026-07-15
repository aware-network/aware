-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE render_component_contract (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  render_component_config_id UUID NOT NULL,
  -- ATTRIBUTES
  component_ref TEXT NOT NULL,
  contract_version INTEGER NOT NULL,
  display_name TEXT,
  description TEXT,
  surface_kind TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, render_component_config_id, component_ref)
);
