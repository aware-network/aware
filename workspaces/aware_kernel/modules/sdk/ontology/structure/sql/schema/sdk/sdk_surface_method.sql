-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_surface_method (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sdk_surface_id UUID NOT NULL,
  target_sdk_operation_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  operation_ref TEXT NOT NULL,
  operation_name TEXT NOT NULL,
  method_family TEXT NOT NULL,
  effect TEXT NOT NULL,
  mutation_scope TEXT NOT NULL,
  confirmation_policy TEXT NOT NULL,
  execution_mode TEXT NOT NULL,
  runtime_binding_kind TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_surface_id, name, target_sdk_operation_id)
);
