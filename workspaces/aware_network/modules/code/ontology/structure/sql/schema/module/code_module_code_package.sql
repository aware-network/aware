-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_module_code_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_package_id UUID NOT NULL,
  code_module_id UUID NOT NULL,
  -- ATTRIBUTES
  manifest_relative_path TEXT,
  mirrors_ontology BOOLEAN NOT NULL,
  module_package_id TEXT,
  module_package_kind TEXT,
  module_relative_package_root TEXT,
  semantic_contract_capabilities TEXT[] NOT NULL,
  semantic_contract_module TEXT,
  semantic_contract_name TEXT,
  semantic_contract_owns_manifest_kinds TEXT[] NOT NULL,
  semantic_contract_provider_key TEXT,
  semantic_contract_role TEXT,
  visibility TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_module_id) REFERENCES code_module(branch_id, projection_hash, id)
);
