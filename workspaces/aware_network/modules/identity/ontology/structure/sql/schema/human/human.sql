-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE human (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  actor_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, actor_id),
  FOREIGN KEY (branch_id, projection_hash, actor_id) REFERENCES actor(branch_id, projection_hash, id)
);
