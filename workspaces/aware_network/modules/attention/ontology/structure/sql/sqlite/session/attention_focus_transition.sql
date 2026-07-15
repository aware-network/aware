-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_focus_transition (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  id TEXT NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  attention_session_section_id TEXT NOT NULL,
  previous_transition_id TEXT,
  focus_scope_id TEXT NOT NULL,
  focus_id TEXT,
  observable_id TEXT,
  object_projection_graph_identity_id TEXT,
  object_instance_graph_branch_id TEXT,
  object_instance_graph_commit_id TEXT,
  -- ATTRIBUTES
  transition_key TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  transition_kind TEXT NOT NULL,
  rationale TEXT,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, attention_session_section_id, transition_key, focus_scope_id),
  FOREIGN KEY (branch_id, projection_hash, previous_transition_id) REFERENCES attention_focus_transition(branch_id, projection_hash, id)
);
