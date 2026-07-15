-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_node (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id UUID NOT NULL,
  class_config_relationship_id UUID UNIQUE,
  -- ATTRIBUTES
  type_ object_config_graph_node_type NOT NULL,
  node_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, type_, node_key),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_id) REFERENCES object_config_graph(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_config_relationship_id) REFERENCES class_config_relationship(branch_id, projection_hash, id)
);
