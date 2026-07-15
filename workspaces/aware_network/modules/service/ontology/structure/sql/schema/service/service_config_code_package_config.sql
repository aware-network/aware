-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_config_code_package_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_config_id UUID NOT NULL,
  code_package_config_id UUID NOT NULL,
  -- ATTRIBUTES
  slot_key TEXT NOT NULL,
  cardinality service_config_code_package_config_cardinality NOT NULL,
  required BOOLEAN NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_config_id, slot_key, code_package_config_id),
  FOREIGN KEY (branch_id, projection_hash, service_config_id) REFERENCES service_config(branch_id, projection_hash, id)
);
