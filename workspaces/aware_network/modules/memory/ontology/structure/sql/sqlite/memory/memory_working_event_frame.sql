-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_event_frame (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  memory_working_item_id TEXT UNIQUE,
  event_id TEXT NOT NULL,
  -- ATTRIBUTES
  event_config_id TEXT,
  event_activation_id TEXT,
  event_type TEXT,
  event_source TEXT,
  event_status TEXT,
  commit_branch_id TEXT,
  commit_projection_hash TEXT,
  commit_id TEXT,
  object_instance_graph_id TEXT,
  object_instance_graph_commit_id TEXT,
  action_intent_id TEXT,
  intent_key TEXT,
  action_config_id TEXT,
  action_execution_id TEXT,
  action_execution_key TEXT,
  api_call_key TEXT,
  action_binding_id TEXT,
  action_experience_id TEXT,
  environment_profile_id TEXT,
  environment_event_id TEXT,
  invocation_config_id TEXT,
  endpoint_id TEXT,
  actor_subscription_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id),
  FOREIGN KEY (branch_id, projection_hash, memory_working_item_id) REFERENCES memory_working_item(branch_id, projection_hash, id)
);
