-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_node_key (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_node_id UUID NOT NULL,
  object_projection_graph_node_key_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_node_id, object_projection_graph_node_key_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_node_id) REFERENCES projection_experience_node(branch_id, projection_hash, id)
);
