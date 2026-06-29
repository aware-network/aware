-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_call (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_capability_endpoint_id UUID NOT NULL,
  request_model_id UUID NOT NULL UNIQUE,
  -- ATTRIBUTES
  call_key UUID NOT NULL,
  description TEXT,
  request_hash TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_capability_endpoint_id, call_key),
  FOREIGN KEY (branch_id, projection_hash, api_capability_endpoint_id) REFERENCES api_capability_endpoint(branch_id, projection_hash, id)
);
