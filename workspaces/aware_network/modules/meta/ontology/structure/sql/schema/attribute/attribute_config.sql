-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  type_descriptor_id UUID NOT NULL,
  code_section_attribute_id UUID,
  -- ATTRIBUTES
  owner_key TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  default_value TEXT,
  is_primary BOOLEAN NOT NULL,
  is_public BOOLEAN NOT NULL,
  is_required BOOLEAN NOT NULL,
  is_unique BOOLEAN NOT NULL,
  is_virtual BOOLEAN NOT NULL,
  exclude_serialization BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, owner_key, name),
  FOREIGN KEY (branch_id, projection_hash, type_descriptor_id) REFERENCES attribute_type_descriptor(branch_id, projection_hash, id)
);
