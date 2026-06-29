-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_config_relationship (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  class_config_id TEXT NOT NULL,
  target_class_config_id TEXT NOT NULL,
  reified_from_relationship_id TEXT,
  -- ATTRIBUTES
  relationship_key TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  identity_rail TEXT,
  forward_required INTEGER NOT NULL,
  forward_loading_strategy TEXT,
  reverse_loading_strategy TEXT,
  reified_role TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_config_id, relationship_key, target_class_config_id),
  FOREIGN KEY (branch_id, projection_hash, class_config_id) REFERENCES class_config(branch_id, projection_hash, id)
);
