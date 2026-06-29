-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_condition (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  event_id UUID NOT NULL,
  condition_id UUID NOT NULL,
  config_id UUID NOT NULL,
  -- ATTRIBUTES
  evaluation_context JSONB NOT NULL,
  matched BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id, condition_id, config_id),
  FOREIGN KEY (branch_id, projection_hash, event_id) REFERENCES event(branch_id, projection_hash, id)
);
