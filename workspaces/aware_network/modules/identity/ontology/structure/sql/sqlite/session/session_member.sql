-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_member (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  session_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  session_actor_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  joined_at_unix_ms INTEGER,
  left_at_unix_ms INTEGER,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_id, actor_id),
  FOREIGN KEY (branch_id, projection_hash, session_id) REFERENCES session(branch_id, projection_hash, id)
);
