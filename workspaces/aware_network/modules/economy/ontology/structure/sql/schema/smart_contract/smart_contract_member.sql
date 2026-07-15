-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_member (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  smart_contract_id UUID NOT NULL,
  finance_entity_id UUID NOT NULL,
  -- ATTRIBUTES
  type_ smart_contract_member_type NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, smart_contract_id, type_, finance_entity_id),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_id) REFERENCES smart_contract(branch_id, projection_hash, id)
);
