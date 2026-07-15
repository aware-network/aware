-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_operation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  network_request_id UUID,
  network_response_id UUID,
  network_stream_id UUID,
  network_stream_frame_id UUID,
  -- ATTRIBUTES
  message_type network_operation_message_type NOT NULL,
  type_ network_operation_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, message_type, type_)
);
