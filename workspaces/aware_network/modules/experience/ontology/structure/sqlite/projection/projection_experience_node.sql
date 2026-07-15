-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_node (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  object_projection_graph_node_id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key, object_projection_graph_node_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_id) REFERENCES projection_experience(branch_id, projection_hash, id)
);
