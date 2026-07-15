-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_capability_endpoint_stream_event_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_capability_endpoint_stream_config_id UUID NOT NULL,
  class_config_id UUID NOT NULL,
  -- ATTRIBUTES
  kind api_capability_endpoint_stream_event_kind NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_capability_endpoint_stream_config_id, kind, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, api_capability_endpoint_stream_config_id) REFERENCES api_capability_endpoint_stream_config(branch_id, projection_hash, id)
);
