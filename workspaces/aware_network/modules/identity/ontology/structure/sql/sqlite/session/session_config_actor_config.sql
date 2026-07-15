-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_config_actor_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  session_config_id TEXT NOT NULL,
  actor_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  purpose TEXT,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_config_id, actor_config_id),
  FOREIGN KEY (branch_id, projection_hash, session_config_id) REFERENCES session_config(branch_id, projection_hash, id)
);
