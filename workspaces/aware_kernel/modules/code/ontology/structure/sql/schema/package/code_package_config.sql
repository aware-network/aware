-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  config_key TEXT NOT NULL,
  provider_key TEXT NOT NULL,
  semantic_owner TEXT NOT NULL,
  contract TEXT NOT NULL,
  package_role TEXT,
  manifest_kind TEXT NOT NULL,
  manifest_filename TEXT NOT NULL,
  semantic_package_family TEXT,
  semantic_package_kind TEXT,
  semantic_projection_name TEXT,
  semantic_root_kind TEXT,
  default_surface TEXT,
  materialization_capability TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, config_key)
);
