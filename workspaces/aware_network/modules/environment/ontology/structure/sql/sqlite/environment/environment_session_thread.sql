-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_session_thread (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_session_id TEXT NOT NULL,
  thread_id TEXT NOT NULL,
  thread_layout_id TEXT NOT NULL,
  attention_session_id TEXT,
  -- ATTRIBUTES
  key TEXT,
  title TEXT,
  status TEXT NOT NULL,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_session_id, thread_id, thread_layout_id)
);
