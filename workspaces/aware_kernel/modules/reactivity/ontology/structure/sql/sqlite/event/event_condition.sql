-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_condition (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  event_id TEXT NOT NULL,
  condition_id TEXT NOT NULL,
  config_id TEXT NOT NULL,
  -- ATTRIBUTES
  evaluation_context TEXT NOT NULL,
  matched INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id, condition_id, config_id),
  FOREIGN KEY (branch_id, projection_hash, event_id) REFERENCES event(branch_id, projection_hash, id)
);
