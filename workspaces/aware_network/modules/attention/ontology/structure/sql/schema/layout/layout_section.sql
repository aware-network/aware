-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE layout_section (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  layout_id UUID NOT NULL,
  section_id UUID NOT NULL,
  -- ATTRIBUTES
  order_ INTEGER NOT NULL,
  flex NUMERIC NOT NULL,
  is_visible BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, layout_id, section_id),
  FOREIGN KEY (branch_id, projection_hash, layout_id) REFERENCES layout(branch_id, projection_hash, id)
);
