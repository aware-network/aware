# Aware Meta Graph Render Components

Module-local Interface render components for General Meta graph surfaces.

V0 exposes `aware.meta.graph.canvas`, a native Flutter graph canvas that consumes
only explicit render component inputs and emits only explicit action ports.

This package is owned by the Meta module because it visualizes General Meta graph
truth: Object Config Graph, Object Projection Graph, Object Instance Graph, and
Object Instance Graph Branch/Commit coordinates. It does not call Meta services,
open runtime state, or know Ontology/API/SDK semantic layers.

## Component

`aware.meta.graph.canvas`

Inputs:

- `graph_snapshot`
- `object_config_graph_ref`
- `object_projection_graph_ref`
- `object_instance_graph_ref`
- `object_instance_graph_branch_ref`
- `object_instance_graph_commit_ref`
- `selected_identity`
- `viewport_state`

Actions:

- `select_identity`
- `activate_identity`
- `request_focus_transition`
- `set_viewport`
- `open_branch`
- `compare_commit`

The renderer displays graph truth. Experience decides pane activation. Attention
owns selection, focus, zoom, and viewport continuity.
