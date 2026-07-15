-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_input_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_config_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT NOT NULL,
  source TEXT NOT NULL,
  required BOOLEAN NOT NULL,
  default_expr JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_config_id, name, source),
  FOREIGN KEY (branch_id, projection_hash, program_config_id) REFERENCES program_config(branch_id, projection_hash, id)
);
