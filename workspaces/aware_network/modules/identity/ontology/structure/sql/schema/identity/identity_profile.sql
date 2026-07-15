-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity_profile (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  image_id UUID UNIQUE,
  -- ATTRIBUTES
  public_handle TEXT NOT NULL,
  display_name TEXT NOT NULL,
  full_name TEXT NOT NULL,
  country_code TEXT NOT NULL,
  language_code TEXT NOT NULL,
  bio TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, public_handle)
);
