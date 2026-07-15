-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_primitive_type_element_type (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  element_type_id UUID NOT NULL,
  code_primitive_type_id UUID NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, element_type_id, code_primitive_type_id, position),
  FOREIGN KEY (branch_id, projection_hash, element_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_primitive_type_id) REFERENCES code_primitive_type(branch_id, projection_hash, id)
);
