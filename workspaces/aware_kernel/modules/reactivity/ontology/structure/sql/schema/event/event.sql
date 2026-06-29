-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  config_id UUID NOT NULL,
  -- ATTRIBUTES
  activation_id UUID NOT NULL,
  event_type TEXT NOT NULL,
  source TEXT NOT NULL,
  status event_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, activation_id, config_id)
);
