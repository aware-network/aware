-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  process_id UUID NOT NULL,
  parent_id UUID,
  thread_config_id UUID NOT NULL,
  image_id UUID UNIQUE,
  overview_content_id UUID,
  backlog_chain_id UUID,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  description TEXT,
  is_main BOOLEAN NOT NULL,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, process_id, key, thread_config_id)
);
