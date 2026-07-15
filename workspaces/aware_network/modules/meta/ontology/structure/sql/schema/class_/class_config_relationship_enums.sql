-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE class_config_relationship_attribute_role AS ENUM ('auxiliary', 'foreign_key', 'reference');

CREATE TYPE class_config_relationship_direction AS ENUM ('forward', 'reverse');

CREATE TYPE class_config_relationship_identity_rail AS ENUM ('containment', 'reference');

CREATE TYPE class_config_relationship_reified_role AS ENUM ('association_to_target', 'source_to_association');

CREATE TYPE class_config_relationship_side_loading_strategy AS ENUM ('eager', 'lazy');

CREATE TYPE class_config_relationship_type AS ENUM ('many_to_many', 'many_to_one', 'one_to_many', 'one_to_one');
