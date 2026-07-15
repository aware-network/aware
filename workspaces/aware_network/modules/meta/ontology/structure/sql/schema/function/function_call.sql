-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_call (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_lane_id UUID NOT NULL,
  function_config_id UUID NOT NULL,
  target_class_instance_identity_id UUID,
  base_commit_id UUID,
  -- ATTRIBUTES
  call_key UUID NOT NULL,
  graph_hash_pre TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_instance_graph_lane_id, call_key, function_config_id),
  FOREIGN KEY (branch_id, projection_hash, base_commit_id) REFERENCES object_instance_graph_commit(branch_id, projection_hash, id)
);
