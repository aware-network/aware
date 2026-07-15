-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_call_stream_event (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  api_call_id UUID NOT NULL,
  api_capability_endpoint_stream_event_config_id UUID NOT NULL,
  event_model_id UUID NOT NULL UNIQUE,
  -- ATTRIBUTES
  description TEXT,
  sequence INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_call_id, sequence),
  FOREIGN KEY (branch_id, projection_hash, api_call_id) REFERENCES api_call(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, api_capability_endpoint_stream_event_config_id) REFERENCES api_capability_endpoint_stream_event_config(branch_id, projection_hash, id)
);
