-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_service_code_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  slot_key TEXT NOT NULL,
  package_name TEXT NOT NULL,
  language code_language NOT NULL,
  -- RELATIONSHIPS
  node_config_service_target_id UUID NOT NULL,
  service_config_code_package_config_id UUID,
  code_package_id UUID,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, slot_key, package_name, language),
  FOREIGN KEY (branch_id, projection_hash, node_config_service_target_id) REFERENCES node_config_service_target(branch_id, projection_hash, id)
);
