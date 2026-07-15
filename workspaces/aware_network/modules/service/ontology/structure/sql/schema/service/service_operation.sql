-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_operation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_id UUID NOT NULL,
  api_call_id UUID,
  api_endpoint_id UUID,
  service_operation_config_id UUID NOT NULL,
  -- ATTRIBUTES
  execution_context JSONB NOT NULL,
  operation_key TEXT NOT NULL,
  result_info TEXT,
  status service_operation_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_id, operation_key, service_operation_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_id) REFERENCES service(branch_id, projection_hash, id)
);
