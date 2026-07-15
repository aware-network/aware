-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_config_input (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_package_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  input_key TEXT NOT NULL,
  kind TEXT NOT NULL,
  artifact_family TEXT,
  artifact_role TEXT,
  package_family TEXT,
  semantic_kind TEXT,
  runtime_contract_version TEXT,
  required INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_config_id, input_key),
  FOREIGN KEY (branch_id, projection_hash, code_package_config_id) REFERENCES code_package_config(branch_id, projection_hash, id)
);
