-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  id TEXT NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  object_instance_graph_branch_id TEXT,
  object_projection_graph_identity_id TEXT NOT NULL,
  -- ATTRIBUTES
  focus_scope_id TEXT NOT NULL,
  target_id TEXT,
  target_type TEXT,
  description TEXT,
  expires_at TEXT,
  is_active INTEGER NOT NULL,
  last_accessed TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, focus_scope_id, object_projection_graph_identity_id)
);
