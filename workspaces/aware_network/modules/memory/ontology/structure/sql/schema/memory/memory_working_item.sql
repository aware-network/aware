-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_item (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  memory_working_id UUID NOT NULL,
  attention_transition_id UUID,
  -- ATTRIBUTES
  kind memory_working_item_kind NOT NULL,
  position INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  rationale TEXT,
  summary TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, memory_working_id, kind, position),
  FOREIGN KEY (branch_id, projection_hash, memory_working_id) REFERENCES memory_working(branch_id, projection_hash, id)
);
