-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TABLE object_config_graph_annotation (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  object_config_graph_id UUID NOT NULL,
  code_section_annotation_discriminate_id UUID,
  code_section_annotation_load_id UUID,
  code_section_annotation_overlay_id UUID,
  code_section_annotation_override_id UUID,
  code_section_annotation_oneof_id UUID,
  code_section_annotation_identity_id UUID,
  code_section_annotation_reference_id UUID,
  code_section_annotation_index_id UUID,
  code_section_annotation_storage_id UUID,
  -- ATTRIBUTES
  kind object_config_graph_annotation_kind NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  UNIQUE (branch_id, projection_hash, object_config_graph_id, kind),
  FOREIGN KEY (branch_id, projection_hash, object_config_graph_id) REFERENCES object_config_graph(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_discriminate_id) REFERENCES code_section_annotation_discriminate(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_load_id) REFERENCES code_section_annotation_load(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_overlay_id) REFERENCES code_section_annotation_overlay(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_override_id) REFERENCES code_section_annotation_override(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_oneof_id) REFERENCES code_section_annotation_one_of(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_reference_id) REFERENCES code_section_annotation_reference(branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_annotation_index_id) REFERENCES code_section_annotation_index(branch_id, projection_hash, id)
);
