-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_relationship_class (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_relationship_id TEXT NOT NULL,
  class_config_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_relationship_id, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_relationship_id) REFERENCES object_config_graph_relationship(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_config_id) REFERENCES class_config(branch_id, projection_hash, id)
);
