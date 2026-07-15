-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE app_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  app_config_id UUID NOT NULL UNIQUE,
  app_config_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  aware_app_version INTEGER NOT NULL,
  dart JSONB NOT NULL,
  dependencies JSONB NOT NULL,
  description TEXT,
  manifest_relative_path TEXT,
  metadata_json JSONB NOT NULL,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
