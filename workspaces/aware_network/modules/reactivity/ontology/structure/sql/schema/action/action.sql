-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE action (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  event_id UUID NOT NULL,
  config_id UUID NOT NULL,
  -- ATTRIBUTES
  execution_context JSONB NOT NULL,
  result_info TEXT,
  status action_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, event_id, config_id)
);
