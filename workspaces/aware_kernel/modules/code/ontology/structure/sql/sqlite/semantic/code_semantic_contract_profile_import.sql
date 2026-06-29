-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_semantic_contract_profile_import (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_semantic_contract_profile_id TEXT NOT NULL,
  imported_profile_id TEXT NOT NULL,
  -- ATTRIBUTES
  import_key TEXT NOT NULL,
  required INTEGER NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_semantic_contract_profile_id, import_key, imported_profile_id),
  FOREIGN KEY (branch_id, projection_hash, code_semantic_contract_profile_id) REFERENCES code_semantic_contract_profile(branch_id, projection_hash, id)
);
