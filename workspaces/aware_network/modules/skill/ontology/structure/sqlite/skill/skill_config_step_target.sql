-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_step_target (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  skill_config_target_id TEXT NOT NULL UNIQUE,
  -- RELATIONSHIPS
  skill_config_step_id TEXT NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, skill_config_target_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_step_id) REFERENCES skill_config_step(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_target_id) REFERENCES skill_config_target(branch_id, projection_hash, id)
);
