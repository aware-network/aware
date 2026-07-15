-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE smart_contract_settlement (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  smart_contract_reservation_id UUID NOT NULL,
  coin_id UUID NOT NULL,
  payer_finance_entity_id UUID NOT NULL,
  payer_wallet_public_id UUID NOT NULL,
  receiver_finance_entity_id UUID NOT NULL,
  receiver_wallet_public_id UUID NOT NULL,
  -- ATTRIBUTES
  final_cost NUMERIC NOT NULL,
  status smart_contract_settlement_status NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, smart_contract_reservation_id) REFERENCES smart_contract_reservation(branch_id, projection_hash, id)
);
