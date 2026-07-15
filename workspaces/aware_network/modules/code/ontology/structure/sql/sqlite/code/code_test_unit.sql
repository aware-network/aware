-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_test_unit (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_test_id TEXT NOT NULL,
  code_section_id TEXT NOT NULL,
  -- ATTRIBUTES
  unit_key TEXT NOT NULL,
  selector TEXT NOT NULL,
  kind TEXT NOT NULL,
  name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_test_id, unit_key, code_section_id),
  FOREIGN KEY (branch_id, projection_hash, code_test_id) REFERENCES code_test(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
