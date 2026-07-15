-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_layout_topology_transition (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attention_session_layout_id UUID NOT NULL,
  previous_topology_transition_id UUID,
  -- ATTRIBUTES
  client_intent_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  transition_kind TEXT NOT NULL,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_session_layout_id, client_intent_id)
);
