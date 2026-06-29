-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_operation_dependency (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  sdk_operation_id TEXT NOT NULL,
  target_sdk_operation_id TEXT NOT NULL,
  -- ATTRIBUTES
  target_operation_ref TEXT NOT NULL,
  target_sdk_name TEXT NOT NULL,
  target_operation_name TEXT NOT NULL,
  target_package_name TEXT,
  role TEXT NOT NULL,
  order_ INTEGER NOT NULL,
  required INTEGER NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_operation_id, target_sdk_operation_id),
  FOREIGN KEY (branch_id, projection_hash, sdk_operation_id) REFERENCES sdk_operation(branch_id, projection_hash, id)
);
