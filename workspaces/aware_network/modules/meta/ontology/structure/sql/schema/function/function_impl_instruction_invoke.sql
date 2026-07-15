-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_impl_instruction_invoke (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_impl_instruction_id UUID UNIQUE,
  target_function_config_id UUID NOT NULL,
  class_config_relationship_id UUID,
  -- ATTRIBUTES
  kind function_impl_invoke_kind NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_impl_instruction_id) REFERENCES function_impl_instruction(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, target_function_config_id) REFERENCES function_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_config_relationship_id) REFERENCES class_config_relationship(branch_id, projection_hash, id)
);
