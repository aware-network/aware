-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_call (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_lane_id TEXT NOT NULL,
  function_config_id TEXT NOT NULL,
  target_class_instance_identity_id TEXT,
  base_commit_id TEXT,
  -- ATTRIBUTES
  call_key TEXT NOT NULL,
  graph_hash_pre TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_lane_id, call_key, function_config_id),
  FOREIGN KEY (branch_id, projection_hash, base_commit_id) REFERENCES object_instance_graph_commit(branch_id, projection_hash, id)
);
