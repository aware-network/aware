-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_impl_instruction (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_impl_id TEXT NOT NULL,
  -- ATTRIBUTES
  type_ TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_impl_id, sequence),
  FOREIGN KEY (branch_id, projection_hash, program_impl_id) REFERENCES program_impl(branch_id, projection_hash, id)
);
