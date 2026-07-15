-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_node_key (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_node_id TEXT NOT NULL,
  object_config_graph_binding_class_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  position INTEGER,
  required INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_node_id, key, object_config_graph_binding_class_id),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_node_id) REFERENCES object_projection_graph_node(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_binding_class_id) REFERENCES object_config_graph_binding_class(branch_id, projection_hash, id)
);
