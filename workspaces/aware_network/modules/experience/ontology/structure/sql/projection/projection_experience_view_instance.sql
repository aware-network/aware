-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_view_instance (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  view_instance_key TEXT NOT NULL,
  section_graph_binding_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_view_id UUID NOT NULL,
  object_instance_graph_branch_id UUID,
  -- ATTRIBUTES
  state_commit_id UUID,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, view_instance_key, section_graph_binding_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_view_id) REFERENCES projection_experience_view(branch_id, projection_hash, id)
);
