-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_config_condition_config_scope_event (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  event_config_condition_config_scope_id UUID NOT NULL,
  event_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_config_condition_config_scope_id, event_id),
  FOREIGN KEY (branch_id, projection_hash, event_config_condition_config_scope_id) REFERENCES event_config_condition_config_scope(branch_id, projection_hash, id)
);
