-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_semantic_contract_runtime_import (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_semantic_contract_profile_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  capabilities TEXT NOT NULL,
  import_role TEXT NOT NULL,
  owned_manifest_kinds TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  required INTEGER NOT NULL,
  semantic_contract_module TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_semantic_contract_profile_package_id, import_role, provider_key, semantic_contract_module),
  FOREIGN KEY (branch_id, projection_hash, code_semantic_contract_profile_package_id) REFERENCES code_semantic_contract_profile_package(branch_id, projection_hash, id)
);
