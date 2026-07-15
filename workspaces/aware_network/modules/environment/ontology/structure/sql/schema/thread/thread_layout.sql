-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE thread_layout (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  thread_id UUID NOT NULL,
  layout_id UUID NOT NULL,
  -- ATTRIBUTES
  key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, thread_id, layout_id),
  FOREIGN KEY (branch_id, projection_hash, thread_id) REFERENCES thread(branch_id, projection_hash, id)
);
