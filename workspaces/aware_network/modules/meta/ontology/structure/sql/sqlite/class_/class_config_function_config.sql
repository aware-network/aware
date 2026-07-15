-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_config_function_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  class_config_id TEXT NOT NULL,
  function_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  is_public INTEGER NOT NULL,
  is_constructor INTEGER NOT NULL,
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_config_id, function_config_id),
  FOREIGN KEY (branch_id, projection_hash, class_config_id) REFERENCES class_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_config_id) REFERENCES function_config(branch_id, projection_hash, id)
);
