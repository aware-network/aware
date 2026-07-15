-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_subscription_event (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_subscription_id UUID NOT NULL,
  event_config_condition_config_scope_event_id UUID NOT NULL,
  -- ATTRIBUTES
  reason TEXT,
  status subscription_activation_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_subscription_id, event_config_condition_config_scope_event_id),
  FOREIGN KEY (branch_id, projection_hash, actor_subscription_id) REFERENCES actor_subscription(branch_id, projection_hash, id)
);
