-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_profile_actor_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_profile_config_id TEXT NOT NULL,
  actor_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  access_scope TEXT NOT NULL,
  description TEXT,
  metadata_json TEXT NOT NULL,
  policy_key TEXT NOT NULL,
  requirement_kind TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_profile_config_id, policy_key, actor_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_profile_config_id) REFERENCES environment_profile_config(branch_id, projection_hash, id)
);
