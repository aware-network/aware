-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_environment_profile_mount (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  node_config_environment_target_id UUID NOT NULL,
  environment_profile_package_id UUID,
  -- ATTRIBUTES
  package_name TEXT NOT NULL,
  profile_key TEXT NOT NULL,
  mount_key TEXT NOT NULL,
  mode TEXT NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, node_config_environment_target_id, mount_key),
  FOREIGN KEY (branch_id, projection_hash, node_config_environment_target_id) REFERENCES node_config_environment_target(branch_id, projection_hash, id)
);
