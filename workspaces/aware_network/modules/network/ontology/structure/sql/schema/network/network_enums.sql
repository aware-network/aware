-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE network_app_type AS ENUM ('environment', 'interface', 'network_node');

CREATE TYPE network_environment_role AS ENUM ('owner', 'replica');

CREATE TYPE network_fanout_mode AS ENUM ('notify_pull');

CREATE TYPE network_node_status AS ENUM ('active', 'inactive', 'suspended', 'syncing');

CREATE TYPE network_operation_message_type AS ENUM ('notification', 'request', 'response', 'stream');

CREATE TYPE network_operation_type AS ENUM ('api', 'environment', 'environment_config', 'network_node', 'service');

CREATE TYPE network_request_status AS ENUM ('accepted', 'failed', 'pending', 'rejected', 'succeeded');
