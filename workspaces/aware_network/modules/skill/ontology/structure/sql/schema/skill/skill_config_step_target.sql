-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE skill_config_step_target (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  skill_config_step_id UUID NOT NULL,
  skill_config_target_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, skill_config_step_id, skill_config_target_id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_step_id) REFERENCES skill_config_step(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, skill_config_target_id) REFERENCES skill_config_target(branch_id, projection_hash, id)
);
