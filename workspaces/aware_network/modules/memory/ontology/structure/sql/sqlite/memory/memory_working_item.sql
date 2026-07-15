-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_item (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  memory_working_id TEXT NOT NULL,
  attention_transition_id TEXT,
  -- ATTRIBUTES
  kind TEXT NOT NULL,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  rationale TEXT,
  summary TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, memory_working_id, kind, position),
  FOREIGN KEY (branch_id, projection_hash, memory_working_id) REFERENCES memory_working(branch_id, projection_hash, id)
);
