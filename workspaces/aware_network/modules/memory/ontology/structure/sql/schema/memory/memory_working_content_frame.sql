-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_content_frame (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  memory_working_item_id UUID UNIQUE,
  content_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, content_id),
  FOREIGN KEY (branch_id, projection_hash, memory_working_item_id) REFERENCES memory_working_item(branch_id, projection_hash, id)
);
