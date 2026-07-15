-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_operation_config_api_endpoint_function (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_operation_config_api_endpoint_id TEXT NOT NULL,
  api_capability_endpoint_function_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_operation_config_api_endpoint_id, api_capability_endpoint_function_id),
  FOREIGN KEY (branch_id, projection_hash, service_operation_config_api_endpoint_id) REFERENCES service_operation_config_api_endpoint(branch_id, projection_hash, id)
);
