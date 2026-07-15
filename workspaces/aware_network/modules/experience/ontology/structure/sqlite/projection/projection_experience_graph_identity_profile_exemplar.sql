-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_graph_identity_profile_exemplar (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  key TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_graph_identity_profile_id TEXT NOT NULL,
  image_id TEXT UNIQUE,
  -- ATTRIBUTES
  label TEXT,
  prompt_hint TEXT,
  note TEXT,
  is_primary INTEGER NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_graph_identity_profile_id) REFERENCES projection_experience_graph_identity_profile(branch_id, projection_hash, id)
);
