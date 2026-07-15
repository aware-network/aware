-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  name TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  node_config_id UUID NOT NULL UNIQUE,
  -- ATTRIBUTES
  aware_node_version INTEGER NOT NULL,
  compilation_mode TEXT NOT NULL,
  dependencies JSONB NOT NULL,
  description TEXT,
  exclude_paths JSONB NOT NULL,
  force_fresh_scan BOOLEAN NOT NULL,
  fqn_prefix TEXT,
  include_paths JSONB NOT NULL,
  manifest_relative_path TEXT,
  package_root TEXT NOT NULL,
  sources_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name)
);
