-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE network_stream_frame (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  network_stream_id UUID NOT NULL,
  function_call_id UUID,
  -- ATTRIBUTES
  ack_seq INTEGER,
  control network_stream_control NOT NULL,
  seq INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, seq, network_stream_id)
);
