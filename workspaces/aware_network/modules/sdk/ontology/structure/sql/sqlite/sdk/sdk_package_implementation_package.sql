-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE sdk_package_implementation_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  sdk_package_id TEXT NOT NULL,
  code_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  entrypoint TEXT,
  exclude_paths TEXT NOT NULL,
  import_root TEXT NOT NULL,
  include_paths TEXT NOT NULL,
  language TEXT NOT NULL,
  manifest_relative_path TEXT NOT NULL,
  package_name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sdk_package_id, code_package_id),
  FOREIGN KEY (branch_id, projection_hash, sdk_package_id) REFERENCES sdk_package(branch_id, projection_hash, id)
);
