-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_value_link (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attribute_value_id TEXT NOT NULL,
  child_id TEXT NOT NULL,
  -- ATTRIBUTES
  role TEXT NOT NULL,
  position INTEGER,
  identity_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attribute_value_id, child_id),
  FOREIGN KEY (branch_id, projection_hash, attribute_value_id) REFERENCES attribute_value(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, child_id) REFERENCES attribute_value(branch_id, projection_hash, id)
);
