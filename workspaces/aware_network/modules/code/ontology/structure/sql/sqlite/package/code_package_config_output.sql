-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_config_output (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_package_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  output_key TEXT NOT NULL,
  kind TEXT NOT NULL,
  producer_key TEXT,
  artifact_family TEXT,
  artifact_role TEXT,
  package_output_key TEXT,
  target_provider_key TEXT,
  target_input_key TEXT,
  target_semantic_owner TEXT,
  target_package_family TEXT,
  target_semantic_kind TEXT,
  media_type TEXT,
  runtime_contract_version TEXT,
  required_for TEXT NOT NULL,
  required INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_config_id, output_key),
  FOREIGN KEY (branch_id, projection_hash, code_package_config_id) REFERENCES code_package_config(branch_id, projection_hash, id)
);
