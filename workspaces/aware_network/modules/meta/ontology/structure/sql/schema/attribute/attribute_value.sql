-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_value (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  type_descriptor_id UUID NOT NULL,
  enum_option_id UUID,
  class_instance_id UUID,
  inline_value_instance_id UUID,
  -- ATTRIBUTES
  primitive_value JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, type_descriptor_id),
  FOREIGN KEY (branch_id, projection_hash, inline_value_instance_id) REFERENCES inline_value_instance(branch_id, projection_hash, id)
);
