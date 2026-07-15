-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_config_attribute_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_config_id UUID NOT NULL,
  attribute_config_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  position INTEGER NOT NULL,
  type_ function_attribute_type NOT NULL,
  is_identity_key BOOLEAN NOT NULL,
  identity_key_origin function_identity_key_origin NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_config_id, name, type_),
  FOREIGN KEY (branch_id, projection_hash, function_config_id) REFERENCES function_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, attribute_config_id) REFERENCES attribute_config(branch_id, projection_hash, id)
);
