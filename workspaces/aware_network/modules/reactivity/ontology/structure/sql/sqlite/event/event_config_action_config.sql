-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config_action_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  event_config_id TEXT NOT NULL,
  action_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  continue_on_fail INTEGER NOT NULL,
  execution_order INTEGER NOT NULL,
  is_enabled INTEGER NOT NULL,
  is_required INTEGER NOT NULL,
  priority INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_config_id, action_config_id),
  FOREIGN KEY (branch_id, projection_hash, event_config_id) REFERENCES event_config(branch_id, projection_hash, id)
);
