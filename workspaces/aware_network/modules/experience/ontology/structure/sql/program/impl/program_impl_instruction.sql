-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  sequence INTEGER NOT NULL,
  -- RELATIONSHIPS
  program_impl_id UUID NOT NULL,
  -- ATTRIBUTES
  type_ program_impl_instruction_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sequence),
  FOREIGN KEY (branch_id, projection_hash, program_impl_id) REFERENCES program_impl(branch_id, projection_hash, id)
);
