-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_focus_transition (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  id UUID NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  attention_session_section_id UUID NOT NULL,
  previous_transition_id UUID,
  focus_scope_id UUID NOT NULL,
  focus_id UUID,
  observable_id UUID,
  object_projection_graph_identity_id UUID,
  object_instance_graph_branch_id UUID,
  object_instance_graph_commit_id UUID,
  -- ATTRIBUTES
  transition_key TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  transition_kind TEXT NOT NULL,
  rationale TEXT,
  source_kind TEXT,
  source_ref TEXT,
  metadata_json JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, attention_session_section_id, transition_key, focus_scope_id),
  FOREIGN KEY (branch_id, projection_hash, previous_transition_id) REFERENCES attention_focus_transition(branch_id, projection_hash, id)
);
