-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_config_runtime_context (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_package_config_id UUID NOT NULL,
  -- ATTRIBUTES
  context_key TEXT NOT NULL,
  kind code_package_config_runtime_context_kind NOT NULL,
  package_name TEXT,
  projection_name TEXT,
  runtime_contract_version TEXT,
  required BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_config_id, context_key),
  FOREIGN KEY (branch_id, projection_hash, code_package_config_id) REFERENCES code_package_config(branch_id, projection_hash, id)
);
