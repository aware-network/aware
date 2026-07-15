-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_config_attribute_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  function_config_id TEXT NOT NULL,
  attribute_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  position INTEGER NOT NULL,
  type_ TEXT NOT NULL,
  is_identity_key INTEGER NOT NULL,
  identity_key_origin TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_config_id, name, type_),
  FOREIGN KEY (branch_id, projection_hash, function_config_id) REFERENCES function_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, attribute_config_id) REFERENCES attribute_config(branch_id, projection_hash, id)
);
