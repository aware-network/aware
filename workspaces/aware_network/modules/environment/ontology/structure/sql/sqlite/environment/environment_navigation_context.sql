-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_navigation_context (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_session_id TEXT NOT NULL,
  session_thread_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT,
  is_default INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_session_id, key)
);
