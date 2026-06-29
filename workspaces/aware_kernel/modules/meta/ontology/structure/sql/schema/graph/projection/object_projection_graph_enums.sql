-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE object_projection_graph_attribute_role AS ENUM ('foreign_key', 'reference');

CREATE TYPE object_projection_graph_edge_include AS ENUM ('optional', 'required');

CREATE TYPE object_projection_graph_edge_multiplicity AS ENUM ('at_least_1', 'many', 'one');

CREATE TYPE object_projection_graph_node_selection AS ENUM ('all', 'one', 'top_n');
