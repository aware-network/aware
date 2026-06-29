from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import SimpleNamespace
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_package_id,
    stable_object_projection_graph_id,
    stable_object_projection_graph_node_id,
)
from aware_meta.attribute.config.deltas.typed_operations import (
    attribute_config_create_typed_operation,
)
from aware_meta.class_.config.deltas.typed_operations import (
    class_config_create_typed_operation,
)
from aware_meta.graph.config.stable_ids import (
    stable_class_config_id,
    stable_object_config_graph_node_id,
)
from aware_meta.graph.config.deltas.typed_operations import (
    OBJECT_CONFIG_GRAPH_BUILD_FUNCTION,
    object_config_graph_create_typed_operation,
)
from aware_meta.graph.package.deltas.typed_operations import (
    OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_FUNCTION,
    OBJECT_CONFIG_GRAPH_PACKAGE_BUILD_FUNCTION,
    object_config_graph_package_attach_graph_typed_operation,
    object_config_graph_package_create_typed_operation,
)
from aware_meta.graph.projection.deltas.typed_operations import (
    OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION,
    OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION,
    object_projection_graph_create_typed_operation,
    object_projection_graph_node_create_typed_operation,
)
from aware_meta.materialization.deltas.capability_matrix import (
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.materialization.deltas.semantic_scope_closure import (
    SCOPE_STATUS_READY,
    SYMBOL_KIND_CLASS,
    build_meta_ocg_semantic_scope_closure,
    MetaOcgSemanticScopeClosureEvidence,
)


OCG_GENESIS_CONTRACT_VERSION = (
    "aware.meta.ocg.package-genesis-typed-operation.v0"
)
OCG_GENESIS_PROVIDER_DELTA_CONSUMER_CONTRACT_VERSION = (
    "aware.meta.ocg.package-genesis-provider-delta-consumer.v0"
)
OCG_GENESIS_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION = (
    "aware.meta.ocg.package-genesis-semantic-dirty-diff.v0"
)
OCG_GENESIS_PROJECTION_PORTAL_CONSUMER_CONTRACT_VERSION = (
    "aware.meta.ocg.package-genesis-projection-portal-consumer.v0"
)
OCG_GENESIS_COMPOSITION_KEY = "meta_ocg_genesis"
OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY = (
    "aware_meta.ocg_genesis.object_projection_graphs"
)
OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PROJECTION_NAME = "ObjectProjectionGraph"


@dataclass(frozen=True, slots=True)
class MetaOcgGenesisSpec:
    package_name: str
    fqn_prefix: str
    source_ref: str
    package_id: str
    object_config_graph_id: str
    object_config_graph_node_id: str
    class_config_id: str
    attribute_config_id: str
    object_projection_graph_id: str
    object_projection_graph_node_id: str
    class_name: str
    attribute_name: str
    primitive_base_type: str = "string"
    language: str = "aware"
    graph_name: str | None = None
    graph_hash: str = ""
    layout_hash: str | None = None
    projection_name: str | None = None
    projection_hash: str = ""
    projection_description: str | None = None
    projection_supports_virtual_build: bool = True
    projection_node_required_for_validity: bool = True
    projection_node_selection: str = "all"
    package_title: str | None = None
    package_description: str | None = None
    class_description: str | None = None
    attribute_description: str | None = None

    @property
    def resolved_graph_name(self) -> str:
        return self.graph_name or self.package_name

    @property
    def resolved_projection_name(self) -> str:
        return self.projection_name or self.resolved_graph_name

    @property
    def graph_semantic_key(self) -> str:
        return f"ocg:{self.fqn_prefix}"

    @property
    def package_semantic_key(self) -> str:
        return f"ocg_package:{self.package_name}"

    @property
    def class_fqn(self) -> str:
        return f"{self.fqn_prefix}.{self.class_name}"

    @property
    def class_semantic_key(self) -> str:
        return f"{self.graph_semantic_key}/node:{self.class_fqn}"

    @property
    def attribute_semantic_key(self) -> str:
        return f"{self.class_semantic_key}/attribute:{self.attribute_name}"

    @property
    def object_projection_graph_semantic_key(self) -> str:
        return f"{self.graph_semantic_key}/projection:{self.resolved_projection_name}"

    @property
    def object_projection_graph_node_semantic_key(self) -> str:
        return (
            f"{self.object_projection_graph_semantic_key}"
            f"/node:{self.class_fqn}"
        )


def ocg_genesis_typed_operation_plan(
    *,
    spec: MetaOcgGenesisSpec,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ) = None,
) -> dict[str, object]:
    scope_closure_payload = _ocg_genesis_scope_closure_payload(
        spec=spec,
        semantic_scope_closure=semantic_scope_closure,
    )
    scope_blockers = _ocg_genesis_scope_closure_blockers(
        spec=spec,
        semantic_scope_closure=scope_closure_payload,
    )
    if scope_blockers:
        return _blocked_ocg_genesis_typed_operation_plan(
            spec=spec,
            semantic_scope_closure=scope_closure_payload,
            blockers=scope_blockers,
        )

    operations = (
        object_config_graph_package_create_typed_operation(
            package_name=spec.package_name,
            fqn_prefix=spec.fqn_prefix,
            package_id=spec.package_id,
            semantic_key=spec.package_semantic_key,
            source_refs=(spec.source_ref,),
            title=spec.package_title,
            description=spec.package_description,
        ),
        object_config_graph_create_typed_operation(
            fqn_prefix=spec.fqn_prefix,
            semantic_key=spec.graph_semantic_key,
            object_config_graph_id=spec.object_config_graph_id,
            name=spec.resolved_graph_name,
            source_refs=(spec.source_ref,),
            graph_hash=spec.graph_hash,
            layout_hash=spec.layout_hash,
            language=spec.language,
            description=spec.package_description,
        ),
        object_config_graph_package_attach_graph_typed_operation(
            package_name=spec.package_name,
            package_id=spec.package_id,
            object_config_graph_id=spec.object_config_graph_id,
            semantic_key=spec.package_semantic_key,
            source_refs=(spec.source_ref,),
            title=spec.package_title,
            description=spec.package_description,
        ),
        class_config_create_typed_operation(
            semantic_key=spec.class_semantic_key,
            graph_semantic_key=spec.graph_semantic_key,
            object_config_graph_node_id=spec.object_config_graph_node_id,
            class_config_id=spec.class_config_id,
            node_key=spec.class_fqn,
            class_fqn=spec.class_fqn,
            class_name=spec.class_name,
            source_refs=(spec.source_ref,),
            description=spec.class_description,
        ),
        attribute_config_create_typed_operation(
            semantic_key=spec.attribute_semantic_key,
            attribute_config_id=spec.attribute_config_id,
            owner_semantic_key=spec.class_semantic_key,
            attribute_name=spec.attribute_name,
            source_refs=(spec.source_ref,),
            primitive_base_type=spec.primitive_base_type,
            description=spec.attribute_description,
        ),
        object_projection_graph_create_typed_operation(
            semantic_key=spec.object_projection_graph_semantic_key,
            graph_semantic_key=spec.graph_semantic_key,
            object_config_graph_id=spec.object_config_graph_id,
            object_projection_graph_id=spec.object_projection_graph_id,
            name=spec.resolved_projection_name,
            projection_hash=spec.projection_hash,
            source_refs=(spec.source_ref,),
            language=spec.language,
            description=spec.projection_description,
            supports_virtual_build=spec.projection_supports_virtual_build,
        ),
        object_projection_graph_node_create_typed_operation(
            semantic_key=spec.object_projection_graph_node_semantic_key,
            object_projection_graph_semantic_key=(
                spec.object_projection_graph_semantic_key
            ),
            object_projection_graph_id=spec.object_projection_graph_id,
            object_projection_graph_node_id=(
                spec.object_projection_graph_node_id
            ),
            class_config_id=spec.class_config_id,
            source_refs=(spec.source_ref,),
            is_root=True,
            required_for_validity=spec.projection_node_required_for_validity,
            selection=spec.projection_node_selection,
        ),
    )
    operation_payloads = _operation_payloads(operations=operations)
    return {
        "plan_kind": "meta_ocg_package_genesis_typed_operation_plan",
        "contract_version": OCG_GENESIS_CONTRACT_VERSION,
        "operation_composition": {
            "composition_key": OCG_GENESIS_COMPOSITION_KEY,
            "composition_kind": "meta_ocg_package_genesis",
            "package_semantic_key": spec.package_semantic_key,
            "graph_semantic_key": spec.graph_semantic_key,
        },
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_package_genesis_typed_operations_ready",
        "typed_operation_count": len(operations),
        "semantic_scope_closure_status": scope_closure_payload.get("status"),
        "semantic_scope_closure_ready": True,
        "semantic_scope_closure_consumed": True,
        "semantic_scope_closure": scope_closure_payload,
        "semantic_scope_closure_blockers": (),
        "semantic_object_anchors": (),
        "typed_operations": operation_payloads,
        "blocked_operations": (),
        "operation_type_counts": _count_by_field(
            entries=operation_payloads,
            field_name="provider_operation_type",
        ),
        "ontology_subject_kind_counts": _count_by_field(
            entries=operation_payloads,
            field_name="ontology_subject_kind",
        ),
        "required_ontology_functions": (
            OBJECT_CONFIG_GRAPH_PACKAGE_BUILD_FUNCTION,
            OBJECT_CONFIG_GRAPH_BUILD_FUNCTION,
            OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_FUNCTION,
            "ObjectConfigGraph.create_node",
            "ObjectConfigGraphNode.create_class",
            "ClassConfig.create_primitive_attribute_config",
            OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION,
            OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION,
        ),
        "builder_fallback_used": False,
        "would_use_builder": False,
    }


def ocg_genesis_preflight(
    *,
    spec: MetaOcgGenesisSpec,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ) = None,
) -> dict[str, object]:
    typed_operation_plan = ocg_genesis_typed_operation_plan(
        spec=spec,
        semantic_scope_closure=semantic_scope_closure,
    )
    if typed_operation_plan.get("status") != "typed_operation_plan_ready":
        blockers = _tuple_text(typed_operation_plan.get("blockers"))
        return {
            "preflight_kind": "meta_ocg_package_genesis_preflight",
            "contract_version": OCG_GENESIS_CONTRACT_VERSION,
            "status": "ocg_genesis_blocked",
            "reason": "meta_ocg_package_genesis_typed_operation_plan_blocked",
            "typed_operation_plan": typed_operation_plan,
            "ontology_execution_plan": None,
            "functioncall_capability_matrix": None,
            "typed_operation_count": 0,
            "ontology_invocation_intent_count": 0,
            "executable_operation_count": 0,
            "non_executable_operation_count": 0,
            "blocker_count": len(blockers),
            "blockers": blockers,
            "execution_allowed": False,
            "builder_fallback_used": False,
            "would_use_builder": False,
            "did_execute": False,
            "did_persist": False,
        }
    ontology_execution_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    functioncall_capability_matrix = (
        build_provider_delta_functioncall_capability_matrix(
            provider_delta_typed_operation_plan=typed_operation_plan,
            provider_delta_ontology_execution_plan=ontology_execution_plan,
        )
    )
    execution_allowed = (
        functioncall_capability_matrix.get("execution_allowed") is True
    )
    blockers = tuple(
        dict.fromkeys(
            (
                *_tuple_text(ontology_execution_plan.get("blockers")),
                *_tuple_text(functioncall_capability_matrix.get("blockers")),
            )
        )
    )
    return {
        "preflight_kind": "meta_ocg_package_genesis_preflight",
        "contract_version": OCG_GENESIS_CONTRACT_VERSION,
        "status": (
            "ocg_genesis_executable"
            if execution_allowed
            else "ocg_genesis_blocked"
        ),
        "reason": (
            "meta_ocg_package_genesis_functioncalls_ready"
            if execution_allowed
            else "meta_ocg_package_genesis_functioncalls_blocked"
        ),
        "typed_operation_plan": typed_operation_plan,
        "ontology_execution_plan": ontology_execution_plan,
        "functioncall_capability_matrix": functioncall_capability_matrix,
        "typed_operation_count": typed_operation_plan["typed_operation_count"],
        "ontology_invocation_intent_count": ontology_execution_plan.get(
            "invocation_intent_count",
            0,
        ),
        "executable_operation_count": functioncall_capability_matrix.get(
            "executable_operation_count",
            0,
        ),
        "non_executable_operation_count": functioncall_capability_matrix.get(
            "non_executable_operation_count",
            0,
        ),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "execution_allowed": execution_allowed,
        "builder_fallback_used": False,
        "would_use_builder": False,
        "did_execute": False,
        "did_persist": False,
    }


def ocg_genesis_preflight_from_provider_delta_request(
    *,
    request: object,
    analysis: object,
) -> dict[str, object]:
    lane_state = _provider_delta_lane_state_payload(request=request)
    lane_status = _optional_text(lane_state.get("status"))
    base_payload = {
        "preflight_kind": "meta_ocg_package_genesis_provider_delta_consumer",
        "contract_version": (
            OCG_GENESIS_PROVIDER_DELTA_CONSUMER_CONTRACT_VERSION
        ),
        "provider_delta_lane_state": lane_state,
        "provider_delta_lane_state_status": lane_status,
        "builder_fallback_used": False,
        "would_use_builder": False,
        "did_execute": False,
        "did_persist": False,
    }
    if lane_status != "empty_lane":
        return {
            **base_payload,
            "status": "ocg_genesis_not_applicable",
            "reason": "provider_delta_lane_state_not_empty_lane",
            "route_active": False,
            "blockers": (),
            "blocker_count": 0,
            "typed_operation_plan": None,
            "ontology_execution_plan": None,
            "functioncall_capability_matrix": None,
        }

    portal_consumer = _ocg_genesis_projection_portal_consumer_evidence(
        request=request,
    )
    portal_blockers = _tuple_text(portal_consumer.get("blockers"))
    if portal_blockers:
        return {
            **base_payload,
            "status": "ocg_genesis_blocked",
            "reason": "meta_ocg_package_genesis_projection_portal_blocked",
            "route_active": True,
            "projection_portal_consumer_status": _optional_text(
                portal_consumer.get("status")
            ),
            "projection_portal_consumer": portal_consumer,
            "blockers": portal_blockers,
            "blocker_count": len(portal_blockers),
            "typed_operation_plan": None,
            "ontology_execution_plan": None,
            "functioncall_capability_matrix": None,
        }

    spec_result = _ocg_genesis_spec_from_provider_delta_analysis(
        request=request,
        analysis=analysis,
        lane_state=lane_state,
    )
    blockers = _tuple_text(spec_result.get("blockers"))
    spec = spec_result.get("spec")
    if blockers or not isinstance(spec, MetaOcgGenesisSpec):
        return {
            **base_payload,
            "status": "ocg_genesis_blocked",
            "reason": "meta_ocg_package_genesis_inputs_blocked",
            "route_active": True,
            "projection_portal_consumer_status": _optional_text(
                portal_consumer.get("status")
            ),
            "projection_portal_consumer": portal_consumer,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "typed_operation_plan": None,
            "ontology_execution_plan": None,
            "functioncall_capability_matrix": None,
        }

    preflight = ocg_genesis_preflight(spec=spec)
    execution_allowed = preflight.get("execution_allowed") is True
    return {
        **base_payload,
        "status": (
            "ocg_genesis_consumer_ready"
            if execution_allowed
            else "ocg_genesis_blocked"
        ),
        "reason": (
            "provider_delta_empty_lane_ocg_genesis_ready"
            if execution_allowed
            else "provider_delta_empty_lane_ocg_genesis_blocked"
        ),
        "route_active": True,
        "projection_portal_consumer_status": _optional_text(
            portal_consumer.get("status")
        ),
        "projection_portal_consumer": portal_consumer,
        "spec": _ocg_genesis_spec_payload(spec=spec),
        "preflight": preflight,
        "typed_operation_plan": preflight["typed_operation_plan"],
        "ontology_execution_plan": preflight["ontology_execution_plan"],
        "functioncall_capability_matrix": (
            preflight["functioncall_capability_matrix"]
        ),
        "typed_operation_count": preflight["typed_operation_count"],
        "ontology_invocation_intent_count": preflight[
            "ontology_invocation_intent_count"
        ],
        "executable_operation_count": preflight["executable_operation_count"],
        "blockers": preflight["blockers"],
        "blocker_count": preflight["blocker_count"],
        "execution_allowed": execution_allowed,
    }


def ocg_genesis_semantic_dirty_diff_from_preflight(
    *,
    preflight: Mapping[str, object],
    current_delta_fingerprint: str,
) -> dict[str, object]:
    typed_operation_plan = _mapping_value(preflight.get("typed_operation_plan"))
    typed_operations = tuple(
        _mapping_value(operation)
        for operation in _sequence(typed_operation_plan.get("typed_operations"))
        if isinstance(operation, Mapping)
    )
    ready = (
        preflight.get("status") == "ocg_genesis_consumer_ready"
        and typed_operation_plan.get("status") == "typed_operation_plan_ready"
        and bool(typed_operations)
    )
    entries = (
        tuple(
            _semantic_dirty_entry_from_genesis_operation(
                operation=operation,
                position=position,
            )
            for position, operation in enumerate(typed_operations)
        )
        if ready
        else ()
    )
    operation_counts = _count_by_field(
        entries=entries,
        field_name="baseline_compare_operation",
    )
    return {
        "diff_kind": "meta_ocg_package_genesis_semantic_dirty_diff",
        "contract_version": OCG_GENESIS_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
        "status": (
            "semantic_dirty_diff_ready"
            if ready
            else "semantic_dirty_diff_blocked"
        ),
        "reason": (
            "meta_ocg_empty_lane_genesis_dirty_diff_ready"
            if ready
            else "meta_ocg_empty_lane_genesis_dirty_diff_blocked"
        ),
        "available": ready,
        "blocked": not ready,
        "current_delta_fingerprint": current_delta_fingerprint,
        "baseline_identity_source": "workspace.provider_delta_lane_state",
        "baseline_semantic_object_index_available": True,
        "baseline_semantic_object_index_status": (
            "baseline_semantic_object_index_empty"
        ),
        "baseline_semantic_object_index_count": 0,
        "baseline_index_compare_available": ready,
        "baseline_index_compare_status": (
            "baseline_index_compared"
            if ready
            else "baseline_index_compare_blocked"
        ),
        "baseline_index_compare_reason": (
            "empty_lane_baseline_index_compared"
            if ready
            else "empty_lane_genesis_preflight_not_ready"
        ),
        "dirty_entry_count": len(entries),
        "semantic_dirty_entries": entries,
        "dirty_operation_counts": operation_counts,
        "baseline_compare_operation_counts": operation_counts,
        "stale_semantic_keys": (),
        "stale_semantic_key_count": 0,
        "provider_delta_lane_state_status": _optional_text(
            _mapping_value(preflight.get("provider_delta_lane_state")).get("status")
        ),
        "provider_delta_empty_lane_genesis_preflight_status": _optional_text(
            preflight.get("status")
        ),
    }


def _blocked_ocg_genesis_typed_operation_plan(
    *,
    spec: MetaOcgGenesisSpec,
    semantic_scope_closure: Mapping[str, object],
    blockers: tuple[str, ...],
) -> dict[str, object]:
    return {
        "plan_kind": "meta_ocg_package_genesis_typed_operation_plan",
        "contract_version": OCG_GENESIS_CONTRACT_VERSION,
        "operation_composition": {
            "composition_key": OCG_GENESIS_COMPOSITION_KEY,
            "composition_kind": "meta_ocg_package_genesis",
            "package_semantic_key": spec.package_semantic_key,
            "graph_semantic_key": spec.graph_semantic_key,
        },
        "status": "typed_operation_plan_blocked",
        "reason": "meta_ocg_semantic_scope_closure_blocked",
        "typed_operation_count": 0,
        "semantic_scope_closure_status": semantic_scope_closure.get("status"),
        "semantic_scope_closure_ready": False,
        "semantic_scope_closure_consumed": False,
        "semantic_scope_closure": dict(semantic_scope_closure),
        "semantic_scope_closure_blockers": blockers,
        "semantic_object_anchors": (),
        "typed_operations": (),
        "blocked_operations": (),
        "blockers": blockers,
        "operation_type_counts": {},
        "ontology_subject_kind_counts": {},
        "required_ontology_functions": (),
        "builder_fallback_used": False,
        "would_use_builder": False,
    }


def _ocg_genesis_scope_closure_payload(
    *,
    spec: MetaOcgGenesisSpec,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ),
) -> Mapping[str, object]:
    if isinstance(semantic_scope_closure, MetaOcgSemanticScopeClosureEvidence):
        return semantic_scope_closure.evidence_payload()
    if isinstance(semantic_scope_closure, Mapping):
        return dict(semantic_scope_closure)
    return _default_ocg_genesis_scope_closure(spec=spec).evidence_payload()


def _default_ocg_genesis_scope_closure(
    *,
    spec: MetaOcgGenesisSpec,
) -> MetaOcgSemanticScopeClosureEvidence:
    class_config = ClassConfig(
        id=UUID(spec.class_config_id),
        class_fqn=spec.class_fqn,
        name=spec.class_name,
        description=spec.class_description,
        object_config_graph_node_id=UUID(spec.object_config_graph_node_id),
    )
    code_id = uuid5(
        NAMESPACE_URL,
        (
            "aware:meta:ocg-genesis:semantic-scope:"
            f"{spec.package_name}:{spec.source_ref}"
        ),
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix=spec.fqn_prefix,
        namespace_by_code_id={
            code_id: NamespacePath(
                package=spec.fqn_prefix,
                namespace="default",
            ),
        },
        class_configs=(class_config,),
    )


def _ocg_genesis_scope_closure_blockers(
    *,
    spec: MetaOcgGenesisSpec,
    semantic_scope_closure: Mapping[str, object],
) -> tuple[str, ...]:
    blockers: list[str] = []
    status = _optional_text(semantic_scope_closure.get("status"))
    if status != SCOPE_STATUS_READY:
        blockers.append(f"semantic_scope_closure_not_ready:{status or 'unknown'}")
    closure_prefix = _optional_text(
        semantic_scope_closure.get("package_fqn_prefix")
    )
    if closure_prefix != spec.fqn_prefix:
        blockers.append(
            "semantic_scope_closure_package_mismatch:"
            f"{closure_prefix or 'unknown'}"
        )
    closure_blockers = _tuple_text(semantic_scope_closure.get("blockers"))
    blockers.extend(closure_blockers)
    if not _scope_closure_contains_class_fqn(
        semantic_scope_closure=semantic_scope_closure,
        class_fqn=spec.class_fqn,
    ):
        blockers.append(
            "semantic_scope_closure_missing_class_fqn:"
            f"{spec.class_fqn}"
        )
    return tuple(dict.fromkeys(blockers))


def _scope_closure_contains_class_fqn(
    *,
    semantic_scope_closure: Mapping[str, object],
    class_fqn: str,
) -> bool:
    for symbol in _sequence(semantic_scope_closure.get("symbols")):
        symbol_payload = _mapping_value(symbol)
        if (
            _optional_text(symbol_payload.get("symbol_kind")) == SYMBOL_KIND_CLASS
            and _optional_text(symbol_payload.get("fqn")) == class_fqn
        ):
            return True
    return False


def _operation_payloads(
    *,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(operation.evidence_payload() for operation in operations)


def _count_by_field(
    *,
    entries: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = str(entry.get(field_name) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _tuple_text(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _ocg_genesis_spec_from_provider_delta_analysis(
    *,
    request: object,
    analysis: object,
    lane_state: Mapping[str, object],
) -> dict[str, object]:
    blockers: list[str] = []
    graph = getattr(analysis, "object_config_graph", None)
    if not isinstance(graph, ObjectConfigGraph):
        return {
            "spec": None,
            "blockers": ("current_object_config_graph_unavailable",),
        }
    class_nodes = _genesis_class_nodes(graph=graph)
    if len(class_nodes) != 1:
        blockers.append(f"ocg_genesis_requires_one_class:{len(class_nodes)}")
    class_node = class_nodes[0] if len(class_nodes) == 1 else None
    class_config = class_node.class_config if class_node is not None else None
    if not isinstance(class_config, ClassConfig):
        blockers.append("ocg_genesis_class_config_unavailable")

    primitive_attributes = (
        _primitive_attribute_configs(class_config=class_config)
        if isinstance(class_config, ClassConfig)
        else ()
    )
    if len(primitive_attributes) != 1:
        blockers.append(
            "ocg_genesis_requires_one_primitive_attribute:"
            f"{len(primitive_attributes)}"
        )
    attribute_config = (
        primitive_attributes[0] if len(primitive_attributes) == 1 else None
    )
    package_name = _request_package_name(request=request, lane_state=lane_state)
    if package_name is None:
        blockers.append("package_name_unavailable")
    source_ref = _analysis_source_ref(analysis=analysis)
    if source_ref is None:
        blockers.append("source_ref_unavailable")
    primitive_base_type = (
        _primitive_base_type(attribute_config=attribute_config)
        if isinstance(attribute_config, AttributeConfig)
        else None
    )
    if primitive_base_type is None:
        blockers.append("primitive_base_type_unavailable")
    if blockers:
        return {"spec": None, "blockers": tuple(dict.fromkeys(blockers))}

    assert class_node is not None
    assert class_config is not None
    assert attribute_config is not None
    assert package_name is not None
    assert source_ref is not None
    assert primitive_base_type is not None
    projection_name = graph.name or package_name
    class_name = class_config.name
    if class_name is None:
        raise ValueError("OCG genesis requires ClassConfig.name")
    class_fqn = f"{graph.fqn_prefix}.{class_name}"
    class_node_id = _genesis_ocg_class_node_id(
        graph=graph,
        class_fqn=class_fqn,
    )
    class_config_id = _genesis_ocg_class_config_id(
        class_node_id=class_node_id,
        class_fqn=class_fqn,
    )
    return {
        "spec": MetaOcgGenesisSpec(
            package_name=package_name,
            fqn_prefix=graph.fqn_prefix,
            source_ref=source_ref,
            package_id=_genesis_package_id(
                package_name=package_name,
                fqn_prefix=graph.fqn_prefix,
                lane_state=lane_state,
            ),
            object_config_graph_id=str(graph.id),
            object_config_graph_node_id=str(class_node_id),
            class_config_id=str(class_config_id),
            attribute_config_id=str(attribute_config.id),
            object_projection_graph_id=_genesis_opg_id(
                object_config_graph_id=str(graph.id),
                projection_name=projection_name,
            ),
            object_projection_graph_node_id=_genesis_opg_node_id(
                object_config_graph_id=str(graph.id),
                projection_name=projection_name,
                class_config_id=str(class_config.id),
            ),
            class_name=class_name,
            attribute_name=attribute_config.name,
            primitive_base_type=primitive_base_type,
            language=_enum_value(graph.language),
            graph_name=graph.name,
            graph_hash=graph.hash,
            layout_hash=graph.layout_hash,
            projection_name=projection_name,
            projection_hash=graph.hash,
            projection_description=graph.description,
            package_title=package_name,
            package_description=graph.description,
            class_description=class_config.description,
            attribute_description=attribute_config.description,
        ),
        "blockers": (),
    }


def _genesis_class_nodes(
    *,
    graph: ObjectConfigGraph,
) -> tuple[ObjectConfigGraphNode, ...]:
    return tuple(
        node
        for node in graph.object_config_graph_nodes
        if isinstance(node, ObjectConfigGraphNode)
        and _enum_value(node.type) == ObjectConfigGraphNodeType.class_.value
        and isinstance(node.class_config, ClassConfig)
    )


def _genesis_ocg_class_node_id(
    *,
    graph: ObjectConfigGraph,
    class_fqn: str,
) -> UUID:
    graph_id = graph.id
    if graph_id is None:
        raise ValueError("OCG genesis requires ObjectConfigGraph.id")
    return stable_object_config_graph_node_id(
        object_config_graph_id=graph_id,
        type=ObjectConfigGraphNodeType.class_.value,
        node_key=class_fqn,
    )


def _genesis_ocg_class_config_id(
    *,
    class_node_id: UUID,
    class_fqn: str,
) -> UUID:
    return stable_class_config_id(
        object_config_graph_node_id=class_node_id,
        class_fqn=class_fqn,
    )


def _primitive_attribute_configs(
    *,
    class_config: ClassConfig,
) -> tuple[AttributeConfig, ...]:
    attributes: list[AttributeConfig] = []
    for edge in class_config.class_config_attribute_configs:
        attribute_config = edge.attribute_config
        if not isinstance(attribute_config, AttributeConfig):
            continue
        descriptor = attribute_config.type_descriptor
        if _enum_value(descriptor.kind) != AttributeTypeDescriptorKind.primitive.value:
            continue
        attributes.append(attribute_config)
    return tuple(attributes)


def _primitive_base_type(
    *,
    attribute_config: AttributeConfig | None,
) -> str | None:
    if attribute_config is None:
        return None
    descriptor = attribute_config.type_descriptor
    primitive_config = descriptor.primitive_config
    if primitive_config is None:
        return None
    primitive_type = primitive_config.primitive_type
    return _optional_text(_enum_value(primitive_type.base_type))


def _genesis_package_id(
    *,
    package_name: str,
    fqn_prefix: str,
    lane_state: Mapping[str, object],
) -> str:
    semantic_package_id = _optional_text(lane_state.get("semantic_package_id"))
    if semantic_package_id is not None:
        return semantic_package_id
    return str(
        stable_object_config_graph_package_id(
            package_name=package_name,
            fqn_prefix=fqn_prefix,
        )
    )


def _genesis_opg_id(
    *,
    object_config_graph_id: str,
    projection_name: str,
) -> str:
    return str(
        stable_object_projection_graph_id(
            object_config_graph_id=UUID(object_config_graph_id),
            name=projection_name,
        )
    )


def _genesis_opg_node_id(
    *,
    object_config_graph_id: str,
    projection_name: str,
    class_config_id: str,
) -> str:
    object_projection_graph_id = stable_object_projection_graph_id(
        object_config_graph_id=UUID(object_config_graph_id),
        name=projection_name,
    )
    return str(
        stable_object_projection_graph_node_id(
            object_projection_graph_id=object_projection_graph_id,
            class_config_id=UUID(class_config_id),
        )
    )


def _request_package_name(
    *,
    request: object,
    lane_state: Mapping[str, object],
) -> str | None:
    package_payload = _object_payload(getattr(request, "package", None))
    lane_package_payload = _mapping_value(lane_state.get("package"))
    return (
        _optional_text(package_payload.get("package_name"))
        or _optional_text(lane_package_payload.get("package_name"))
        or _optional_text(lane_state.get("semantic_package_name"))
    )


def _analysis_source_ref(*, analysis: object) -> str | None:
    preview = getattr(analysis, "change_preview", None)
    changed_files = _tuple_text(getattr(preview, "changed_source_files", None))
    source_files = _tuple_text(getattr(analysis, "source_files", None))
    source_path = (changed_files or source_files or (None,))[0]
    if source_path is None:
        return None
    normalized = source_path.strip().strip("/")
    if not normalized:
        return None
    if normalized.startswith("aware/"):
        return normalized
    return f"aware/{normalized}"


def _ocg_genesis_spec_payload(
    *,
    spec: MetaOcgGenesisSpec,
) -> dict[str, object]:
    return {
        "package_name": spec.package_name,
        "fqn_prefix": spec.fqn_prefix,
        "source_ref": spec.source_ref,
        "package_id": spec.package_id,
        "object_config_graph_id": spec.object_config_graph_id,
        "object_config_graph_node_id": spec.object_config_graph_node_id,
        "class_config_id": spec.class_config_id,
        "attribute_config_id": spec.attribute_config_id,
        "object_projection_graph_id": spec.object_projection_graph_id,
        "object_projection_graph_node_id": spec.object_projection_graph_node_id,
        "class_name": spec.class_name,
        "attribute_name": spec.attribute_name,
        "primitive_base_type": spec.primitive_base_type,
        "language": spec.language,
        "graph_name": spec.resolved_graph_name,
        "graph_hash": spec.graph_hash,
        "layout_hash": spec.layout_hash,
        "projection_name": spec.resolved_projection_name,
        "projection_hash": spec.projection_hash,
    }


def _semantic_dirty_entry_from_genesis_operation(
    *,
    operation: Mapping[str, object],
    position: int,
) -> dict[str, object]:
    current = _mapping_value(operation.get("current"))
    semantic_key = _optional_text(operation.get("semantic_key")) or (
        f"unknown:{position}"
    )
    operation_family = _optional_text(operation.get("operation_family")) or "create"
    ontology_subject_kind = _optional_text(
        operation.get("ontology_subject_kind")
    ) or "unknown"
    source_refs = _tuple_text(operation.get("source_refs"))
    return {
        "entry_kind": "meta_ocg_genesis_semantic_dirty_entry",
        "entry_key": f"dirty:empty_lane_genesis:{position}:{semantic_key}",
        "semantic_key": semantic_key,
        "source_delta_key": f"aware_meta.empty_lane_genesis:{semantic_key}",
        "source": "aware_meta.provider_delta.empty_lane_genesis",
        "source_refs": source_refs,
        "verb": operation_family,
        "semantic_subject_type": _optional_text(
            operation.get("semantic_subject_type")
        ),
        "ontology_subject_kind": ontology_subject_kind,
        "dirty_operation": f"{ontology_subject_kind}_{operation_family}",
        "baseline_compare_status": "empty_lane_create",
        "baseline_compare_operation": "create",
        "baseline_object_matched": False,
        "baseline_object_id": None,
        "baseline_object_kind": ontology_subject_kind,
        "target_semantic_object_id": _optional_text(
            current.get("entity_id")
            or current.get("object_id")
            or current.get("node_id")
            or current.get("semantic_object_id")
        ),
        "payload": current,
    }


def _provider_delta_lane_state_payload(*, request: object) -> dict[str, object]:
    return _object_payload(getattr(request, "provider_delta_lane_state", None))


def _ocg_genesis_projection_portal_consumer_evidence(
    *,
    request: object,
) -> dict[str, object]:
    resolution = _projection_portal_resolution_payload(request=request)
    blockers: list[str] = []
    if not resolution:
        blockers.append("projection_portal_resolution_missing")
        return _projection_portal_consumer_payload(
            status="projection_portal_consumer_blocked",
            reason="projection_portal_resolution_missing",
            resolution=resolution,
            portal={},
            blockers=tuple(blockers),
        )

    resolution_status = _optional_text(resolution.get("status"))
    if resolution_status != "ready":
        blockers.extend(_tuple_text(resolution.get("blockers")))
        blockers.append(
            "projection_portal_resolution_not_ready:"
            f"{resolution_status or 'unknown'}"
        )

    portal = _projection_portal_payload(
        resolution=resolution,
        policy_key=OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY,
    )
    if not portal:
        blockers.append(
            "projection_portal_missing:"
            f"{OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY}"
        )
    else:
        target_projection = _optional_text(portal.get("target_projection"))
        portal_status = _optional_text(portal.get("status"))
        target_lane_status = _optional_text(portal.get("target_lane_status"))
        if target_projection != OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PROJECTION_NAME:
            blockers.append(
                "projection_portal_target_mismatch:"
                f"{target_projection or 'unknown'}"
            )
        if portal_status != "created_in_plan":
            blockers.append(
                "projection_portal_not_created_in_plan:"
                f"{portal_status or 'unknown'}"
            )
        if target_lane_status != "created_in_plan":
            blockers.append(
                "projection_portal_target_lane_not_created_in_plan:"
                f"{target_lane_status or 'unknown'}"
            )
        blockers.extend(_tuple_text(portal.get("blockers")))

    normalized_blockers = tuple(dict.fromkeys(blockers))
    return _projection_portal_consumer_payload(
        status=(
            "projection_portal_consumer_ready"
            if not normalized_blockers
            else "projection_portal_consumer_blocked"
        ),
        reason=(
            "ocg_genesis_object_projection_graph_portal_ready"
            if not normalized_blockers
            else "ocg_genesis_object_projection_graph_portal_blocked"
        ),
        resolution=resolution,
        portal=portal,
        blockers=normalized_blockers,
    )


def _projection_portal_consumer_payload(
    *,
    status: str,
    reason: str,
    resolution: Mapping[str, object],
    portal: Mapping[str, object],
    blockers: tuple[str, ...],
) -> dict[str, object]:
    return {
        "consumer_kind": "meta_ocg_genesis_projection_portal_consumer",
        "contract_version": (
            OCG_GENESIS_PROJECTION_PORTAL_CONSUMER_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "required_policy_key": (
            OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY
        ),
        "required_target_projection": (
            OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PROJECTION_NAME
        ),
        "projection_portal_resolution_status": _optional_text(
            resolution.get("status")
        ),
        "projection_portal_resolution_reason": _optional_text(
            resolution.get("reason")
        ),
        "portal_status": _optional_text(portal.get("status")),
        "portal_reason": _optional_text(portal.get("reason")),
        "portal_target_projection": _optional_text(
            portal.get("target_projection")
        ),
        "portal_target_lane_status": _optional_text(
            portal.get("target_lane_status")
        ),
        "portal": dict(portal),
        "projection_portal_resolution": dict(resolution),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "available": status == "projection_portal_consumer_ready",
        "blocked": status == "projection_portal_consumer_blocked",
    }


def _projection_portal_resolution_payload(
    *,
    request: object,
) -> dict[str, object]:
    previous_evidence = _object_payload(
        getattr(request, "previous_materialization_evidence", None)
    )
    return _mapping_value(previous_evidence.get("projection_portal_resolution"))


def _projection_portal_payload(
    *,
    resolution: Mapping[str, object],
    policy_key: str,
) -> dict[str, object]:
    for portal in _sequence(resolution.get("portals")):
        portal_payload = _mapping_value(portal)
        if _optional_text(portal_payload.get("policy_key")) == policy_key:
            return portal_payload
    return {}


def _object_payload(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    try:
        raw_vars = vars(value)
    except TypeError:
        return {}
    if isinstance(raw_vars, Mapping):
        return {str(key): item for key, item in raw_vars.items()}
    return {}


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return value
    return ()


def _enum_value(value: object) -> str:
    enum_value = getattr(value, "value", value)
    return str(enum_value)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "OCG_GENESIS_COMPOSITION_KEY",
    "OCG_GENESIS_CONTRACT_VERSION",
    "OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY",
    "OCG_GENESIS_PROVIDER_DELTA_CONSUMER_CONTRACT_VERSION",
    "OCG_GENESIS_PROJECTION_PORTAL_CONSUMER_CONTRACT_VERSION",
    "OCG_GENESIS_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION",
    "MetaOcgGenesisSpec",
    "ocg_genesis_preflight",
    "ocg_genesis_preflight_from_provider_delta_request",
    "ocg_genesis_semantic_dirty_diff_from_preflight",
    "ocg_genesis_typed_operation_plan",
]
