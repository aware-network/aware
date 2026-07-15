-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE section_focus_scope (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  section_id TEXT NOT NULL,
  focus_scope_id TEXT NOT NULL,
  -- ATTRIBUTES
  title TEXT NOT NULL,
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, section_id, focus_scope_id),
  FOREIGN KEY (branch_id, projection_hash, section_id) REFERENCES section(branch_id, projection_hash, id)
);
