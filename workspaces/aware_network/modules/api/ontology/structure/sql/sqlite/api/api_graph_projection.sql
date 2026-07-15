-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_graph_projection (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_graph_id TEXT NOT NULL,
  object_projection_graph_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_graph_id, object_projection_graph_id),
  FOREIGN KEY (branch_id, projection_hash, api_graph_id) REFERENCES api_graph(branch_id, projection_hash, id)
);
