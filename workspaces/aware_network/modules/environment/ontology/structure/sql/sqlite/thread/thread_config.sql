-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  process_config_id TEXT NOT NULL,
  image_id TEXT UNIQUE,
  -- ATTRIBUTES
  description TEXT,
  narrative TEXT,
  intent TEXT,
  state_prompt_template TEXT,
  key TEXT NOT NULL,
  title TEXT,
  workspace_view_key TEXT,
  position INTEGER,
  is_default INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, process_config_id, key),
  FOREIGN KEY (branch_id, projection_hash, process_config_id) REFERENCES process_config(branch_id, projection_hash, id)
);
