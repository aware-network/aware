-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_section_view (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  object_projection_graph_observable_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_section_id UUID NOT NULL,
  projection_experience_view_instance_id UUID NOT NULL UNIQUE,
  -- ATTRIBUTES
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, object_projection_graph_observable_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_section_id) REFERENCES projection_experience_section(branch_id, projection_hash, id)
);
