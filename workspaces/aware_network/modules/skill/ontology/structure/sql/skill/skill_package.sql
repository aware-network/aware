-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  name TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  source_code_package_id UUID,
  skill_config_id UUID NOT NULL UNIQUE,
  skill_config_object_instance_graph_commit_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name)
);
