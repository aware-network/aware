-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_view (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_id TEXT NOT NULL,
  object_projection_graph_observable_id TEXT NOT NULL,
  state_model_id TEXT NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  view_ref TEXT NOT NULL UNIQUE,
  view_key TEXT,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_id, name, object_projection_graph_observable_id),
  FOREIGN KEY (branch_id, projection_hash, api_id) REFERENCES api(branch_id, projection_hash, id)
);
