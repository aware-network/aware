-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE event_delivery_mode AS ENUM ('batched', 'immediate', 'queued', 'scheduled');

CREATE TYPE event_priority AS ENUM ('critical', 'deferred', 'high', 'low', 'normal');

CREATE TYPE event_schedule_status AS ENUM ('active', 'inactive');

CREATE TYPE event_status AS ENUM ('handled_failure', 'handled_success', 'handling', 'ignored', 'raised');

CREATE TYPE event_type AS ENUM ('condition', 'manual', 'scheduled', 'system', 'webhook');
