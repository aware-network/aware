-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_working_tool_frame (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  id UUID NOT NULL,
  projection_hash TEXT,
  -- RELATIONSHIPS
  memory_working_item_id UUID UNIQUE,
  object_instance_graph_branch_id UUID,
  -- ATTRIBUTES
  tool_call_id UUID NOT NULL,
  tool_response_id UUID,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, id, projection_hash),
  UNIQUE (branch_id, projection_hash, tool_call_id),
  FOREIGN KEY (branch_id, projection_hash, memory_working_item_id) REFERENCES memory_working_item(branch_id, projection_hash, id)
);
