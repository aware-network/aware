-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph_lane (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_branch_id TEXT NOT NULL,
  lane_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_branch_id, lane_id),
  FOREIGN KEY (branch_id, projection_hash, object_instance_graph_branch_id) REFERENCES object_instance_graph_branch(branch_id, projection_hash, id)
);
