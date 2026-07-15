-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_graph_identity (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  projection_experience_node_identity_id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_graph_id TEXT NOT NULL,
  -- ATTRIBUTES
  is_root INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, projection_experience_node_identity_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_graph_id) REFERENCES projection_experience_graph(branch_id, projection_hash, id)
);
