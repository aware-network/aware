-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_graph_identity_profile_exemplar (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  key TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_graph_identity_profile_id UUID NOT NULL,
  image_id UUID UNIQUE,
  -- ATTRIBUTES
  label TEXT,
  prompt_hint TEXT,
  note TEXT,
  is_primary BOOLEAN NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, key),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_graph_identity_profile_id) REFERENCES projection_experience_graph_identity_profile(branch_id, projection_hash, id)
);
