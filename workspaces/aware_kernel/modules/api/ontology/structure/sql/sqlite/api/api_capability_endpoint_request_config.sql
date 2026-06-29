-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_capability_endpoint_request_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_capability_endpoint_id TEXT NOT NULL UNIQUE,
  class_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, api_capability_endpoint_id) REFERENCES api_capability_endpoint(branch_id, projection_hash, id)
);
