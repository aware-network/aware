-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_semantic_package_binding (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_semantic_provider_registration_id TEXT NOT NULL,
  code_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  code_package_config_key TEXT,
  code_module_name TEXT,
  capabilities TEXT NOT NULL,
  manifest_relative_path TEXT,
  module_package_id TEXT NOT NULL,
  module_package_kind TEXT,
  module_relative_package_root TEXT,
  owned_manifest_kinds TEXT NOT NULL,
  semantic_contract_module TEXT,
  semantic_contract_name TEXT NOT NULL,
  semantic_contract_role TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_semantic_provider_registration_id, module_package_id, semantic_contract_name, semantic_contract_role, code_package_id)
);
