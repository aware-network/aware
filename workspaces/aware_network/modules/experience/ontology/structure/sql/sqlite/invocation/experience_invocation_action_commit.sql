-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_invocation_action_commit (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  experience_invocation_action_id TEXT NOT NULL,
  object_instance_graph_commit_id TEXT NOT NULL,
  -- ATTRIBUTES
  commit_role TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_invocation_action_id, object_instance_graph_commit_id),
  FOREIGN KEY (branch_id, projection_hash, experience_invocation_action_id) REFERENCES experience_invocation_action(branch_id, projection_hash, id)
);
