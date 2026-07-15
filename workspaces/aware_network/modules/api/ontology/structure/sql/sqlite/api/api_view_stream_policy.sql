-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_view_stream_policy (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_view_id TEXT UNIQUE,
  -- ATTRIBUTES
  stream_mode TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, stream_mode),
  FOREIGN KEY (branch_id, projection_hash, api_view_id) REFERENCES api_view(branch_id, projection_hash, id)
);
