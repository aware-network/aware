-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_code (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_package_id TEXT NOT NULL,
  -- ATTRIBUTES
  relative_path TEXT NOT NULL,
  path_role TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_id, relative_path),
  FOREIGN KEY (branch_id, projection_hash, code_package_id) REFERENCES code_package(branch_id, projection_hash, id)
);
