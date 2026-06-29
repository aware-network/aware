-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE change_delta_kind AS ENUM ('scalar_set', 'text_patch');

CREATE TYPE change_type AS ENUM ('create', 'delete', 'update');
