-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE api_package_language_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  api_package_id TEXT NOT NULL,
  code_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  exclude_paths TEXT NOT NULL,
  import_root TEXT NOT NULL,
  include_paths TEXT NOT NULL,
  language TEXT NOT NULL,
  manifest_relative_path TEXT NOT NULL,
  output_key TEXT NOT NULL,
  package_name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, api_package_id, code_package_id),
  FOREIGN KEY (branch_id, projection_hash, api_package_id) REFERENCES api_package(branch_id, projection_hash, id)
);
