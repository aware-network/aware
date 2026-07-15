-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE render_component_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  source_code_package_id TEXT,
  render_component_config_id TEXT NOT NULL UNIQUE,
  render_component_config_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  aware_render_component_version INTEGER NOT NULL,
  dart TEXT NOT NULL,
  description TEXT,
  exclude_paths TEXT NOT NULL,
  force_fresh_scan INTEGER NOT NULL,
  fqn_prefix TEXT,
  include_paths TEXT NOT NULL,
  manifest_relative_path TEXT,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  python TEXT NOT NULL,
  sources_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, name)
);
