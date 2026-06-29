-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_edge (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_id UUID NOT NULL,
  class_config_relationship_id UUID NOT NULL,
  -- ATTRIBUTES
  attribute_role object_projection_graph_attribute_role NOT NULL,
  depth_limit INTEGER,
  include object_projection_graph_edge_include NOT NULL,
  loading_override class_config_relationship_side_loading_strategy,
  multiplicity object_projection_graph_edge_multiplicity NOT NULL,
  traversal_direction class_config_relationship_direction NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_id, class_config_relationship_id),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_id) REFERENCES object_projection_graph(branch_id, projection_hash, id)
);
