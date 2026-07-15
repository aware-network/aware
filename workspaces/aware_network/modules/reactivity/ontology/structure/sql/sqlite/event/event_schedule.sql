-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE event_schedule (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  content_id TEXT,
  event_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  end_time TEXT NOT NULL,
  iteration_count INTEGER,
  key TEXT NOT NULL,
  location TEXT,
  rrule TEXT,
  start_time TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, key, event_config_id)
);
