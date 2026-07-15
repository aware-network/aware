-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_member (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  smart_contract_id TEXT NOT NULL,
  finance_entity_id TEXT NOT NULL,
  -- ATTRIBUTES
  type_ TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, smart_contract_id, type_, finance_entity_id),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_id) REFERENCES smart_contract(branch_id, projection_hash, id)
);
