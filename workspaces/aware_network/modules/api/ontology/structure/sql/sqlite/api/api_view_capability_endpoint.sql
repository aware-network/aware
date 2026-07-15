-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_view_capability_endpoint (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_view_id TEXT NOT NULL,
  api_capability_endpoint_id TEXT NOT NULL,
  -- ATTRIBUTES
  action_key TEXT NOT NULL,
  endpoint_ref TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_view_id, api_capability_endpoint_id),
  FOREIGN KEY (branch_id, projection_hash, api_view_id) REFERENCES api_view(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, api_capability_endpoint_id) REFERENCES api_capability_endpoint(branch_id, projection_hash, id)
);
