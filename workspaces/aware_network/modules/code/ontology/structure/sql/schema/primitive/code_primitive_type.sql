-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_primitive_type (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  item_type_id UUID,
  key_type_id UUID,
  value_type_id UUID,
  -- ATTRIBUTES
  signature TEXT NOT NULL,
  base_type code_primitive_base_type NOT NULL,
  constraints JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, signature),
  FOREIGN KEY (branch_id, projection_hash, item_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, key_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, value_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id)
);
