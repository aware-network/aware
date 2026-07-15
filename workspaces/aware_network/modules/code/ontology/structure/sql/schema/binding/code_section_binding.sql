-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_binding (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  source_graph_segment_id UUID NOT NULL,
  target_graph_segment_id UUID NOT NULL,
  -- ATTRIBUTES
  source_graph_ref TEXT NOT NULL,
  target_graph_ref TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id)
);
