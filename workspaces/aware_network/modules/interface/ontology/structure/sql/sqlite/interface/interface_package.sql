-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id TEXT,
  interface_config_id TEXT NOT NULL UNIQUE,
  interface_config_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  aware_interface_version INTEGER NOT NULL,
  compilation_mode TEXT NOT NULL,
  config_bundle_path TEXT,
  dart TEXT NOT NULL,
  dependencies TEXT NOT NULL,
  description TEXT,
  exclude_paths TEXT NOT NULL,
  force_fresh_scan INTEGER NOT NULL,
  fqn_prefix TEXT,
  include_paths TEXT NOT NULL,
  manifest_relative_path TEXT,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  sources_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
