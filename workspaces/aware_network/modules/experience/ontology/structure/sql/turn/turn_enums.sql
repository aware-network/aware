-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE turn_execution_state AS ENUM ('accepted', 'running', 'terminal');

CREATE TYPE turn_execution_terminal_status AS ENUM ('cancelled', 'dead_letter', 'failed', 'skipped', 'succeeded');
