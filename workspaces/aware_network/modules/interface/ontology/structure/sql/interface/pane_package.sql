-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE pane_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  name TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  pane_config_id UUID NOT NULL UNIQUE,
  pane_config_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  aware_pane_version INTEGER NOT NULL,
  dart JSONB NOT NULL,
  description TEXT,
  exclude_paths JSONB NOT NULL,
  force_fresh_scan BOOLEAN NOT NULL,
  fqn_prefix TEXT,
  include_paths JSONB NOT NULL,
  manifest_relative_path TEXT,
  package_root TEXT NOT NULL,
  pane_name TEXT,
  python JSONB NOT NULL,
  sources_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name)
);
