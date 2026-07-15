-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_contract_config_actor_role_grant (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_contract_config_id UUID NOT NULL,
  role_config_id UUID NOT NULL,
  -- ATTRIBUTES
  access_scope TEXT NOT NULL,
  class_instance_identity_required BOOLEAN NOT NULL,
  description TEXT,
  grant_policy_json JSONB,
  role_assignment_binding_required BOOLEAN NOT NULL,
  scope_kind TEXT NOT NULL,
  scope_ref TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_contract_config_id, scope_kind, scope_ref, role_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_contract_config_id) REFERENCES service_contract_config(branch_id, projection_hash, id)
);
