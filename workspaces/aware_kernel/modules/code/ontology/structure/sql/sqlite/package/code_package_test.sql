-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_test (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_package_id TEXT NOT NULL,
  code_test_id TEXT NOT NULL,
  -- ATTRIBUTES
  relative_path TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_id, relative_path, code_test_id),
  FOREIGN KEY (branch_id, projection_hash, code_package_id) REFERENCES code_package(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_test_id) REFERENCES code_test(branch_id, projection_hash, id)
);
