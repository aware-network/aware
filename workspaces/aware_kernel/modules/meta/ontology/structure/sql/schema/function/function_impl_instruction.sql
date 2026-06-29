-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_instruction (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_id UUID NOT NULL,
  -- ATTRIBUTES
  type_ function_impl_instruction_type NOT NULL,
  sequence INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_impl_id, type_, sequence),
  FOREIGN KEY (branch_id, projection_hash, function_impl_id) REFERENCES function_impl(branch_id, projection_hash, id)
);
