-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE ontology_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id TEXT,
  object_config_graph_object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  description TEXT,
  fqn_prefix TEXT NOT NULL,
  name TEXT NOT NULL,
  schema_hash TEXT,
  title TEXT,
  version_number INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, fqn_prefix, name)
);
