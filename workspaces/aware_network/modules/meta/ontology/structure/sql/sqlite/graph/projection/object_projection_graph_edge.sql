-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_edge (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_id TEXT NOT NULL,
  class_config_relationship_id TEXT NOT NULL,
  -- ATTRIBUTES
  attribute_role TEXT NOT NULL,
  depth_limit INTEGER,
  include TEXT NOT NULL,
  loading_override TEXT,
  multiplicity TEXT NOT NULL,
  traversal_direction TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_id, class_config_relationship_id),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_id) REFERENCES object_projection_graph(branch_id, projection_hash, id)
);
