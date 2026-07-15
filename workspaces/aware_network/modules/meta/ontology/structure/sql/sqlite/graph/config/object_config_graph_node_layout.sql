-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_node_layout (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_node_id TEXT NOT NULL,
  -- ATTRIBUTES
  layout_kind TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  source_position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_node_id, layout_kind, relative_path),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_node_id) REFERENCES object_config_graph_node(branch_id, projection_hash, id)
);
