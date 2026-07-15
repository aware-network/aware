-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE projection_experience_view (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  name TEXT NOT NULL,
  object_projection_graph_observable_id UUID NOT NULL,
  -- RELATIONSHIPS
  projection_experience_id UUID NOT NULL,
  state_model_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id, name, object_projection_graph_observable_id),
  FOREIGN KEY (branch_id, projection_hash, projection_experience_id) REFERENCES projection_experience(branch_id, projection_hash, id)
);
