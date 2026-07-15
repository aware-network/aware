-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_session (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  identity_session_id TEXT NOT NULL,
  active_layout_id TEXT,
  -- ATTRIBUTES
  key TEXT,
  title TEXT,
  description TEXT,
  purpose TEXT,
  status TEXT NOT NULL,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, identity_session_id),
  FOREIGN KEY (branch_id, projection_hash, active_layout_id) REFERENCES attention_session_layout(branch_id, projection_hash, id)
);
