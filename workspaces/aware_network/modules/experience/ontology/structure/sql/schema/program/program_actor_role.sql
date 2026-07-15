-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_actor_role (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  program_actor_id UUID NOT NULL,
  actor_role_id UUID NOT NULL,
  actor_config_role_config_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, program_actor_id, actor_role_id, actor_config_role_config_id),
  FOREIGN KEY (branch_id, projection_hash, program_actor_id) REFERENCES program_actor(branch_id, projection_hash, id)
);
