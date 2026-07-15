-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_contract_actor_role_grant (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id TEXT NOT NULL,
  actor_config_role_config_id TEXT NOT NULL,
  role_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  access_scope TEXT NOT NULL,
  class_instance_identity_required INTEGER NOT NULL,
  description TEXT,
  grant_key TEXT NOT NULL,
  grant_policy_json TEXT,
  participant_kind TEXT NOT NULL,
  role_assignment_binding_required INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_id, grant_key, actor_config_role_config_id, role_config_id)
);
