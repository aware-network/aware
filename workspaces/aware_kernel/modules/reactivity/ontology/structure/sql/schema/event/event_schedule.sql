-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_schedule (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  content_id UUID,
  event_config_id UUID NOT NULL,
  -- ATTRIBUTES
  end_time TIMESTAMPTZ NOT NULL,
  iteration_count INTEGER,
  key TEXT NOT NULL,
  location TEXT,
  rrule TEXT,
  start_time TIMESTAMPTZ NOT NULL,
  status event_schedule_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key, event_config_id)
);
