-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_event_node_scope (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_event_id UUID NOT NULL,
  event_config_condition_config_id UUID NOT NULL,
  projection_experience_node_identity_id UUID NOT NULL,
  object_instance_graph_branch_id UUID,
  event_config_condition_config_scope_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_experience_event_id, event_config_condition_config_id, projection_experience_node_identity_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_event_id) REFERENCES environment_experience_event(branch_id, projection_hash, id)
);
