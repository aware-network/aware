-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_call_argument (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  attribute_id TEXT NOT NULL,
  function_call_id TEXT NOT NULL,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, attribute_id) REFERENCES attribute(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, function_call_id) REFERENCES function_call(branch_id, projection_hash, id)
);
