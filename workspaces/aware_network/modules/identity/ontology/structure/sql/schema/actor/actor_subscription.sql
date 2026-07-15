-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_subscription (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_id UUID NOT NULL,
  event_config_condition_config_scope_id UUID NOT NULL,
  -- ATTRIBUTES
  addressing_policy subscription_addressing_policy NOT NULL,
  batch_mode BOOLEAN NOT NULL,
  batch_window_ms INTEGER NOT NULL,
  check_ownership BOOLEAN NOT NULL,
  description TEXT,
  action_type TEXT,
  filter_config JSONB,
  filter_mode subscription_filter_mode NOT NULL,
  is_enabled BOOLEAN NOT NULL,
  max_batch_size INTEGER NOT NULL,
  name TEXT NOT NULL,
  priority INTEGER NOT NULL,
  rate_limit_per_hour INTEGER,
  rate_limit_per_minute INTEGER,
  require_read_access BOOLEAN NOT NULL,
  status subscription_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id, name, event_config_condition_config_scope_id),
  FOREIGN KEY (branch_id, projection_hash, actor_id) REFERENCES actor(branch_id, projection_hash, id)
);
