-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE experience_package_language_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  experience_package_id TEXT NOT NULL,
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
  sources_root TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, experience_package_id, code_package_id),
  FOREIGN KEY (branch_id, projection_hash, experience_package_id) REFERENCES experience_package(branch_id, projection_hash, id)
);
