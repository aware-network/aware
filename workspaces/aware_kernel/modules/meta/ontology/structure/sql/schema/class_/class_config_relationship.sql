-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE class_config_relationship (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  class_config_id UUID NOT NULL,
  target_class_config_id UUID NOT NULL,
  reified_from_relationship_id UUID,
  -- ATTRIBUTES
  relationship_key TEXT NOT NULL,
  relationship_type class_config_relationship_type NOT NULL,
  identity_rail class_config_relationship_identity_rail,
  forward_required BOOLEAN NOT NULL,
  forward_loading_strategy class_config_relationship_side_loading_strategy,
  reverse_loading_strategy class_config_relationship_side_loading_strategy,
  reified_role class_config_relationship_reified_role,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, class_config_id, relationship_key, target_class_config_id),
  FOREIGN KEY (branch_id, projection_hash, class_config_id) REFERENCES class_config(branch_id, projection_hash, id)
);
