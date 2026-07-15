-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_layout_topology_transition_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attention_layout_topology_transition_id UUID NOT NULL,
  attention_session_section_id UUID NOT NULL,
  -- ATTRIBUTES
  order_ INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_layout_topology_transition_id, attention_session_section_id),
  FOREIGN KEY (branch_id, projection_hash, attention_layout_topology_transition_id) REFERENCES attention_layout_topology_transition(branch_id, projection_hash, id)
);
