-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_graph_identity_edge (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  child_projection_experience_graph_identity_id TEXT NOT NULL,
  parent_projection_experience_graph_identity_id TEXT NOT NULL,
  projection_experience_node_identity_edge_id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_graph_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, child_projection_experience_graph_identity_id, parent_projection_experience_graph_identity_id, projection_experience_node_identity_edge_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_graph_id) REFERENCES projection_experience_graph(branch_id, projection_hash, id)
);
