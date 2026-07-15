-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_operation (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_id TEXT NOT NULL,
  api_call_id TEXT,
  api_endpoint_id TEXT,
  service_operation_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  execution_context TEXT NOT NULL,
  operation_key TEXT NOT NULL,
  result_info TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, operation_key, service_operation_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_id) REFERENCES service(branch_id, projection_hash, id)
);
