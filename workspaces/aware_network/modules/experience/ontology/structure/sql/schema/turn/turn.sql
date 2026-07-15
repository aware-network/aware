-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE turn (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- ATTRIBUTES
  environment_id UUID NOT NULL,
  key TEXT NOT NULL,
  mailbox_key TEXT NOT NULL,
  state turn_execution_state NOT NULL,
  terminal_status turn_execution_terminal_status,
  target_actor_id UUID NOT NULL,
  resolved_branch_id UUID,
  resolved_projection_hash TEXT,
  lane_resolution_source TEXT,
  created_at_unix_ms INTEGER NOT NULL,
  accepted_at_unix_ms INTEGER NOT NULL,
  started_at_unix_ms INTEGER,
  terminal_at_unix_ms INTEGER,
  idempotency_key TEXT,
  cause_event_id UUID,
  cause_action_execution_id UUID,
  attempt_count INTEGER NOT NULL,
  max_attempts INTEGER NOT NULL,
  lease_owner TEXT,
  lease_expires_at_unix_ms INTEGER,
  error_code TEXT,
  error_message TEXT,
  result_summary TEXT,
  result_commit_ids UUID[] NOT NULL,
  payload JSONB,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, environment_id, key, target_actor_id)
);
