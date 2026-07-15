-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_settlement (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  smart_contract_reservation_id TEXT NOT NULL,
  coin_id TEXT NOT NULL,
  payer_finance_entity_id TEXT NOT NULL,
  payer_wallet_public_id TEXT NOT NULL,
  receiver_finance_entity_id TEXT NOT NULL,
  receiver_wallet_public_id TEXT NOT NULL,
  -- ATTRIBUTES
  final_cost TEXT NOT NULL,
  status TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_reservation_id) REFERENCES smart_contract_reservation(branch_id, projection_hash, id)
);
