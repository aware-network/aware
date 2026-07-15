-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE focus_scope (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  focus_id TEXT,
  observable_id TEXT,
  -- ATTRIBUTES
  title TEXT NOT NULL,
  description TEXT,
  rationale TEXT,
  expires_at TEXT,
  is_active INTEGER NOT NULL,
  last_accessed TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, title)
);
