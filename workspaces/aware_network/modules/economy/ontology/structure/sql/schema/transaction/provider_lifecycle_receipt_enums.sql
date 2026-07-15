-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE provider_lifecycle_event_kind AS ENUM ('chargeback', 'dispute', 'dispute_release', 'refund');

CREATE TYPE provider_lifecycle_status AS ENUM ('applied', 'held', 'released');
