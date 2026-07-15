-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE session_member (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  session_id UUID NOT NULL,
  actor_id UUID NOT NULL,
  session_actor_config_id UUID NOT NULL,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  joined_at_unix_ms INTEGER,
  left_at_unix_ms INTEGER,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, session_id, actor_id),
  FOREIGN KEY (branch_id, projection_hash, session_id) REFERENCES session(branch_id, projection_hash, id)
);
