-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_projection_graph_node (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_projection_graph_id TEXT NOT NULL,
  class_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  is_root INTEGER NOT NULL,
  policy_refs TEXT NOT NULL,
  required_for_validity INTEGER NOT NULL,
  selection TEXT NOT NULL,
  selector_condition_id TEXT,
  top_n INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_projection_graph_id, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, object_projection_graph_id) REFERENCES object_projection_graph(branch_id, projection_hash, id)
);
