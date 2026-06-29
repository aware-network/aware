-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE action_execution_status AS ENUM ('accepted', 'canceled', 'created', 'failed', 'rejected', 'running', 'succeeded', 'timed_out');

CREATE TYPE action_feedback_stage AS ENUM ('dispatch', 'execute', 'terminal');

CREATE TYPE action_feedback_status AS ENUM ('accepted', 'failed', 'rejected', 'requested', 'responded', 'running', 'skipped', 'succeeded');

CREATE TYPE action_intent_status AS ENUM ('requested', 'skipped', 'superseded');

CREATE TYPE action_status AS ENUM ('executing', 'handled_failure', 'handled_success', 'requested', 'skipped');
