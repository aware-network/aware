-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE window_ (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  window_id UUID NOT NULL,
  -- RELATIONSHIPS
  active_layout_id UUID,
  -- ATTRIBUTES
  active_layout_mode window_active_layout_mode NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, window_id)
);
