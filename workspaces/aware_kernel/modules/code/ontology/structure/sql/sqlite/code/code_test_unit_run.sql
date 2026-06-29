-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_test_unit_run (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_package_test_run_id TEXT NOT NULL,
  code_test_unit_id TEXT NOT NULL,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  selector TEXT NOT NULL,
  duration_s REAL,
  failures TEXT NOT NULL,
  error TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_test_run_id, code_test_unit_id),
  FOREIGN KEY (branch_id, projection_hash, code_package_test_run_id) REFERENCES code_package_test_run(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_test_unit_id) REFERENCES code_test_unit(branch_id, projection_hash, id)
);
