-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE turn_feedback (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  -- RELATIONSHIPS
  turn_id TEXT NOT NULL,
  -- ATTRIBUTES
  mailbox_key TEXT NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at_unix_ms INTEGER NOT NULL,
  message TEXT,
  payload TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, sequence),
  FOREIGN KEY (branch_id, projection_hash, turn_id) REFERENCES turn(branch_id, projection_hash, id)
);
