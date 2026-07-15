-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE attention_session_layout (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attention_session_id TEXT NOT NULL,
  layout_id TEXT NOT NULL,
  layout_config_id TEXT,
  active_section_id TEXT,
  active_topology_transition_id TEXT,
  active_layout_transition_id TEXT,
  -- ATTRIBUTES
  key TEXT,
  order_ INTEGER NOT NULL,
  is_active INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, attention_session_id, layout_id),
  FOREIGN KEY (branch_id, projection_hash, attention_session_id) REFERENCES attention_session(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_section_id) REFERENCES attention_session_section(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_topology_transition_id) REFERENCES attention_layout_topology_transition(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, active_layout_transition_id) REFERENCES attention_layout_transition(branch_id, projection_hash, id)
);
