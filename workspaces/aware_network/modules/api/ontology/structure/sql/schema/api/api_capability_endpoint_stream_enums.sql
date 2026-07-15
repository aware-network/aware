-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE api_capability_endpoint_stream_event_kind AS ENUM ('complete', 'delta', 'error', 'notice', 'snapshot');

CREATE TYPE api_capability_endpoint_stream_mode AS ENUM ('bidirectional', 'client', 'server');
