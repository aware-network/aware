-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE code_section_import (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  code_section_id UUID UNIQUE,
  module_segment_id UUID NOT NULL,
  -- ATTRIBUTES
  module_text TEXT NOT NULL,
  is_from_import BOOLEAN NOT NULL,
  is_star_import BOOLEAN NOT NULL,
  relative_level INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
