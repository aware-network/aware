-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_capability_endpoint_stream_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_capability_endpoint_request_config_id UUID UNIQUE,
  -- ATTRIBUTES
  stream_mode api_capability_endpoint_stream_mode NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, stream_mode),
  FOREIGN KEY (branch_id, projection_hash, api_capability_endpoint_request_config_id) REFERENCES api_capability_endpoint_request_config(branch_id, projection_hash, id)
);
