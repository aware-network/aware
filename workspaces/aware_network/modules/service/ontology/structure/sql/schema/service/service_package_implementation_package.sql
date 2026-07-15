-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_package_implementation_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_package_id UUID NOT NULL,
  code_package_id UUID NOT NULL,
  -- ATTRIBUTES
  entrypoint TEXT,
  exclude_paths JSONB NOT NULL,
  import_root TEXT NOT NULL,
  include_paths JSONB NOT NULL,
  language code_language NOT NULL,
  manifest_relative_path TEXT NOT NULL,
  package_name TEXT NOT NULL,
  package_root TEXT NOT NULL,
  role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_package_id, code_package_id),
  FOREIGN KEY (branch_id, projection_hash, service_package_id) REFERENCES service_package(branch_id, projection_hash, id)
);
