-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config_condition_config_scope (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  event_config_condition_config_id UUID NOT NULL,
  object_instance_graph_identity_id UUID NOT NULL,
  object_instance_graph_branch_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_config_condition_config_id, object_instance_graph_identity_id)
);
