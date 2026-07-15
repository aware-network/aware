-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE interface_environment (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  environment_id UUID NOT NULL,
  -- RELATIONSHIPS
  interface_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, environment_id),
  FOREIGN KEY (branch_id, projection_hash, interface_id) REFERENCES interface(branch_id, projection_hash, id)
);
