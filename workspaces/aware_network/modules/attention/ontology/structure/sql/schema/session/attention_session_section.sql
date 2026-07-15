-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_session_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attention_session_layout_id UUID NOT NULL,
  layout_section_id UUID NOT NULL,
  section_id UUID NOT NULL,
  active_transition_id UUID,
  -- ATTRIBUTES
  section_key TEXT,
  order_ INTEGER NOT NULL,
  is_active BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_session_layout_id, layout_section_id, section_id),
  FOREIGN KEY (branch_id, projection_hash, attention_session_layout_id) REFERENCES attention_session_layout(branch_id, projection_hash, id)
);
