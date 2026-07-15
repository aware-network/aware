-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_session_section (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attention_session_layout_id TEXT NOT NULL,
  layout_section_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  active_transition_id TEXT,
  -- ATTRIBUTES
  section_key TEXT,
  order_ INTEGER NOT NULL,
  is_active INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_session_layout_id, layout_section_id, section_id),
  FOREIGN KEY (branch_id, projection_hash, attention_session_layout_id) REFERENCES attention_session_layout(branch_id, projection_hash, id)
);
