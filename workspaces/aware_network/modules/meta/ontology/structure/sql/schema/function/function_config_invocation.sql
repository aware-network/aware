-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE function_config_invocation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  function_config_id UUID NOT NULL,
  target_function_config_id UUID NOT NULL,
  root_invocation_id UUID,
  class_config_relationship_id UUID,
  -- ATTRIBUTES
  position INTEGER NOT NULL,
  kind function_invocation_kind NOT NULL,
  relationship_fingerprint TEXT NOT NULL,
  root_kind function_invocation_root_kind NOT NULL,
  capture_name TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, function_config_id, position, kind, relationship_fingerprint, target_function_config_id),
  FOREIGN KEY (branch_id, projection_hash, function_config_id) REFERENCES function_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, target_function_config_id) REFERENCES function_config(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, root_invocation_id) REFERENCES function_config_invocation(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, class_config_relationship_id) REFERENCES class_config_relationship(branch_id, projection_hash, id)
);
