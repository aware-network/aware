-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE identity (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  human_id UUID UNIQUE,
  organization_id UUID UNIQUE,
  identity_profile_id UUID UNIQUE,
  -- ATTRIBUTES
  public_key TEXT NOT NULL,
  type_ identity_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, public_key, type_),
  FOREIGN KEY (branch_id, projection_hash, human_id) REFERENCES human(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, identity_profile_id) REFERENCES identity_profile(branch_id, projection_hash, id)
);
