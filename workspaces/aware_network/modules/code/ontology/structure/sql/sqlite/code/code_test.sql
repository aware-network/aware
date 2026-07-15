-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_test (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_id TEXT NOT NULL,
  framework_id TEXT NOT NULL,
  -- ATTRIBUTES
  discovery_kind TEXT NOT NULL,
  selector_prefix TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_id, framework_id),
  FOREIGN KEY (branch_id, projection_hash, code_id) REFERENCES code(branch_id, projection_hash, id)
);
