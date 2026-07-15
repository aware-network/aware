-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus_evidence (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  actor_focus_id TEXT NOT NULL,
  -- ATTRIBUTES
  evidence_key TEXT NOT NULL,
  kind TEXT NOT NULL,
  source_type TEXT,
  source_id TEXT,
  source_key TEXT,
  weight_delta REAL NOT NULL,
  confidence REAL,
  observed_at TEXT,
  expires_at TEXT,
  rationale TEXT,
  metadata TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_focus_id, evidence_key),
  FOREIGN KEY (branch_id, projection_hash, actor_focus_id) REFERENCES actor_focus(branch_id, projection_hash, id)
);
