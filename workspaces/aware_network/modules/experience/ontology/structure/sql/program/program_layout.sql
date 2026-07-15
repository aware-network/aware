-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_layout (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  key TEXT NOT NULL,
  -- RELATIONSHIPS
  program_id UUID NOT NULL,
  config_id UUID,
  -- ATTRIBUTES
  is_active BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key),
  FOREIGN KEY (branch_id, projection_hash, program_id) REFERENCES program(branch_id, projection_hash, id)
);
