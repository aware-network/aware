from __future__ import annotations


def program_config_compile_diag_code(message: str) -> str:
    lowered = (message or "").lower()
    if "graph source contains parse errors" in lowered:
        return "aware.program.graph_parse_error"
    if "graph declaration" in lowered and "references unknown experience" in lowered:
        return "aware.program.graph_experience_unresolved"
    if "graph declaration" in lowered and "references unknown node identity" in lowered:
        return "aware.program.graph_node_identity_unresolved"
    if "graph declaration" in lowered and "multiple root declarations" in lowered:
        return "aware.program.graph_root_duplicate"
    if "graph declaration" in lowered and "must declare exactly one root" in lowered:
        return "aware.program.graph_root_missing"
    if "graph declaration" in lowered and "contains self edge" in lowered:
        return "aware.program.graph_self_edge"
    if "graph declaration" in lowered and "contains duplicate edge" in lowered:
        return "aware.program.graph_edge_duplicate"
    if "graph declaration" in lowered and "assigns multiple parents to child" in lowered:
        return "aware.program.graph_parent_conflict"
    if "graph declaration" in lowered and "cannot appear as a child edge target" in lowered:
        return "aware.program.graph_root_as_child"
    if "graph declaration" in lowered and "contains disconnected node identity" in lowered:
        return "aware.program.graph_disconnected"
    if "graph declaration" in lowered and "contains a cycle" in lowered:
        return "aware.program.graph_cycle"
    if "graph declaration" in lowered and "has unreachable node identity" in lowered:
        return "aware.program.graph_unreachable"
    if "graph node identity reference must use <node>.<identity> form" in lowered:
        return "aware.program.graph_ref_invalid"
    if "graph node identity reference must be non-empty" in lowered:
        return "aware.program.graph_ref_invalid"
    if "call plan.port(...) is not allowed" in lowered:
        return "aware.program.port_legacy_call"
    if "call plan.bind(...) is not allowed" in lowered:
        return "aware.program.bind_legacy_call"
    if "call plan.lane(...) is not allowed" in lowered:
        return "aware.program.lane_legacy_call"
    if "call plan.object(...) is not allowed" in lowered:
        return "aware.program.object_legacy_call"
    if "invoke requires actor attribution" in lowered:
        return "aware.program.invoke_actor_required"
    if "call references undeclared actor" in lowered:
        return "aware.program.invoke_actor_undeclared"
    if "invoke requires target node attribution" in lowered:
        return "aware.program.instance_requires_object"
    if "port declarations must appear at top of program body" in lowered:
        return "aware.program.port_order_invalid"
    if "plan.layout declarations must appear at top of program body" in lowered:
        return "aware.program.layout_order_invalid"
    if "plan.section declarations must appear at top of program body" in lowered:
        return "aware.program.layout_order_invalid"
    if "plan.slot declarations must appear at top of program body" in lowered:
        return "aware.program.layout_order_invalid"
    if "plan.slot references undeclared program port" in lowered:
        return "aware.program.slot_unknown_port"
    if "undeclared program port" in lowered:
        return "aware.program.bind_port_undeclared"
    if "duplicate port key" in lowered:
        return "aware.program.port_duplicate"
    if "does not accept head args" in lowered:
        return "aware.program.port_head_args_not_allowed"
    if "ref must use `<experience>` form" in lowered:
        return "aware.program.port_ref_invalid"
    if "duplicate layout key" in lowered:
        return "aware.program.layout_duplicate"
    if "exactly one default layout" in lowered:
        return "aware.program.layout_default_invalid"
    if "plan.section references unknown layout_key" in lowered:
        return "aware.program.section_unknown_layout"
    if "plan.slot references unknown layout_key" in lowered:
        return "aware.program.slot_unknown_layout"
    if "plan.slot references unknown section_key" in lowered:
        return "aware.program.slot_unknown_section"
    if "plan.slot on_bind must be one of" in lowered:
        return "aware.program.slot_on_bind_invalid"
    if "cannot reference local bindings" in lowered:
        return "aware.program.declaration_local_ref_invalid"
    if "port key" in lowered:
        return "aware.program.port_key_invalid"
    if "references unknown config" in lowered:
        return "aware.program.impl_config_unresolved"
    if "program impl" in lowered and "cannot declare parameters" in lowered:
        return "aware.program.impl_params_forbidden"
    if "config declarations cannot include executable statements" in lowered:
        return "aware.program.config_surface_invalid"
    if "program impl" in lowered and "cannot declare" in lowered:
        return "aware.program.impl_surface_invalid"
    return "aware.program.config_compile_error"
