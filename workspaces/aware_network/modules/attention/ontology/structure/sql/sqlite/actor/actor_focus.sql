-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  actor_id TEXT NOT NULL,
  focus_id TEXT NOT NULL,
  -- ATTRIBUTES
  level TEXT,
  weight REAL NOT NULL,
  weight_algorithm TEXT,
  weight_computed_at TEXT,
  evidence_count INTEGER NOT NULL,
  last_evidence_at TEXT,
  expires_at TEXT,
  is_active INTEGER NOT NULL,
  last_accessed TEXT,
  updated_at TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id, focus_id)
);
