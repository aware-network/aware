-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE node_config_service_code_package (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  slot_key TEXT NOT NULL,
  package_name TEXT NOT NULL,
  language TEXT NOT NULL,
  -- RELATIONSHIPS
  node_config_service_target_id TEXT NOT NULL,
  service_config_code_package_config_id TEXT,
  code_package_id TEXT,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, slot_key, package_name, language),
  FOREIGN KEY (branch_id, projection_hash, node_config_service_target_id) REFERENCES node_config_service_target(branch_id, projection_hash, id)
);
