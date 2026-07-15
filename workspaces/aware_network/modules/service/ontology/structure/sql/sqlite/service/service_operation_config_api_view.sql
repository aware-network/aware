-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_operation_config_api_view (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  service_operation_config_id TEXT NOT NULL,
  api_view_id TEXT NOT NULL,
  service_config_api_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_operation_config_id, api_view_id, service_config_api_id),
  FOREIGN KEY (branch_id, projection_hash, service_operation_config_id) REFERENCES service_operation_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, service_config_api_id) REFERENCES service_config_api(branch_id, projection_hash, id)
);
