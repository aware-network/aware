-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_environment_profile_mount (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  mount_key TEXT NOT NULL,
  -- RELATIONSHIPS
  node_config_environment_target_id TEXT NOT NULL,
  environment_profile_package_id TEXT,
  -- ATTRIBUTES
  package_name TEXT NOT NULL,
  profile_key TEXT NOT NULL,
  mode TEXT NOT NULL,
  position INTEGER,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, mount_key),
  FOREIGN KEY (branch_id, projection_hash, node_config_environment_target_id) REFERENCES node_config_environment_target(branch_id, projection_hash, id)
);
