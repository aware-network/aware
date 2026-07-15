-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE condition_config_class_config (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  condition_config_id UUID NOT NULL,
  class_config_id UUID NOT NULL,
  -- ATTRIBUTES
  class_logic condition_logic_strategy NOT NULL,
  class_selection class_selection_mode NOT NULL,
  require_existence BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, condition_config_id, class_config_id),
  FOREIGN KEY (branch_id, projection_hash, condition_config_id) REFERENCES condition_config(branch_id, projection_hash, id)
);
