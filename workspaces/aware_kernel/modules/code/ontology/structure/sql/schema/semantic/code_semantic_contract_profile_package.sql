-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_semantic_contract_profile_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_package_id UUID NOT NULL,
  semantic_contract_profile_id UUID NOT NULL,
  -- ATTRIBUTES
  manifest_relative_path TEXT,
  profile_key TEXT NOT NULL,
  profile_package_key TEXT NOT NULL,
  runtime_import_mode TEXT NOT NULL,
  runtime_import_required BOOLEAN NOT NULL,
  source_workspace_handle TEXT,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, profile_package_key, code_package_id, semantic_contract_profile_id)
);
