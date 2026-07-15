-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  sdk_config_id UUID NOT NULL UNIQUE,
  sdk_config_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  aware_sdk_version INTEGER NOT NULL,
  compilation_mode TEXT NOT NULL,
  dependencies JSONB NOT NULL,
  description TEXT,
  exclude_paths JSONB NOT NULL,
  force_fresh_scan BOOLEAN NOT NULL,
  fqn_prefix TEXT,
  include_paths JSONB NOT NULL,
  manifest_relative_path TEXT,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  sources_root TEXT NOT NULL,
  targets JSONB NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
