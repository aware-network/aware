-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_projection_edge (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  code_section_projection_id TEXT NOT NULL,
  type_segment_id TEXT NOT NULL,
  member_segment_id TEXT NOT NULL,
  target_segment_id TEXT,
  -- ATTRIBUTES
  type_ref TEXT NOT NULL,
  member TEXT NOT NULL,
  target_projection_ref TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, code_section_projection_id, member),
  FOREIGN KEY (branch_id, projection_hash, code_section_projection_id) REFERENCES code_section_projection(branch_id, projection_hash, id)
);
