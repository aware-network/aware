-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_node_identity_edge (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_graph_id UUID NOT NULL,
  child_projection_experience_node_identity_id UUID NOT NULL,
  parent_projection_experience_node_identity_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_graph_id, child_projection_experience_node_identity_id, parent_projection_experience_node_identity_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_graph_id) REFERENCES projection_experience_graph(branch_id, projection_hash, id)
);
