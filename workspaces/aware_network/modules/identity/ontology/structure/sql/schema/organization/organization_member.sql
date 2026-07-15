-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE organization_member (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  organization_id UUID NOT NULL,
  identity_id UUID NOT NULL,
  -- ATTRIBUTES
  role organization_member_role NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, organization_id, identity_id),
  FOREIGN KEY (branch_id, projection_hash, organization_id) REFERENCES organization(branch_id, projection_hash, id)
);
