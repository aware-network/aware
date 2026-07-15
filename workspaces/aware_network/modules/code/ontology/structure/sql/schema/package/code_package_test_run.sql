-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_package_test_run (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_package_test_id UUID NOT NULL,
  -- ATTRIBUTES
  run_key TEXT NOT NULL,
  backend_kind TEXT NOT NULL,
  status code_test_run_status NOT NULL,
  started_at_utc TIMESTAMPTZ,
  finished_at_utc TIMESTAMPTZ,
  duration_s NUMERIC,
  selected_unit_count INTEGER NOT NULL,
  total_tests INTEGER NOT NULL,
  passed_tests INTEGER NOT NULL,
  failed_tests INTEGER NOT NULL,
  skipped_tests INTEGER NOT NULL,
  unsupported_tests INTEGER NOT NULL,
  error TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_package_test_id, run_key),
  FOREIGN KEY (branch_id, projection_hash, code_package_test_id) REFERENCES code_package_test(branch_id, projection_hash, id)
);
