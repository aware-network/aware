-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_package_build (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_package_id UUID NOT NULL,
  -- ATTRIBUTES
  environment_slug TEXT NOT NULL,
  sources_dir TEXT NOT NULL,
  include_paths TEXT[] NOT NULL,
  exclude_paths TEXT[] NOT NULL,
  force_fresh_scan BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_package_id)
);
