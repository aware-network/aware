-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_instruction_construct (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_instruction_id UUID UNIQUE,
  target_class_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_impl_instruction_id) REFERENCES function_impl_instruction(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, target_class_config_id) REFERENCES class_config(branch_id, projection_hash, id)
);
