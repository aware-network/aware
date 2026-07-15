-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_layout_section_graph_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_layout_graph_binding_id UUID NOT NULL,
  section_graph_binding_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, projection_experience_layout_graph_binding_id, section_graph_binding_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_layout_graph_binding_id) REFERENCES projection_experience_layout_graph_binding(branch_id, projection_hash, id)
);
