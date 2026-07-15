-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE window_layout_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  layout_section_id UUID NOT NULL,
  -- RELATIONSHIPS
  window_layout_id UUID NOT NULL,
  projection_experience_view_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, layout_section_id),
  FOREIGN KEY (branch_id, projection_hash, window_layout_id) REFERENCES window_layout(branch_id, projection_hash, id)
);
