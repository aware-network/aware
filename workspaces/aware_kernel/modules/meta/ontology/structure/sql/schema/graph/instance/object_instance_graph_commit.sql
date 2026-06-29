-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_instance_graph_commit (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  id UUID NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  object_instance_graph_identity_id UUID NOT NULL,
  object_instance_graph_id UUID NOT NULL,
  commit_id UUID NOT NULL,
  -- ATTRIBUTES
  object_instance_graph_key TEXT NOT NULL,
  object_instance_graph_name TEXT NOT NULL,
  object_instance_graph_description TEXT,
  root_class_config_id UUID NOT NULL,
  root_source_object_id UUID NOT NULL,
  graph_hash_post TEXT NOT NULL,
  graph_hash_pre TEXT NOT NULL,
  source_language code_language NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, object_instance_graph_identity_id, commit_id)
);
