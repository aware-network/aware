-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_attribute_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  type_ program_attribute_type NOT NULL,
  attribute_config_id UUID NOT NULL,
  -- RELATIONSHIPS
  program_config_id UUID NOT NULL,
  -- ATTRIBUTES
  position INTEGER,
  required BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, type_, attribute_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_config_id) REFERENCES program_config(branch_id, projection_hash, id)
);
