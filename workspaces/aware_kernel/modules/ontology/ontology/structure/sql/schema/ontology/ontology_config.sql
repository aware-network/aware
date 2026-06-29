-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE ontology_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id UUID,
  object_config_graph_object_instance_graph_commit_id UUID,
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
