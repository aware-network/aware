-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_episode (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  memory_episodic_id UUID NOT NULL,
  content_chain_content_id UUID NOT NULL,
  content_chain_section_id UUID NOT NULL,
  -- ATTRIBUTES
  end_time TIMESTAMPTZ NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, memory_episodic_id, content_chain_content_id, content_chain_section_id),
  FOREIGN KEY (branch_id, projection_hash, memory_episodic_id) REFERENCES memory_episodic(branch_id, projection_hash, id)
);
