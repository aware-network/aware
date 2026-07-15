from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import cast

import pytest

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.handlers.impl.class_ import class_config as class_config_handler
from aware_meta.materialization.deltas.semantic_scope_closure import (
    build_meta_ocg_semantic_scope_closure,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
)
from aware_meta_ontology.class_.class_config import ClassConfig

from .fixtures import provider_delta_uuid


def test_class_inheritance_augment_emits_parent_update_typed_operation() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Child"
    parent_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Parent"
    class_config_id = str(provider_delta_uuid("class-parent-update-child"))
    parent_class_id = str(provider_delta_uuid("class-parent-update-parent"))

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_parent_update_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    class_semantic_key=class_semantic_key,
                    parent_semantic_key=parent_semantic_key,
                    class_config_id=class_config_id,
                    parent_class_id=parent_class_id,
                    semantic_scope_closure=_class_scope_closure(
                        class_fqns=(
                            ("aware_demo.home.Child", "Child"),
                            ("aware_demo.home.Parent", "Parent"),
                        ),
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    operations = cast(Sequence[Mapping[str, object]], typed_plan["typed_operations"])
    current = _mapping(operations[0]["current"])
    parent_gate = _mapping(current["parent_semantic_scope_closure_gate"])
    closure_gates = cast(
        Sequence[Mapping[str, object]],
        current["semantic_scope_closure_gates"],
    )
    handler_results = cast(
        Sequence[Mapping[str, object]],
        ontology_plan["operation_handler_results"],
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert typed_plan["typed_operation_count"] == 1
    assert operations[0]["operation_family"] == "update"
    assert operations[0]["provider_operation_type"] == ("meta_ocg.class.parent.update")
    assert operations[0]["operation_key"] == (
        f"meta_ocg.class.parent.update:{class_semantic_key}"
    )
    assert current["class_config_id"] == class_config_id
    assert current["parent_class_id"] == parent_class_id
    assert current["parent_class_fqn"] == "aware_demo.home.Parent"
    assert current["parent_class_semantic_key"] == parent_semantic_key
    assert current["previous_parent_class_id"] is None
    assert current["semantic_scope_closure_consumed"] is True
    assert current["semantic_scope_closure_ready"] is True
    assert current["semantic_scope_closure_blockers"] == ()
    assert current["semantic_scope_closure_hash"]
    assert current["semantic_scope_closure_ref_keys"]
    assert len(closure_gates) == 2
    assert parent_gate["target_fqn"] == "aware_demo.home.Parent"
    assert parent_gate["status"] == "semantic_scope_closure_gate_ready"

    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    assert handler_results[0]["reason"] == (
        "meta_ocg_class_parent_update_function_call_ready"
    )
    invocation_intents = cast(
        Sequence[Mapping[str, object]],
        ontology_plan["invocation_intents"],
    )
    parent_update_intent = invocation_intents[0]
    assert parent_update_intent["owner_class_name"] == "ClassConfig"
    assert parent_update_intent["function_name"] == "update_parent_class"
    assert parent_update_intent["function_ref"] == (
        "aware_meta_ontology.class_.class_config." "ClassConfig.update_parent_class"
    )
    assert parent_update_intent["target_object_id"] == class_config_id
    assert parent_update_intent["receiver_semantic_key"] == class_semantic_key
    assert parent_update_intent["expected_result_object_id"] == class_config_id
    assert _mapping(parent_update_intent["kwargs"]) == {
        "parent_class_config_id": parent_class_id,
    }


def test_class_inheritance_augment_blocks_when_parent_closure_is_missing() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Child"

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_parent_update_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    class_semantic_key=class_semantic_key,
                    parent_semantic_key=(
                        f"{graph_semantic_key}/node:aware_demo.home.Parent"
                    ),
                    class_config_id=str(
                        provider_delta_uuid("class-parent-update-missing-child")
                    ),
                    parent_class_id=str(
                        provider_delta_uuid("class-parent-update-missing-parent")
                    ),
                    semantic_scope_closure=_class_scope_closure(
                        class_fqns=(("aware_demo.home.Child", "Child"),),
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    blockers = cast(tuple[str, ...], typed_plan["typed_operation_entry_blockers"])
    blocked_operations = cast(
        Sequence[Mapping[str, object]],
        typed_plan["blocked_operations"],
    )
    blocked_current = _mapping(blocked_operations[0]["current"])

    assert typed_plan["status"] == "typed_operation_plan_blocked"
    assert typed_plan["typed_operation_count"] == 0
    assert "semantic_scope_closure_missing_class_fqn:aware_demo.home.Parent" in blockers
    assert blocked_operations[0]["provider_operation_type"] == (
        "meta_ocg.class.parent.update"
    )
    assert blocked_current["semantic_scope_closure_ready"] is False
    assert blocked_current["parent_class_fqn"] == "aware_demo.home.Parent"


def test_class_inheritance_augment_blocks_when_parent_id_is_missing() -> None:
    graph_semantic_key = "ocg:aware_demo"
    class_semantic_key = f"{graph_semantic_key}/node:aware_demo.home.Child"

    typed_plan = _provider_delta_typed_operation_plan(
        semantic_dirty_diff=_semantic_dirty_diff(
            entries=(
                _class_parent_update_dirty_entry(
                    graph_semantic_key=graph_semantic_key,
                    class_semantic_key=class_semantic_key,
                    parent_semantic_key=(
                        f"{graph_semantic_key}/node:aware_demo.home.Parent"
                    ),
                    class_config_id=str(
                        provider_delta_uuid("class-parent-update-no-id-child")
                    ),
                    parent_class_id=None,
                    semantic_scope_closure=_class_scope_closure(
                        class_fqns=(
                            ("aware_demo.home.Child", "Child"),
                            ("aware_demo.home.Parent", "Parent"),
                        ),
                    ),
                ),
            ),
        ),
        provider_delta_head_move_plan=_ready_head_move_plan(),
        semantic_change_payloads=(),
        function_call_plans=(),
    )
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    handler_results = cast(
        Sequence[Mapping[str, object]],
        ontology_plan["operation_handler_results"],
    )

    assert typed_plan["status"] == "typed_operation_plan_ready"
    assert ontology_plan["status"] == "ontology_execution_plan_blocked"
    assert handler_results[0]["reason"] == (
        "meta_ocg_class_parent_update_requires_parent_identity"
    )
    assert handler_results[0]["blockers"] == ("missing_parent_class_config_id",)


@pytest.mark.asyncio
async def test_class_update_parent_handler_mutates_only_receiver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    child_id = provider_delta_uuid("class-parent-update-handler-child")
    parent_id = provider_delta_uuid("class-parent-update-handler-parent")
    parent = ClassConfig(
        id=parent_id,
        class_fqn="aware_demo.home.Parent",
        name="Parent",
    )
    child = ClassConfig(
        id=child_id,
        class_fqn="aware_demo.home.Child",
        name="Child",
    )
    monkeypatch.setattr(
        class_config_handler,
        "current_handler_session",
        lambda: _HandlerSession(parent),
    )

    await class_config_handler.update_parent_class(
        child,
        parent_class_config_id=parent_id,
    )

    assert child.parent_class_id == parent_id
    assert child.parent_class is parent
    assert child.class_fqn == "aware_demo.home.Child"
    assert child.name == "Child"

    await class_config_handler.update_parent_class(child, parent_class_config_id=None)

    assert child.parent_class_id is None
    assert child.parent_class is None


def _semantic_dirty_diff(
    *,
    entries: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "current_delta_fingerprint": "sha256:class-inheritance-augment",
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "baseline_index_compare_reason": (
            "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        ),
        "semantic_dirty_entries": entries,
    }


def _class_parent_update_dirty_entry(
    *,
    graph_semantic_key: str,
    class_semantic_key: str,
    parent_semantic_key: str,
    class_config_id: str,
    parent_class_id: str | None,
    semantic_scope_closure: Mapping[str, object],
) -> dict[str, object]:
    return {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta:1:{class_semantic_key}",
        "semantic_key": class_semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta:{class_semantic_key}",
        "source_refs": ("aware/home/model.aware",),
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "dirty_operation": "class_update",
        "baseline_compare_status": "baseline_object_changed",
        "baseline_compare_operation": "update",
        "baseline_object_matched": True,
        "baseline_object_id": class_config_id,
        "baseline_object_kind": "class",
        "graph_semantic_key": graph_semantic_key,
        "node_id": str(provider_delta_uuid("class-parent-update-node")),
        "node_key": "aware_demo.home.Child",
        "node_type": "class",
        "entity_id": class_config_id,
        "entity_name": "Child",
        "class_fqn": "aware_demo.home.Child",
        "name": "Child",
        "parent_class_id": parent_class_id,
        "parent_class_fqn": "aware_demo.home.Parent",
        "parent_class_semantic_key": parent_semantic_key,
        "semantic_scope_closure": dict(semantic_scope_closure),
        "payload": {
            "graph_semantic_key": graph_semantic_key,
            "node_key": "aware_demo.home.Child",
            "entity_id": class_config_id,
            "entity_name": "Child",
            "class_fqn": "aware_demo.home.Child",
            "parent_class_id": parent_class_id,
            "parent_class_fqn": "aware_demo.home.Parent",
            "parent_class_semantic_key": parent_semantic_key,
        },
        "baseline_object": {
            "semantic_key": class_semantic_key,
            "object_kind": "class",
            "object_id": class_config_id,
            "entity_id": class_config_id,
            "class_config_id": class_config_id,
            "node_key": "aware_demo.home.Child",
            "class_fqn": "aware_demo.home.Child",
            "name": "Child",
            "parent_class_id": None,
            "parent_class_fqn": None,
            "parent_class_semantic_key": None,
            "payload": {
                "entity_id": class_config_id,
                "class_fqn": "aware_demo.home.Child",
                "name": "Child",
                "parent_class_id": None,
                "parent_class_fqn": None,
                "parent_class_semantic_key": None,
            },
        },
    }


def _ready_head_move_plan() -> dict[str, object]:
    return {
        "status": "head_move_plan_ready",
        "reason": "provider_delta_head_move_plan_ready",
        "blocked": False,
    }


def _class_scope_closure(
    *,
    class_fqns: tuple[tuple[str, str], ...],
) -> Mapping[str, object]:
    class_configs = tuple(
        ClassConfig(
            id=provider_delta_uuid(f"class-inheritance-closure:{class_fqn}"),
            class_fqn=class_fqn,
            name=class_name,
        )
        for class_fqn, class_name in class_fqns
    )
    return build_meta_ocg_semantic_scope_closure(
        package_fqn_prefix="aware_demo",
        namespace_by_code_id={
            provider_delta_uuid("class-inheritance-scope-code"): NamespacePath(
                package="aware_demo",
                namespace="home",
            ),
        },
        class_configs=class_configs,
    ).evidence_payload()


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))


class _HandlerSession:
    def __init__(self, *objects: object) -> None:
        self._objects = {
            getattr(item, "id"): item
            for item in objects
            if getattr(item, "id", None) is not None
        }

    def imap_get(self, _model: type[object], object_id: object) -> object | None:
        return self._objects.get(object_id)
