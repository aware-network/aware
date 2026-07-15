-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  name TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  source_code_package_id TEXT,
  skill_config_id TEXT NOT NULL UNIQUE,
  skill_config_object_instance_graph_commit_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name)
);
