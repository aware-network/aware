-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE content_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- ATTRIBUTES
  package_name TEXT NOT NULL,
  package_root TEXT,
  manifest_relative_path TEXT,
  title TEXT,
  package_kind TEXT,
  source_provider_key TEXT,
  source_ref TEXT,
  runtime_contract_version TEXT,
  provider_payload TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, package_name)
);
