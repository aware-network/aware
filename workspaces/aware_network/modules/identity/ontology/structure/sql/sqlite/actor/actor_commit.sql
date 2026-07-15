-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_commit (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  actor_id TEXT NOT NULL,
  object_instance_graph_commit_id TEXT NOT NULL,
  -- ATTRIBUTES
  domain_branch_id TEXT NOT NULL,
  domain_projection_hash TEXT NOT NULL,
  domain_commit_id TEXT NOT NULL,
  environment_id TEXT,
  process_id TEXT,
  thread_id TEXT,
  receipt_actor_id TEXT,
  created_at_unix_ms INTEGER,
  operation_label TEXT,
  call_target TEXT,
  function_id TEXT,
  object_id TEXT,
  class_instance_identity_id TEXT,
  graph_hash_post TEXT,
  object_instance_graph_id TEXT,
  root_object_id TEXT,
  head_version INTEGER,
  source TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id, domain_branch_id, domain_projection_hash, domain_commit_id),
  FOREIGN KEY (branch_id, projection_hash, actor_id) REFERENCES actor(branch_id, projection_hash, id)
);
