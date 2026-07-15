-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE service_api_provider_set_service_package (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  service_api_provider_set_id UUID NOT NULL,
  service_package_id UUID NOT NULL,
  -- ATTRIBUTES
  description TEXT,
  membership_key TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, service_api_provider_set_id, service_package_id),
  FOREIGN KEY (branch_id, projection_hash, service_api_provider_set_id) REFERENCES service_api_provider_set(branch_id, projection_hash, id)
);
