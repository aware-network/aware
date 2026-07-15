-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_call_response_commit (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_instance_graph_commit_id UUID NOT NULL,
  function_call_response_id UUID NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, object_instance_graph_commit_id) REFERENCES object_instance_graph_commit(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_call_response_id) REFERENCES function_call_response(branch_id, projection_hash, id)
);
