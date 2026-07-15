-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_tool_frame (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  id TEXT NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  memory_working_item_id TEXT UNIQUE,
  object_instance_graph_branch_id TEXT,
  -- ATTRIBUTES
  tool_call_id TEXT NOT NULL,
  tool_response_id TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, tool_call_id),
  FOREIGN KEY (branch_id, projection_hash, memory_working_item_id) REFERENCES memory_working_item(branch_id, projection_hash, id)
);
