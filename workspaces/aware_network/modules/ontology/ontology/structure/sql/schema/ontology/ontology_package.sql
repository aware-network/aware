-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE ontology_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  ontology_config_id UUID,
  ontology_config_object_instance_graph_commit_id UUID,
  source_code_package_id UUID,
  object_config_graph_package_id UUID,
  object_config_graph_package_object_instance_graph_commit_id UUID,
  object_config_graph_object_instance_graph_commit_id UUID,
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
