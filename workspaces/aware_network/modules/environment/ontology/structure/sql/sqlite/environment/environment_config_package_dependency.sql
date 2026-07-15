-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_config_package_dependency (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_config_package_id TEXT NOT NULL,
  target_environment_config_package_id TEXT NOT NULL,
  target_environment_config_package_object_instance_graph_commit_id TEXT NOT NULL,
  -- ATTRIBUTES
  dependency_role TEXT NOT NULL,
  dependency_index INTEGER NOT NULL,
  target_handle TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_config_package_id, dependency_role, dependency_index, target_handle, target_environment_config_package_id, target_environment_config_package_object_instance_graph_commit_id),
  FOREIGN KEY (branch_id, projection_hash, environment_config_package_id) REFERENCES environment_config_package(branch_id, projection_hash, id)
);
