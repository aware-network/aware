-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attribute_type_descriptor (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  class_config_id TEXT,
  enum_config_id TEXT,
  primitive_config_id TEXT,
  -- ATTRIBUTES
  collection_kind TEXT NOT NULL,
  kind TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, collection_kind, kind),
  FOREIGN KEY (branch_id, projection_hash, primitive_config_id) REFERENCES primitive_config(branch_id, projection_hash, id)
);
