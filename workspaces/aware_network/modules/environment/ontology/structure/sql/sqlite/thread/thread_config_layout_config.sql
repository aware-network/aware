-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_config_layout_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  thread_config_id TEXT NOT NULL,
  layout_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  position INTEGER,
  narrative TEXT,
  intent TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, thread_config_id, layout_config_id),
  FOREIGN KEY (branch_id, projection_hash, thread_config_id) REFERENCES thread_config(branch_id, projection_hash, id)
);
