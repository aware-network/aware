-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_section_graph_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  binding_key TEXT NOT NULL,
  layout_config_section_config_id UUID NOT NULL,
  projection_experience_view_id UUID NOT NULL,
  projection_experience_graph_identity_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id UUID NOT NULL,
  -- ATTRIBUTES
  section_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, binding_key, layout_config_section_config_id, projection_experience_view_id, projection_experience_graph_identity_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_id) REFERENCES projection_experience(branch_id, projection_hash, id)
);
