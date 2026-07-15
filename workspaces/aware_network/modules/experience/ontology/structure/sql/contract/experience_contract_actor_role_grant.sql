-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_contract_actor_role_grant (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  grant_key TEXT NOT NULL,
  actor_config_role_config_id UUID NOT NULL,
  role_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id UUID NOT NULL,
  -- ATTRIBUTES
  access_scope TEXT NOT NULL,
  class_instance_identity_required BOOLEAN NOT NULL,
  description TEXT,
  grant_policy_json JSONB,
  participant_kind TEXT NOT NULL,
  role_assignment_binding_required BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, grant_key, actor_config_role_config_id, role_config_id)
);
