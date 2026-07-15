-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE memory_episode (
  -- PRIMARY KEY
  branch_id TEXT NOT NULL,
  projection_hash TEXT NOT NULL,
  id TEXT NOT NULL,
  -- RELATIONSHIPS
  memory_episodic_id TEXT NOT NULL,
  content_chain_content_id TEXT NOT NULL,
  content_chain_section_id TEXT NOT NULL,
  -- ATTRIBUTES
  end_time TEXT NOT NULL,
  start_time TEXT NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, memory_episodic_id, content_chain_content_id, content_chain_section_id),
  FOREIGN KEY (branch_id, projection_hash, memory_episodic_id) REFERENCES memory_episodic(branch_id, projection_hash, id)
);
