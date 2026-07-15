-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  process_id TEXT NOT NULL,
  parent_id TEXT,
  thread_config_id TEXT NOT NULL,
  image_id TEXT UNIQUE,
  overview_content_id TEXT,
  backlog_chain_id TEXT,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  description TEXT,
  is_main INTEGER NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, process_id, key, thread_config_id)
);
