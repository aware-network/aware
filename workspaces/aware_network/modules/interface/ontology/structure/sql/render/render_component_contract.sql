-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE render_component_contract (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  component_ref TEXT NOT NULL,
  -- RELATIONSHIPS
  render_component_config_id UUID NOT NULL,
  -- ATTRIBUTES
  contract_version INTEGER NOT NULL,
  display_name TEXT,
  description TEXT,
  surface_kind TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, component_ref)
);
