-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE app_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id TEXT,
  app_config_id TEXT NOT NULL UNIQUE,
  app_config_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  aware_app_version INTEGER NOT NULL,
  dart TEXT NOT NULL,
  dependencies TEXT NOT NULL,
  description TEXT,
  manifest_relative_path TEXT,
  metadata_json TEXT NOT NULL,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
