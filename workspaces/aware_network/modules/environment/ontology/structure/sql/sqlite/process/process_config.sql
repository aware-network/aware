-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE process_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  environment_profile_config_id TEXT NOT NULL,
  image_id TEXT UNIQUE,
  -- ATTRIBUTES
  description TEXT,
  narrative TEXT,
  intent TEXT,
  key TEXT NOT NULL,
  shape TEXT,
  title TEXT,
  type_ TEXT NOT NULL,
  position INTEGER,
  is_default INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_profile_config_id, key),
  FOREIGN KEY (branch_id, projection_hash, environment_profile_config_id) REFERENCES environment_profile_config(branch_id, projection_hash, id)
);
