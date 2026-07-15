-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE wallet (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  wallet_private_id TEXT UNIQUE,
  wallet_public_id TEXT UNIQUE,
  -- ATTRIBUTES
  private_key_encrypted TEXT NOT NULL,
  public_key TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, private_key_encrypted, public_key),
  FOREIGN KEY (branch_id, projection_hash, wallet_private_id) REFERENCES wallet_private(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, wallet_public_id) REFERENCES wallet_public(branch_id, projection_hash, id)
);
