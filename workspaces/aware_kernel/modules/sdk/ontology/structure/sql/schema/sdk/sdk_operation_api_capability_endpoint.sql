-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_operation_api_capability_endpoint (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sdk_operation_id UUID NOT NULL,
  api_capability_endpoint_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  endpoint_ref TEXT,
  discriminant TEXT,
  role TEXT NOT NULL,
  order_ INTEGER NOT NULL,
  required BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_operation_id, name, api_capability_endpoint_id),
  FOREIGN KEY (branch_id, projection_hash, sdk_operation_id) REFERENCES sdk_operation(branch_id, projection_hash, id)
);
