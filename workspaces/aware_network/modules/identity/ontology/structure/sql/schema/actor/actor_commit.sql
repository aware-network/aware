-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_commit (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_id UUID NOT NULL,
  object_instance_graph_commit_id UUID NOT NULL,
  -- ATTRIBUTES
  domain_branch_id UUID NOT NULL,
  domain_projection_hash TEXT NOT NULL,
  domain_commit_id UUID NOT NULL,
  environment_id UUID,
  process_id UUID,
  thread_id UUID,
  receipt_actor_id UUID,
  created_at_unix_ms INTEGER,
  operation_label TEXT,
  call_target TEXT,
  function_id UUID,
  object_id UUID,
  class_instance_identity_id UUID,
  graph_hash_post TEXT,
  object_instance_graph_id UUID,
  root_object_id UUID,
  head_version INTEGER,
  source TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id, domain_branch_id, domain_projection_hash, domain_commit_id),
  FOREIGN KEY (branch_id, projection_hash, actor_id) REFERENCES actor(branch_id, projection_hash, id)
);
