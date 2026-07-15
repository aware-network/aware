-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE actor_focus_request (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  sender_id UUID NOT NULL,
  receiver_id UUID NOT NULL,
  focus_id UUID NOT NULL,
  response_id UUID,
  -- ATTRIBUTES
  suggested_level actor_focus_level_type NOT NULL,
  rationale TEXT NOT NULL,
  status actor_focus_request_status NOT NULL,
  confidence NUMERIC,
  expires_at TIMESTAMPTZ,
  response_message TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, sender_id, receiver_id, focus_id),
  FOREIGN KEY (branch_id, projection_hash, response_id) REFERENCES actor_focus_request_response(branch_id, projection_hash, id)
);
