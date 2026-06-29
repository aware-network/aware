-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_test (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_id UUID NOT NULL,
  framework_id UUID NOT NULL,
  -- ATTRIBUTES
  discovery_kind TEXT NOT NULL,
  selector_prefix TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_id, framework_id),
  FOREIGN KEY (branch_id, projection_hash, code_id) REFERENCES code(branch_id, projection_hash, id)
);
