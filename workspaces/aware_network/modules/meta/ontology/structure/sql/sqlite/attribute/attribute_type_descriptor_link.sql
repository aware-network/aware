-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_type_descriptor_link (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attribute_type_descriptor_id TEXT NOT NULL,
  child_id TEXT NOT NULL,
  -- ATTRIBUTES
  role TEXT NOT NULL,
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attribute_type_descriptor_id, role, position, child_id),
  FOREIGN KEY (branch_id, projection_hash, attribute_type_descriptor_id) REFERENCES attribute_type_descriptor(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, child_id) REFERENCES attribute_type_descriptor(branch_id, projection_hash, id)
);
