-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action_intent (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  event_id UUID NOT NULL,
  config_id UUID NOT NULL,
  payload_model_id UUID UNIQUE,
  -- ATTRIBUTES
  action_payload JSONB NOT NULL,
  action_type TEXT,
  actor_id UUID,
  actor_subscription_id UUID,
  intent_key TEXT NOT NULL,
  priority INTEGER NOT NULL,
  status action_intent_status NOT NULL,
  subscription_filter_config JSONB NOT NULL,
  target_actor_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id, intent_key, config_id)
);
