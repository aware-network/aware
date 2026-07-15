-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_graph_identity_profile (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  projection_experience_graph_identity_id TEXT UNIQUE,
  -- ATTRIBUTES
  review_label TEXT NOT NULL,
  resolution_prompts TEXT NOT NULL,
  aliases TEXT NOT NULL,
  summary TEXT,
  notes TEXT,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_graph_identity_id) REFERENCES projection_experience_graph_identity(branch_id, projection_hash, id)
);
