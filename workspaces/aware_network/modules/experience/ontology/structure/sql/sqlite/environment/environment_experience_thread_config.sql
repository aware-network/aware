-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_thread_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_experience_process_config_id TEXT NOT NULL,
  thread_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  intent TEXT,
  key TEXT NOT NULL,
  narrative TEXT,
  position INTEGER,
  title TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_experience_process_config_id, key, thread_config_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_process_config_id) REFERENCES environment_experience_process_config(branch_id, projection_hash, id)
);
