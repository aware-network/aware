-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  type_descriptor_id TEXT NOT NULL,
  code_section_attribute_id TEXT,
  -- ATTRIBUTES
  owner_key TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  default_value TEXT,
  is_primary INTEGER NOT NULL,
  is_public INTEGER NOT NULL,
  is_required INTEGER NOT NULL,
  is_unique INTEGER NOT NULL,
  is_virtual INTEGER NOT NULL,
  exclude_serialization INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, owner_key, name),
  FOREIGN KEY (branch_id, projection_hash, type_descriptor_id) REFERENCES attribute_type_descriptor(branch_id, projection_hash, id)
);
