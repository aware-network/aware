-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE program_config_actor_config (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  alias TEXT NOT NULL,
  -- RELATIONSHIPS
  program_config_id TEXT NOT NULL,
  actor_config_id TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, alias),
  FOREIGN KEY (branch_id, projection_hash, program_config_id) REFERENCES program_config(branch_id, projection_hash, id)
);
