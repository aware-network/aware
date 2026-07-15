from __future__ import annotations

from aware_meta.graph.projection.deltas.typed_operations import (
    OBJECT_INSTANCE_GRAPH_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
)
from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyInvocationIntent,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
    blocked_handler_result,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    mapping_value,
    optional_text,
)


HANDLER_KEY = "object_projection_graph.function_calls"
OPG_CREATE_ROOT_INVOCATION_ORDER = 50
OPG_CREATE_NODE_INVOCATION_ORDER = 51
OPG_CREATE_EDGE_INVOCATION_ORDER = 52
OPG_CREATE_CONSTRUCTOR_INVOCATION_ORDER = 53
OPG_CREATE_RELATIONSHIP_INVOCATION_ORDER = 54
OPG_CREATE_OBJECT_INSTANCE_GRAPH_INVOCATION_ORDER = 55
OPG_CREATE_PROJECTION_DECLARATION_INVOCATION_ORDER = 48
OPG_CREATE_PROJECTION_BINDING_INVOCATION_ORDER = 49
OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.build_via_object_config_graph"
)
OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.create_node"
)
OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.create_edge"
)
OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.create_constructor"
)
OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.create_relationship"
)
OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.create_object_instance_graph"
)
OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION_REF = (
    "aware_meta_ontology.graph.config.object_config_graph."
    "ObjectConfigGraph.create_object_projection_graph_declaration"
)
OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph_declaration."
    "ObjectProjectionGraphDeclaration.create_binding"
)


def plan_object_projection_graph_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind == OBJECT_PROJECTION_GRAPH_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_opg_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if operation.ontology_subject_kind == OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_opg_node_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if operation.ontology_subject_kind == OBJECT_PROJECTION_GRAPH_EDGE_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_opg_edge_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if (
        operation.ontology_subject_kind
        == OBJECT_PROJECTION_GRAPH_CONSTRUCTOR_SUBJECT_KIND
    ):
        if operation.operation_family == "create":
            return _plan_opg_constructor_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if (
        operation.ontology_subject_kind
        == OBJECT_PROJECTION_GRAPH_RELATIONSHIP_SUBJECT_KIND
    ):
        if operation.operation_family == "create":
            return _plan_opg_relationship_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if operation.ontology_subject_kind == OBJECT_INSTANCE_GRAPH_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_object_instance_graph_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if (
        operation.ontology_subject_kind
        == OBJECT_PROJECTION_GRAPH_DECLARATION_SUBJECT_KIND
    ):
        if operation.operation_family == "create":
            return _plan_projection_declaration_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if operation.ontology_subject_kind == OBJECT_PROJECTION_GRAPH_BINDING_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_projection_binding_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_opg_ontology_handler_subject_mismatch",
        blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
    )


def _plan_opg_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        operation=operation,
        context=context,
    )
    opg_id = _opg_id(operation=operation)
    name = _opg_name(operation=operation)
    projection_hash = _opg_projection_hash(operation=operation)
    language = _opg_language(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("graph_semantic_key", graph_semantic_key),
            ("graph_object_id", graph_object_id),
            ("object_projection_graph_id", opg_id),
            ("name", name),
            ("projection_hash", projection_hash),
            ("language", language),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_create_requires_graph_and_signature",
            blockers=tuple(f"missing_opg_create_{field}" for field in missing),
        )

    assert graph_semantic_key is not None
    assert graph_object_id is not None
    assert opg_id is not None
    assert name is not None
    assert projection_hash is not None
    assert language is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_opg_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:build_via_object_config_graph",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=OPG_CREATE_ROOT_INVOCATION_ORDER,
                invocation_mode="constructor",
                owner_class_name="ObjectProjectionGraph",
                function_name="build_via_object_config_graph",
                function_ref=OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION_REF,
                target_object_id=None,
                receiver_semantic_key=graph_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=opg_id,
                result_projection_name="ObjectProjectionGraph",
                lane_state_role="created_in_plan",
                commit_required=True,
                kwargs={
                    "object_config_graph_id": graph_object_id,
                    "name": name,
                    "projection_hash": projection_hash,
                    "language": language,
                    "description": _opg_description(operation=operation),
                    "supports_virtual_build": _opg_supports_virtual_build(
                        operation=operation,
                    ),
                },
                reason="meta_opg_create_function_call_ready",
            ),
        ),
    )


def _plan_opg_node_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    opg_semantic_key = _opg_semantic_key(operation=operation)
    opg_object_id = _opg_receiver_object_id(
        opg_semantic_key=opg_semantic_key,
        operation=operation,
        context=context,
    )
    node_id = _opg_node_id(operation=operation)
    class_config_id = _opg_node_class_config_id(operation=operation)
    selection = _opg_node_selection(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_projection_graph_semantic_key", opg_semantic_key),
            ("object_projection_graph_id", opg_object_id),
            ("object_projection_graph_node_id", node_id),
            ("class_config_id", class_config_id),
            ("selection", selection),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_node_create_requires_projection_and_class",
            blockers=tuple(f"missing_opg_node_create_{field}" for field in missing),
        )

    assert opg_semantic_key is not None
    assert opg_object_id is not None
    assert node_id is not None
    assert class_config_id is not None
    assert selection is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_opg_node_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_node",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=OPG_CREATE_NODE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectProjectionGraph",
                function_name="create_node",
                function_ref=OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION_REF,
                target_object_id=opg_object_id,
                receiver_semantic_key=opg_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=node_id,
                target_projection_name="ObjectProjectionGraph",
                lane_state_role="created_in_plan_member",
                commit_required=True,
                kwargs={
                    "class_config_id": class_config_id,
                    "is_root": _opg_node_is_root(operation=operation),
                    "required_for_validity": (
                        _opg_node_required_for_validity(operation=operation)
                    ),
                    "selection": selection,
                    "top_n": _opg_node_top_n(operation=operation),
                    "selector_condition_id": (
                        _opg_node_selector_condition_id(operation=operation)
                    ),
                    "policy_refs": list(_opg_node_policy_refs(operation=operation)),
                },
                reason="meta_opg_node_create_function_call_ready",
            ),
        ),
    )


def _plan_opg_edge_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    opg_semantic_key = _opg_semantic_key(operation=operation)
    opg_object_id = _opg_receiver_object_id(
        opg_semantic_key=opg_semantic_key,
        operation=operation,
        context=context,
    )
    edge_id = _opg_member_id(
        operation=operation,
        field_name="object_projection_graph_edge_id",
    )
    class_config_relationship_id = _field_text(
        operation=operation,
        field_name="class_config_relationship_id",
    )
    include = _field_text(operation=operation, field_name="include") or "required"
    multiplicity = _field_text(operation=operation, field_name="multiplicity") or "many"
    traversal_direction = (
        _field_text(operation=operation, field_name="traversal_direction") or "forward"
    )
    attribute_role = (
        _field_text(operation=operation, field_name="attribute_role") or "reference"
    )
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_projection_graph_semantic_key", opg_semantic_key),
            ("object_projection_graph_id", opg_object_id),
            ("object_projection_graph_edge_id", edge_id),
            ("class_config_relationship_id", class_config_relationship_id),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_edge_create_requires_projection_and_relationship",
            blockers=tuple(f"missing_opg_edge_create_{field}" for field in missing),
        )

    assert opg_semantic_key is not None
    assert opg_object_id is not None
    assert edge_id is not None
    assert class_config_relationship_id is not None
    return _opg_member_create_result(
        operation=operation,
        opg_semantic_key=opg_semantic_key,
        opg_object_id=opg_object_id,
        expected_result_object_id=edge_id,
        invocation_order=OPG_CREATE_EDGE_INVOCATION_ORDER,
        function_name="create_edge",
        function_ref=OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION_REF,
        kwargs={
            "class_config_relationship_id": class_config_relationship_id,
            "include": include,
            "multiplicity": multiplicity,
            "traversal_direction": traversal_direction,
            "depth_limit": _int_field(operation=operation, field_name="depth_limit"),
            "attribute_role": attribute_role,
            "loading_override": _field_text(
                operation=operation,
                field_name="loading_override",
            ),
        },
        reason="meta_opg_edge_create_function_call_ready",
    )


def _plan_opg_constructor_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    opg_semantic_key = _opg_semantic_key(operation=operation)
    opg_object_id = _opg_receiver_object_id(
        opg_semantic_key=opg_semantic_key,
        operation=operation,
        context=context,
    )
    constructor_id = _opg_member_id(
        operation=operation,
        field_name="object_projection_graph_constructor_id",
    )
    root_node_id = _field_text(operation=operation, field_name="root_node_id")
    function_constructor_id = _field_text(
        operation=operation,
        field_name="function_constructor_id",
    )
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_projection_graph_semantic_key", opg_semantic_key),
            ("object_projection_graph_id", opg_object_id),
            ("object_projection_graph_constructor_id", constructor_id),
            ("root_node_id", root_node_id),
            ("function_constructor_id", function_constructor_id),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_constructor_create_requires_projection_root_and_function",
            blockers=tuple(
                f"missing_opg_constructor_create_{field}" for field in missing
            ),
        )

    assert opg_semantic_key is not None
    assert opg_object_id is not None
    assert constructor_id is not None
    assert root_node_id is not None
    assert function_constructor_id is not None
    return _opg_member_create_result(
        operation=operation,
        opg_semantic_key=opg_semantic_key,
        opg_object_id=opg_object_id,
        expected_result_object_id=constructor_id,
        invocation_order=OPG_CREATE_CONSTRUCTOR_INVOCATION_ORDER,
        function_name="create_constructor",
        function_ref=OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION_REF,
        kwargs={
            "root_node_id": root_node_id,
            "function_constructor_id": function_constructor_id,
        },
        reason="meta_opg_constructor_create_function_call_ready",
    )


def _plan_opg_relationship_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    opg_semantic_key = _opg_semantic_key(operation=operation)
    opg_object_id = _opg_receiver_object_id(
        opg_semantic_key=opg_semantic_key,
        operation=operation,
        context=context,
    )
    relationship_id = _opg_member_id(
        operation=operation,
        field_name="object_projection_graph_relationship_id",
    )
    target_opg_id = _field_text(
        operation=operation,
        field_name="target_object_projection_graph_id",
    )
    class_config_relationship_id = _field_text(
        operation=operation,
        field_name="class_config_relationship_id",
    )
    source_node_id = _field_text(
        operation=operation,
        field_name="source_object_projection_graph_node_id",
    )
    target_node_id = _field_text(
        operation=operation,
        field_name="target_object_projection_graph_node_id",
    )
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_projection_graph_semantic_key", opg_semantic_key),
            ("object_projection_graph_id", opg_object_id),
            ("object_projection_graph_relationship_id", relationship_id),
            ("target_object_projection_graph_id", target_opg_id),
            ("class_config_relationship_id", class_config_relationship_id),
            ("source_object_projection_graph_node_id", source_node_id),
            ("target_object_projection_graph_node_id", target_node_id),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_relationship_create_requires_projection_nodes_and_relationship",
            blockers=tuple(
                f"missing_opg_relationship_create_{field}" for field in missing
            ),
        )

    assert opg_semantic_key is not None
    assert opg_object_id is not None
    assert relationship_id is not None
    assert target_opg_id is not None
    assert class_config_relationship_id is not None
    assert source_node_id is not None
    assert target_node_id is not None
    return _opg_member_create_result(
        operation=operation,
        opg_semantic_key=opg_semantic_key,
        opg_object_id=opg_object_id,
        expected_result_object_id=relationship_id,
        invocation_order=OPG_CREATE_RELATIONSHIP_INVOCATION_ORDER,
        function_name="create_relationship",
        function_ref=OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION_REF,
        kwargs={
            "target_object_projection_graph_id": target_opg_id,
            "class_config_relationship_id": class_config_relationship_id,
            "source_object_projection_graph_node_id": source_node_id,
            "target_object_projection_graph_node_id": target_node_id,
        },
        reason="meta_opg_relationship_create_function_call_ready",
    )


def _plan_object_instance_graph_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    opg_semantic_key = _opg_semantic_key(operation=operation)
    opg_object_id = _opg_receiver_object_id(
        opg_semantic_key=opg_semantic_key,
        operation=operation,
        context=context,
    )
    object_instance_graph_id = _opg_member_id(
        operation=operation,
        field_name="object_instance_graph_id",
    )
    key = _field_text(operation=operation, field_name="key")
    root_class_config_id = _field_text(
        operation=operation,
        field_name="root_class_config_id",
    )
    root_source_object_id = _field_text(
        operation=operation,
        field_name="root_source_object_id",
    )
    name = _field_text(operation=operation, field_name="name")
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_projection_graph_semantic_key", opg_semantic_key),
            ("object_projection_graph_id", opg_object_id),
            ("object_instance_graph_id", object_instance_graph_id),
            ("key", key),
            ("root_class_config_id", root_class_config_id),
            ("root_source_object_id", root_source_object_id),
            ("name", name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_oig_create_requires_projection_root_and_identity",
            blockers=tuple(f"missing_opg_oig_create_{field}" for field in missing),
        )

    assert opg_semantic_key is not None
    assert opg_object_id is not None
    assert object_instance_graph_id is not None
    assert key is not None
    assert root_class_config_id is not None
    assert root_source_object_id is not None
    assert name is not None
    return _opg_member_create_result(
        operation=operation,
        opg_semantic_key=opg_semantic_key,
        opg_object_id=opg_object_id,
        expected_result_object_id=object_instance_graph_id,
        invocation_order=OPG_CREATE_OBJECT_INSTANCE_GRAPH_INVOCATION_ORDER,
        function_name="create_object_instance_graph",
        function_ref=OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION_REF,
        kwargs={
            "key": key,
            "root_class_config_id": root_class_config_id,
            "root_source_object_id": root_source_object_id,
            "name": name,
            "description": _field_text(operation=operation, field_name="description"),
            "hash": _field_text(operation=operation, field_name="hash") or "",
        },
        reason="meta_opg_oig_create_function_call_ready",
    )


def _plan_projection_declaration_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        operation=operation,
        context=context,
    )
    declaration_id = _opg_member_id(
        operation=operation,
        field_name="object_projection_graph_declaration_id",
    )
    key = _field_text(operation=operation, field_name="key")
    projection_name = _field_text(operation=operation, field_name="projection_name")
    missing = tuple(
        field_name
        for field_name, value in (
            ("graph_semantic_key", graph_semantic_key),
            ("object_config_graph_id", graph_object_id),
            ("object_projection_graph_declaration_id", declaration_id),
            ("key", key),
            ("projection_name", projection_name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_projection_declaration_create_requires_graph_and_identity",
            blockers=tuple(
                f"missing_opg_projection_declaration_create_{field}"
                for field in missing
            ),
        )

    assert graph_semantic_key is not None
    assert graph_object_id is not None
    assert declaration_id is not None
    assert key is not None
    assert projection_name is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_opg_projection_declaration_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_object_projection_graph_declaration",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=OPG_CREATE_PROJECTION_DECLARATION_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraph",
                function_name="create_object_projection_graph_declaration",
                function_ref=OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION_REF,
                target_object_id=graph_object_id,
                receiver_semantic_key=graph_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=declaration_id,
                target_projection_name="ObjectConfigGraph",
                lane_state_role="created_in_plan_member",
                commit_required=True,
                kwargs={
                    "key": key,
                    "projection_name": projection_name,
                    "label": _field_text(operation=operation, field_name="label"),
                    "description": _field_text(
                        operation=operation,
                        field_name="description",
                    ),
                    "is_branchable": _bool_field(
                        operation=operation,
                        field_name="is_branchable",
                        default=False,
                    ),
                    "object_projection_graph_declaration_id": declaration_id,
                },
                reason="meta_opg_projection_declaration_create_function_call_ready",
            ),
        ),
    )


def _plan_projection_binding_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    declaration_semantic_key = _projection_declaration_semantic_key(
        operation=operation,
    )
    declaration_object_id = _projection_declaration_receiver_object_id(
        declaration_semantic_key=declaration_semantic_key,
        operation=operation,
        context=context,
    )
    binding_id = _opg_member_id(
        operation=operation,
        field_name="object_projection_graph_binding_id",
    )
    fqn_prefix = _field_text(operation=operation, field_name="fqn_prefix")
    namespace = _field_text(operation=operation, field_name="namespace")
    class_name = _field_text(operation=operation, field_name="class_name")
    missing = tuple(
        field_name
        for field_name, value in (
            (
                "object_projection_graph_declaration_semantic_key",
                declaration_semantic_key,
            ),
            ("object_projection_graph_declaration_id", declaration_object_id),
            ("object_projection_graph_binding_id", binding_id),
            ("fqn_prefix", fqn_prefix),
            ("namespace", namespace),
            ("class_name", class_name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_projection_binding_create_requires_declaration_and_identity",
            blockers=tuple(
                f"missing_opg_projection_binding_create_{field}" for field in missing
            ),
        )

    assert declaration_semantic_key is not None
    assert declaration_object_id is not None
    assert binding_id is not None
    assert fqn_prefix is not None
    assert namespace is not None
    assert class_name is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_opg_projection_binding_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_binding",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=OPG_CREATE_PROJECTION_BINDING_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectProjectionGraphDeclaration",
                function_name="create_binding",
                function_ref=OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION_REF,
                target_object_id=declaration_object_id,
                receiver_semantic_key=declaration_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=binding_id,
                target_projection_name="ObjectConfigGraph",
                lane_state_role="created_in_plan_member",
                commit_required=True,
                kwargs={
                    "fqn_prefix": fqn_prefix,
                    "namespace": namespace,
                    "class_name": class_name,
                    "attribute_name": _field_text(
                        operation=operation,
                        field_name="attribute_name",
                    ),
                    "target_projection_name": _field_text(
                        operation=operation,
                        field_name="target_projection_name",
                    ),
                    "side": _field_text(operation=operation, field_name="side"),
                    "object_projection_graph_binding_id": binding_id,
                },
                reason="meta_opg_projection_binding_create_function_call_ready",
            ),
        ),
    )


def _opg_member_create_result(
    *,
    operation: OntologyTypedOperation,
    opg_semantic_key: str,
    opg_object_id: str,
    expected_result_object_id: str,
    invocation_order: int,
    function_name: str,
    function_ref: str,
    kwargs: dict[str, object],
    reason: str,
) -> OntologyOperationHandlerResult:
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason=reason,
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:{function_name}",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=invocation_order,
                invocation_mode="instance",
                owner_class_name="ObjectProjectionGraph",
                function_name=function_name,
                function_ref=function_ref,
                target_object_id=opg_object_id,
                receiver_semantic_key=opg_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=expected_result_object_id,
                target_projection_name="ObjectProjectionGraph",
                lane_state_role="created_in_plan_member",
                commit_required=True,
                kwargs=kwargs,
                reason=reason,
            ),
        ),
    )


def _unsupported_family(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_opg_delta_requires_create_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _graph_receiver_object_id(
    *,
    graph_semantic_key: str | None,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    if graph_semantic_key is not None:
        graph_operation = context.operation_by_semantic_key.get(graph_semantic_key)
        if graph_operation is not None:
            graph_payload = mapping_value(graph_operation.current.get("payload"))
            return _first_text(
                graph_operation.current.get("entity_id"),
                graph_payload.get("entity_id"),
                graph_operation.current.get("object_id"),
                graph_payload.get("object_id"),
            )
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_config_graph_id"),
        payload.get("object_config_graph_id"),
    )


def _opg_receiver_object_id(
    *,
    opg_semantic_key: str | None,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    if opg_semantic_key is not None:
        opg_operation = context.operation_by_semantic_key.get(opg_semantic_key)
        if opg_operation is not None:
            opg_payload = mapping_value(opg_operation.current.get("payload"))
            return _first_text(
                opg_operation.current.get("entity_id"),
                opg_payload.get("entity_id"),
                opg_operation.current.get("object_projection_graph_id"),
                opg_payload.get("object_projection_graph_id"),
            )
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_projection_graph_id"),
        payload.get("object_projection_graph_id"),
    )


def _projection_declaration_receiver_object_id(
    *,
    declaration_semantic_key: str | None,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    if declaration_semantic_key is not None:
        declaration_operation = context.operation_by_semantic_key.get(
            declaration_semantic_key,
        )
        if declaration_operation is not None:
            declaration_payload = mapping_value(
                declaration_operation.current.get("payload"),
            )
            return _first_text(
                declaration_operation.current.get("entity_id"),
                declaration_payload.get("entity_id"),
                declaration_operation.current.get(
                    "object_projection_graph_declaration_id",
                ),
                declaration_payload.get("object_projection_graph_declaration_id"),
            )
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_projection_graph_declaration_id"),
        payload.get("object_projection_graph_declaration_id"),
    )


def _graph_semantic_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        _graph_semantic_key_from_opg_semantic_key(operation.semantic_key),
    )


def _opg_semantic_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_projection_graph_semantic_key"),
        payload.get("object_projection_graph_semantic_key"),
        _opg_semantic_key_from_node_semantic_key(operation.semantic_key),
        _opg_semantic_key_from_member_semantic_key(operation.semantic_key),
    )


def _projection_declaration_semantic_key(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_projection_graph_declaration_semantic_key"),
        payload.get("object_projection_graph_declaration_semantic_key"),
        _projection_declaration_key_from_binding_semantic_key(
            operation.semantic_key,
        ),
    )


def _opg_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("object_projection_graph_id"),
        payload.get("object_projection_graph_id"),
    )


def _opg_node_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("object_projection_graph_node_id"),
        payload.get("object_projection_graph_node_id"),
    )


def _opg_member_id(
    *,
    operation: OntologyTypedOperation,
    field_name: str,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get(field_name),
        payload.get(field_name),
    )


def _opg_node_class_config_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("class_config_id"),
        payload.get("class_config_id"),
    )


def _opg_name(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(operation.current.get("name"), payload.get("name"))


def _opg_projection_hash(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("projection_hash"),
        payload.get("projection_hash"),
        "",
    )


def _opg_language(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("language"),
        payload.get("language"),
        "aware",
    )


def _opg_description(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("description"),
        payload.get("description"),
    )


def _opg_supports_virtual_build(*, operation: OntologyTypedOperation) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(
            operation.current.get("supports_virtual_build"),
            payload.get("supports_virtual_build"),
            True,
        )
    )


def _opg_node_is_root(*, operation: OntologyTypedOperation) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(operation.current.get("is_root"), payload.get("is_root"), False)
    )


def _opg_node_required_for_validity(*, operation: OntologyTypedOperation) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(
            operation.current.get("required_for_validity"),
            payload.get("required_for_validity"),
            False,
        )
    )


def _bool_field(
    *,
    operation: OntologyTypedOperation,
    field_name: str,
    default: bool,
) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(
            operation.current.get(field_name),
            payload.get(field_name),
            default,
        )
    )


def _opg_node_selection(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("selection"),
        payload.get("selection"),
        "all",
    )


def _opg_node_top_n(*, operation: OntologyTypedOperation) -> int | None:
    payload = mapping_value(operation.current.get("payload"))
    value = _first_value(operation.current.get("top_n"), payload.get("top_n"))
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _opg_node_selector_condition_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("selector_condition_id"),
        payload.get("selector_condition_id"),
    )


def _opg_node_policy_refs(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    payload = mapping_value(operation.current.get("payload"))
    value = _first_value(
        operation.current.get("policy_refs"), payload.get("policy_refs")
    )
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text for text in (optional_text(item) for item in value) if text is not None
    )


def _field_text(
    *,
    operation: OntologyTypedOperation,
    field_name: str,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(operation.current.get(field_name), payload.get(field_name))


def _int_field(
    *,
    operation: OntologyTypedOperation,
    field_name: str,
) -> int | None:
    value = _first_value(
        operation.current.get(field_name),
        mapping_value(operation.current.get("payload")).get(field_name),
    )
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _graph_semantic_key_from_opg_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/projection:")
    if not separator:
        return None
    return optional_text(graph_key)


def _opg_semantic_key_from_node_semantic_key(value: str) -> str | None:
    opg_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return optional_text(opg_key)


def _opg_semantic_key_from_member_semantic_key(value: str) -> str | None:
    for separator in (
        "/edge:",
        "/constructor:",
        "/relationship:",
        "/object_instance_graph:",
    ):
        opg_key, matched_separator, _ = value.partition(separator)
        if matched_separator:
            return optional_text(opg_key)
    return None


def _projection_declaration_key_from_binding_semantic_key(
    value: str,
) -> str | None:
    declaration_key, separator, _ = value.partition("/binding:")
    if not separator:
        return None
    return optional_text(declaration_key)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _first_value(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


__all__ = [
    "HANDLER_KEY",
    "OBJECT_CONFIG_GRAPH_CREATE_PROJECTION_DECLARATION_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_CREATE_CONSTRUCTOR_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_CREATE_EDGE_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_CREATE_OBJECT_INSTANCE_GRAPH_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_DECLARATION_CREATE_BINDING_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_CREATE_RELATIONSHIP_FUNCTION_REF",
    "OPG_CREATE_CONSTRUCTOR_INVOCATION_ORDER",
    "OPG_CREATE_EDGE_INVOCATION_ORDER",
    "OPG_CREATE_NODE_INVOCATION_ORDER",
    "OPG_CREATE_OBJECT_INSTANCE_GRAPH_INVOCATION_ORDER",
    "OPG_CREATE_PROJECTION_BINDING_INVOCATION_ORDER",
    "OPG_CREATE_PROJECTION_DECLARATION_INVOCATION_ORDER",
    "OPG_CREATE_RELATIONSHIP_INVOCATION_ORDER",
    "OPG_CREATE_ROOT_INVOCATION_ORDER",
    "plan_object_projection_graph_operation",
]
