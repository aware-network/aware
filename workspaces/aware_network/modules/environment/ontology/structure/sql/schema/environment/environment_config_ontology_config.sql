-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_config_ontology_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_config_id UUID NOT NULL,
  ontology_config_id UUID,
  ontology_config_object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  fqn_prefix TEXT NOT NULL,
  name TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_config_id, fqn_prefix, name),
  FOREIGN KEY (branch_id, projection_hash, environment_config_id) REFERENCES environment_config(branch_id, projection_hash, id)
);
