-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_relationship (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_id UUID NOT NULL,
  target_object_projection_graph_id UUID NOT NULL,
  class_config_relationship_id UUID NOT NULL,
  source_object_projection_graph_node_id UUID NOT NULL,
  target_object_projection_graph_node_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_id, target_object_projection_graph_id, class_config_relationship_id, source_object_projection_graph_node_id, target_object_projection_graph_node_id),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_id) REFERENCES object_projection_graph(branch_id, projection_hash, id)
);
