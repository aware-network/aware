-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  section_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id UUID NOT NULL,
  -- ATTRIBUTES
  section_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, section_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_id) REFERENCES projection_experience(branch_id, projection_hash, id)
);
