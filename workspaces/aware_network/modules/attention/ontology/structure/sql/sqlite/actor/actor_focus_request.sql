-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus_request (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  sender_id TEXT NOT NULL,
  receiver_id TEXT NOT NULL,
  focus_id TEXT NOT NULL,
  response_id TEXT,
  -- ATTRIBUTES
  suggested_level TEXT NOT NULL,
  rationale TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence REAL,
  expires_at TEXT,
  response_message TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sender_id, receiver_id, focus_id),
  FOREIGN KEY (branch_id, projection_hash, response_id) REFERENCES actor_focus_request_response(branch_id, projection_hash, id)
);
