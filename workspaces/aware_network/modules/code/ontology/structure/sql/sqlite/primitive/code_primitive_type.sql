-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_primitive_type (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  item_type_id TEXT,
  key_type_id TEXT,
  value_type_id TEXT,
  -- ATTRIBUTES
  signature TEXT NOT NULL,
  base_type TEXT NOT NULL,
  constraints TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, signature),
  FOREIGN KEY (branch_id, projection_hash, item_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, key_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, value_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id)
);
