-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE process (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_profile_id TEXT NOT NULL,
  parent_id TEXT,
  process_config_id TEXT NOT NULL,
  image_id TEXT UNIQUE,
  overview_content_id TEXT,
  backlog_chain_id TEXT,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  description TEXT,
  priority_level TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_profile_id, key, process_config_id)
);
