-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE turn (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  environment_id TEXT NOT NULL,
  key TEXT NOT NULL,
  target_actor_id TEXT NOT NULL,
  -- ATTRIBUTES
  mailbox_key TEXT NOT NULL,
  state TEXT NOT NULL,
  terminal_status TEXT,
  resolved_branch_id TEXT,
  resolved_projection_hash TEXT,
  lane_resolution_source TEXT,
  created_at_unix_ms INTEGER NOT NULL,
  accepted_at_unix_ms INTEGER NOT NULL,
  started_at_unix_ms INTEGER,
  terminal_at_unix_ms INTEGER,
  idempotency_key TEXT,
  cause_event_id TEXT,
  cause_action_execution_id TEXT,
  attempt_count INTEGER NOT NULL,
  max_attempts INTEGER NOT NULL,
  lease_owner TEXT,
  lease_expires_at_unix_ms INTEGER,
  error_code TEXT,
  error_message TEXT,
  result_summary TEXT,
  result_commit_ids TEXT NOT NULL,
  payload TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, environment_id, key, target_actor_id)
);
