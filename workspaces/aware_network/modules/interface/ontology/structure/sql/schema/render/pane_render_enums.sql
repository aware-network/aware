-- coverage:ignore-file
-- GENERATED CODE - DO NOT MODIFY BY HAND

CREATE TYPE pane_action_event AS ENUM ('activate', 'change', 'submit');

CREATE TYPE pane_render_capability_kind AS ENUM ('action_binding', 'input_kind', 'layout_kind', 'node_kind', 'receipt', 'render_component');

CREATE TYPE pane_render_node_kind AS ENUM ('box', 'button', 'column', 'component', 'disclosure', 'field', 'list_item', 'metric', 'receipt', 'repeat', 'row', 'scroll', 'section_header', 'status', 'text', 'text_input');

CREATE TYPE pane_render_semantic_role AS ENUM ('action', 'heading', 'input', 'message', 'metadata', 'metric', 'pane', 'paragraph', 'receipt', 'section', 'status');

CREATE TYPE pane_state_binding_target_property AS ENUM ('enabled', 'identity', 'items', 'media_ref', 'text', 'tone', 'value', 'visible');

CREATE TYPE pane_state_binding_transform AS ENUM ('count', 'equals', 'exists', 'is_empty', 'not_empty', 'plural_count', 'raw', 'text');
