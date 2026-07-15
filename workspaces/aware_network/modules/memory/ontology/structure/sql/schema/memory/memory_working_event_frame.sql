-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_event_frame (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  memory_working_item_id UUID UNIQUE,
  event_id UUID NOT NULL,
  -- ATTRIBUTES
  event_config_id UUID,
  event_activation_id UUID,
  event_type TEXT,
  event_source TEXT,
  event_status TEXT,
  commit_branch_id UUID,
  commit_projection_hash TEXT,
  commit_id UUID,
  object_instance_graph_id UUID,
  object_instance_graph_commit_id UUID,
  action_intent_id UUID,
  intent_key TEXT,
  action_config_id UUID,
  action_execution_id UUID,
  action_execution_key TEXT,
  api_call_key UUID,
  action_binding_id UUID,
  action_experience_id UUID,
  environment_profile_id UUID,
  environment_event_id UUID,
  invocation_config_id UUID,
  endpoint_id UUID,
  actor_subscription_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id),
  FOREIGN KEY (branch_id, projection_hash, memory_working_item_id) REFERENCES memory_working_item(branch_id, projection_hash, id)
);
