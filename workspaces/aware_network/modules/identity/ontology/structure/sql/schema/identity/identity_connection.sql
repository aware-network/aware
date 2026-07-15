-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity_connection (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  requester_identity_id UUID NOT NULL,
  recipient_identity_id UUID NOT NULL,
  -- ATTRIBUTES
  connection_type TEXT NOT NULL,
  metadata JSONB,
  status connection_request_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, connection_type, requester_identity_id, recipient_identity_id)
);
