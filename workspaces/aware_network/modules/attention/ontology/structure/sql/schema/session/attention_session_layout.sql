-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_session_layout (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  attention_session_id UUID NOT NULL,
  layout_id UUID NOT NULL,
  layout_config_id UUID,
  active_section_id UUID,
  active_topology_transition_id UUID,
  active_layout_transition_id UUID,
  -- ATTRIBUTES
  key TEXT,
  order_ INTEGER NOT NULL,
  is_active BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_session_id, layout_id),
  FOREIGN KEY (branch_id, projection_hash, attention_session_id) REFERENCES attention_session(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_section_id) REFERENCES attention_session_section(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_topology_transition_id) REFERENCES attention_layout_topology_transition(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_layout_transition_id) REFERENCES attention_layout_transition(branch_id, projection_hash, id)
);
