-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE ontology_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  ontology_config_id TEXT,
  ontology_config_object_instance_graph_commit_id TEXT,
  source_code_package_id TEXT,
  object_config_graph_package_id TEXT,
  object_config_graph_package_object_instance_graph_commit_id TEXT,
  object_config_graph_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  description TEXT,
  fqn_prefix TEXT NOT NULL,
  manifest_relative_path TEXT,
  name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  sources_root TEXT NOT NULL,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, fqn_prefix, name)
);
