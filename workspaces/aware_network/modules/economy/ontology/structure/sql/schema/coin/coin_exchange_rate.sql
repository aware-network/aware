-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE coin_exchange_rate (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  coin_id UUID NOT NULL,
  quote_coin_id UUID NOT NULL,
  -- ATTRIBUTES
  data_source TEXT NOT NULL,
  rate NUMERIC NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, coin_id, data_source, quote_coin_id),
  FOREIGN KEY (branch_id, projection_hash, coin_id) REFERENCES coin(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, quote_coin_id) REFERENCES coin(branch_id, projection_hash, id)
);
