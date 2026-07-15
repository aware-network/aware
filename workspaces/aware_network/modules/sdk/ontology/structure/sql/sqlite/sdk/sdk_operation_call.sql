-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_operation_call (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  sdk_operation_id TEXT NOT NULL,
  api_call_id TEXT,
  -- ATTRIBUTES
  call_key TEXT NOT NULL,
  description TEXT,
  request_hash TEXT NOT NULL,
  context_hash TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_operation_id, call_key),
  FOREIGN KEY (branch_id, projection_hash, sdk_operation_id) REFERENCES sdk_operation(branch_id, projection_hash, id)
);
