-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE environment_experience_view_event_transition (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  transition_key TEXT NOT NULL,
  source_view_id UUID NOT NULL,
  trigger_event_id UUID NOT NULL,
  target_section_graph_binding_id UUID NOT NULL,
  -- RELATIONSHIPS
  environment_experience_profile_config_id UUID NOT NULL,
  -- ATTRIBUTES
  name TEXT,
  rationale TEXT,
  idempotency_policy TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, transition_key, source_view_id, trigger_event_id, target_section_graph_binding_id),
  FOREIGN KEY (branch_id, projection_hash, environment_experience_profile_config_id) REFERENCES environment_experience_profile_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, trigger_event_id) REFERENCES environment_experience_event(branch_id, projection_hash, id)
);
