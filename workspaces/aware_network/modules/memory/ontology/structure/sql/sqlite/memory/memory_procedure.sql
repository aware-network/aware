-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_procedure (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  memory_procedural_id TEXT NOT NULL,
  content_id TEXT NOT NULL,
  procedure_config_id TEXT NOT NULL,
  -- ATTRIBUTES
  reward_score REAL NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, memory_procedural_id, content_id, procedure_config_id),
  FOREIGN KEY (branch_id, projection_hash, memory_procedural_id) REFERENCES memory_procedural(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, procedure_config_id) REFERENCES memory_procedure_config(branch_id, projection_hash, id)
);
