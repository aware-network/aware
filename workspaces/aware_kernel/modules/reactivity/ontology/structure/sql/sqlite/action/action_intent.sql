-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_intent (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  event_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  payload_model_id TEXT UNIQUE,
  -- ATTRIBUTES
  action_payload TEXT NOT NULL,
  action_type TEXT,
  actor_id TEXT,
  actor_subscription_id TEXT,
  intent_key TEXT NOT NULL,
  priority INTEGER NOT NULL,
  status TEXT NOT NULL,
  subscription_filter_config TEXT NOT NULL,
  target_actor_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id, intent_key, config_id)
);
