-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_layout_section (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  program_layout_id TEXT NOT NULL,
  port_section_id TEXT,
  program_branch_id TEXT,
  -- ATTRIBUTES
  key TEXT NOT NULL,
  order_ INTEGER NOT NULL,
  is_visible INTEGER NOT NULL,
  flex REAL,
  is_active INTEGER NOT NULL,
  view_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_layout_id, key),
  FOREIGN KEY (branch_id, projection_hash, program_layout_id) REFERENCES program_layout(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, program_branch_id) REFERENCES program_branch(branch_id, projection_hash, id)
);
