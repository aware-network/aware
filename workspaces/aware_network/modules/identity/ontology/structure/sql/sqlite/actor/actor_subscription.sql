-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_subscription (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  actor_id TEXT NOT NULL,
  event_config_condition_config_scope_id TEXT NOT NULL,
  -- ATTRIBUTES
  addressing_policy TEXT NOT NULL,
  batch_mode INTEGER NOT NULL,
  batch_window_ms INTEGER NOT NULL,
  check_ownership INTEGER NOT NULL,
  description TEXT,
  action_type TEXT,
  filter_config TEXT,
  filter_mode TEXT NOT NULL,
  is_enabled INTEGER NOT NULL,
  max_batch_size INTEGER NOT NULL,
  name TEXT NOT NULL,
  priority INTEGER NOT NULL,
  rate_limit_per_hour INTEGER,
  rate_limit_per_minute INTEGER,
  require_read_access INTEGER NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id, name, event_config_condition_config_scope_id),
  FOREIGN KEY (branch_id, projection_hash, actor_id) REFERENCES actor(branch_id, projection_hash, id)
);
