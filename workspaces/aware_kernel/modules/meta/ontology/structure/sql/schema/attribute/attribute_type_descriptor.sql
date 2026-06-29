-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_type_descriptor (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  class_config_id UUID,
  enum_config_id UUID,
  primitive_config_id UUID,
  -- ATTRIBUTES
  collection_kind attribute_collection_type NOT NULL,
  kind attribute_type_descriptor_kind NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, collection_kind, kind),
  FOREIGN KEY (branch_id, projection_hash, primitive_config_id) REFERENCES primitive_config(branch_id, projection_hash, id)
);
