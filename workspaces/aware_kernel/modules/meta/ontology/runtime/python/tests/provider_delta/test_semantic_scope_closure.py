from __future__ import annotations

from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.materialization.deltas.semantic_scope_closure import (
    META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION,
    PROBE_STATUS_RESOLVED,
    PROBE_STATUS_UNRESOLVED,
    SCOPE_STATUS_BLOCKED,
    SCOPE_STATUS_READY,
    SYMBOL_KIND_CLASS,
    SYMBOL_KIND_ENUM,
    SYMBOL_ORIGIN_EXTERNAL,
    build_meta_ocg_semantic_scope_closure,
    meta_ocg_enum_fqn_scope_closure_gate,
    MetaOcgSemanticScopeResolutionProbeRequest,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)

from .fixtures import provider_delta_uuid


def test_semantic_scope_closure_resolves_local_import_and_external_symbols() -> None:
    home_code_id = provider_delta_uuid("semantic-scope-home-code")
    api_code_id = provider_delta_uuid("semantic-scope-api-code")
    room_class = _class_config(
        key="semantic-scope-room-class",
        class_fqn="aware_demo.default.home.Room",
        name="Room",
    )
    room_state_enum = _enum_config(
        key="semantic-scope-room-state-enum",
        enum_fqn="aware_demo.default.home.RoomState",
        name="RoomState",
    )
    external_graph = _external_graph()

    evidence = build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            home_code_id: NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
            api_code_id: NamespacePath(
                package="aware_demo",
                namespace="api.endpoint",
            ),
        },
        class_configs=(room_class,),
        enum_configs=(room_state_enum,),
        imports_by_code_id={
            api_code_id: {
                "RoomAlias": "aware_demo.default.home.Room",
                "ExternalSensor": "aware_external.default.sensor.Sensor",
            },
        },
        external_graphs=(external_graph,),
        probes=(
            MetaOcgSemanticScopeResolutionProbeRequest(
                code_id=home_code_id,
                symbol_kind=SYMBOL_KIND_CLASS,
                identifier="Room",
            ),
            MetaOcgSemanticScopeResolutionProbeRequest(
                code_id=api_code_id,
                symbol_kind=SYMBOL_KIND_ENUM,
                identifier="home.RoomState",
            ),
            MetaOcgSemanticScopeResolutionProbeRequest(
                code_id=api_code_id,
                symbol_kind=SYMBOL_KIND_CLASS,
                identifier="ExternalSensor",
            ),
        ),
    )

    assert evidence.status == SCOPE_STATUS_READY
    assert evidence.ready
    assert evidence.namespace_count == 2
    assert evidence.import_alias_count == 2
    assert evidence.local_symbol_count == 2
    assert evidence.external_symbol_count == 1
    assert evidence.blockers == ()
    assert {
        (symbol.origin, symbol.symbol_kind, symbol.fqn) for symbol in evidence.symbols
    } == {
        ("local", SYMBOL_KIND_CLASS, "aware_demo.default.home.Room"),
        ("local", SYMBOL_KIND_ENUM, "aware_demo.default.home.RoomState"),
        (
            SYMBOL_ORIGIN_EXTERNAL,
            SYMBOL_KIND_CLASS,
            "aware_external.default.sensor.Sensor",
        ),
    }
    assert [probe.status for probe in evidence.resolution_probes] == [
        PROBE_STATUS_RESOLVED,
        PROBE_STATUS_RESOLVED,
        PROBE_STATUS_RESOLVED,
    ]
    assert [probe.resolved_fqn for probe in evidence.resolution_probes] == [
        "aware_demo.default.home.Room",
        "aware_demo.default.home.RoomState",
        "aware_external.default.sensor.Sensor",
    ]


def test_semantic_scope_closure_blocks_unresolved_required_probe() -> None:
    code_id = provider_delta_uuid("semantic-scope-blocked-code")

    evidence = build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            code_id: NamespacePath(
                package="other_pkg",
                namespace="home",
            ),
        },
        probes=(
            MetaOcgSemanticScopeResolutionProbeRequest(
                code_id=code_id,
                symbol_kind=SYMBOL_KIND_CLASS,
                identifier="Missing",
            ),
        ),
    )

    assert evidence.status == SCOPE_STATUS_BLOCKED
    assert not evidence.ready
    assert evidence.resolution_probes[0].status == PROBE_STATUS_UNRESOLVED
    assert any(
        blocker.startswith("namespace_package_mismatch:")
        for blocker in evidence.blockers
    )
    assert any(
        blocker.startswith("resolution_probe_unresolved:class:")
        for blocker in evidence.blockers
    )


def test_semantic_scope_closure_payload_is_stable() -> None:
    code_id = provider_delta_uuid("semantic-scope-payload-code")
    room_class = _class_config(
        key="semantic-scope-payload-room",
        class_fqn="aware_demo.default.home.Room",
        name="Room",
    )

    evidence = build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            code_id: NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        class_configs=(room_class,),
        probes=(
            MetaOcgSemanticScopeResolutionProbeRequest(
                code_id=code_id,
                symbol_kind=SYMBOL_KIND_CLASS,
                identifier="Room",
            ),
        ),
    )
    payload = evidence.evidence_payload()

    assert payload["contract_version"] == (
        META_OCG_SEMANTIC_SCOPE_CLOSURE_CONTRACT_VERSION
    )
    assert payload["status"] == SCOPE_STATUS_READY
    assert payload["namespace_prefixes"] == ("aware_demo.default.home",)
    assert payload["local_symbol_count"] == 1
    assert payload["external_symbol_count"] == 0
    assert payload["blockers"] == ()
    assert payload["symbols"] == (
        {
            "symbol_kind": SYMBOL_KIND_CLASS,
            "fqn": "aware_demo.default.home.Room",
            "object_id": str(room_class.id),
            "origin": "local",
            "package": "aware_demo",
            "domain": "default",
            "schema": "home",
            "name": "Room",
        },
    )
    assert payload["resolution_probes"] == (
        {
            "status": PROBE_STATUS_RESOLVED,
            "symbol_kind": SYMBOL_KIND_CLASS,
            "identifier": "Room",
            "code_id": str(code_id),
            "namespace_prefix": "aware_demo.default.home",
            "resolved_fqn": "aware_demo.default.home.Room",
            "resolved_object_id": str(room_class.id),
            "reason": None,
            "blockers": (),
        },
    )


def test_semantic_scope_closure_enum_gate_blocks_missing_enum_fqn() -> None:
    evidence = build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("semantic-scope-enum-gate-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        enum_configs=(
            _enum_config(
                key="semantic-scope-enum-gate-other",
                enum_fqn="aware_demo.default.home.OtherState",
                name="OtherState",
            ),
        ),
    )

    gate = meta_ocg_enum_fqn_scope_closure_gate(
        package_fqn_prefix="aware_demo",
        enum_fqn="aware_demo.default.home.RoomState",
        semantic_scope_closure=evidence,
    )

    assert gate["gate_kind"] == "meta_ocg_enum_fqn_scope_closure_gate"
    assert gate["status"] == "semantic_scope_closure_gate_blocked"
    assert gate["ready"] is False
    assert gate["target_symbol_kind"] == SYMBOL_KIND_ENUM
    assert gate["target_fqn"] == "aware_demo.default.home.RoomState"
    assert gate["blockers"] == (
        "semantic_scope_closure_missing_enum_fqn:" "aware_demo.default.home.RoomState",
    )


def _class_config(*, key: str, class_fqn: str, name: str) -> ClassConfig:
    return ClassConfig(
        id=provider_delta_uuid(key),
        class_fqn=class_fqn,
        name=name,
    )


def _enum_config(*, key: str, enum_fqn: str, name: str) -> EnumConfig:
    return EnumConfig(
        id=provider_delta_uuid(key),
        enum_fqn=enum_fqn,
        name=name,
    )


def _external_graph() -> ObjectConfigGraph:
    graph_id = provider_delta_uuid("semantic-scope-external-graph")
    sensor_class = _class_config(
        key="semantic-scope-external-sensor",
        class_fqn="aware_external.default.sensor.Sensor",
        name="Sensor",
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="External Sensor Graph",
        hash="sha256:test:semantic-scope-external",
        fqn_prefix="aware_external",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            _ocg_node(
                object_config_graph_id=graph_id,
                node_key=sensor_class.class_fqn,
                class_config=sensor_class,
            )
        ],
    )


def _ocg_node(
    *,
    object_config_graph_id: UUID,
    node_key: str,
    class_config: ClassConfig,
) -> ObjectConfigGraphNode:
    return ObjectConfigGraphNode(
        object_config_graph_id=object_config_graph_id,
        type=ObjectConfigGraphNodeType.class_,
        node_key=node_key,
        class_config=class_config,
    )
