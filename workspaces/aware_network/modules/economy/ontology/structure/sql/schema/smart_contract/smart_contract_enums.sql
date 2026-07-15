-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE smart_contract_member_type AS ENUM ('payer', 'receiver');

CREATE TYPE smart_contract_status AS ENUM ('active', 'completed', 'paused');

CREATE TYPE smart_contract_type AS ENUM ('ownership', 'utility');
