-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_value (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  type_descriptor_id TEXT NOT NULL,
  enum_option_id TEXT,
  class_instance_id TEXT,
  inline_value_instance_id TEXT,
  -- ATTRIBUTES
  primitive_value TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, type_descriptor_id),
  FOREIGN KEY (branch_id, projection_hash, inline_value_instance_id) REFERENCES inline_value_instance(branch_id, projection_hash, id)
);
