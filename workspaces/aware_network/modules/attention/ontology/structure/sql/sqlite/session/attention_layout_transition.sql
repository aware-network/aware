-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_layout_transition (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attention_session_layout_id TEXT NOT NULL,
  previous_transition_id TEXT,
  topology_transition_id TEXT,
  -- ATTRIBUTES
  client_intent_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  transition_kind TEXT NOT NULL,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_session_layout_id, client_intent_id),
  FOREIGN KEY (branch_id, projection_hash, attention_session_layout_id) REFERENCES attention_session_layout(branch_id, projection_hash, id)
);
