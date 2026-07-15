-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_profile_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  environment_config_package_id UUID,
  environment_config_package_object_instance_graph_commit_id UUID,
  environment_profile_config_id UUID NOT NULL UNIQUE,
  environment_profile_config_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  description TEXT,
  environment_handle TEXT,
  manifest_relative_path TEXT,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  profile_key TEXT,
  sources_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
