-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE transaction_kind AS ENUM ('external_ingress', 'transfer');

CREATE TYPE transaction_status AS ENUM ('confirmed', 'created', 'failed', 'failed_incoming', 'outgoing_applied', 'sent', 'signed', 'validated');
