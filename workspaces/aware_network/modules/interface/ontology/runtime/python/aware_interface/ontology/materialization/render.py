from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast
from uuid import UUID, uuid5

from aware_interface.builder import (
    _canonical_json_sha256,
    _validate_pane_render_spec_materialization_commit,
)
from aware_interface.lifecycle import InterfaceRuntimePaneRenderSpecState
from aware_interface_ontology.render.pane_action_binding import PaneActionBinding
from aware_interface_ontology.render.pane_input_binding import PaneInputBinding
from aware_interface_ontology.render.pane_render_enums import (
    PaneActionEvent,
    PaneRenderCapabilityKind,
    PaneRenderNodeKind,
    PaneRenderSemanticRole,
    PaneStateBindingTargetProperty,
    PaneStateBindingTransform,
)
from aware_interface_ontology.render.pane_render_node import PaneRenderNode
from aware_interface_ontology.render.pane_render_spec import PaneRenderSpec
from aware_interface_ontology.render.pane_renderer_capability_requirement import (
    PaneRendererCapabilityRequirement,
)
from aware_interface_ontology.render.pane_state_binding import PaneStateBinding
from aware_interface_ontology.render.pane_style_token_ref import PaneStyleTokenRef
from aware_interface.materialization.snapshot_commit import (
    commit_pane_render_spec_snapshot,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime import (
    MetaGraphBoundRuntimeLane,
    MetaGraphRuntimeIndexSnapshot,
    find_meta_graph_projection_hash_by_name,
    reify_meta_orm_root_from_oig_commit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_orm.models.base_model import BaseORMModel

_TRoot = TypeVar("_TRoot", bound=PaneRenderSpec)


class _RuntimeProtocol(Protocol):
    def bind(
        self,
        *,
        environment_id: UUID,
        process_id: UUID,
        thread_id: UUID,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> MetaGraphBoundRuntimeLane: ...


@dataclass(frozen=True, slots=True)
class MaterializedPaneRenderSpec:
    source_path: str
    source_kind: str
    render_spec_content_hash_sha256: str
    pane_render_spec: PaneRenderSpec
    branch_id: UUID | None = None
    last_commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PaneRenderSpecRuntimePayload:
    source_kind: str
    pane_render_spec_id: UUID
    pane_config_id: UUID
    render_spec_content_hash_sha256: str
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class PaneRenderSpecMaterializationResult:
    materialization_path: Path
    materialization_commit_id: UUID
    materialization_content_hash_sha256: str
    branch_id: UUID
    projection_hash: str
    pane_render_specs: tuple[MaterializedPaneRenderSpec, ...]
    runtime_payloads: tuple[PaneRenderSpecRuntimePayload, ...]
    last_commit_id: UUID | None
    last_head_commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None


async def materialize_pane_render_specs_from_materialization_artifact(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndexSnapshot,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    materialization_path: Path,
    branch_id: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
    prefer_snapshot_materialization: bool = False,
) -> PaneRenderSpecMaterializationResult:
    payload = _load_materialization_payload(materialization_path=materialization_path)
    rows = _render_spec_rows(payload=payload)
    materialization_commit_id = UUID(_required_string(payload, "materialization_commit_id"))
    effective_branch_id = branch_id or materialization_commit_id
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="PaneRenderSpec",
    )
    materialized: list[MaterializedPaneRenderSpec] = []
    runtime_payloads: list[PaneRenderSpecRuntimePayload] = []
    last_commit_id: UUID | None = None
    last_head_commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    for row in rows:
        render_payload = _row_payload(row)
        render_spec_id = UUID(_required_string(render_payload, "spec_id"))
        row_branch_id = _row_branch_id(
            materialization_branch_id=effective_branch_id,
            render_spec_id=render_spec_id,
            render_spec_count=len(rows),
        )
        if prefer_snapshot_materialization or not hasattr(runtime, "bind"):
            pane_render_spec, objects_by_id = _build_pane_render_spec_snapshot_objects(row=row)
            _expect_uuid(
                actual=pane_render_spec.id,
                expected=render_spec_id,
                label="PaneRenderSpec.id",
            )
            snapshot_commit = await commit_pane_render_spec_snapshot(
                index=cast(Any, index),
                actor_id=actor_id,
                branch_id=row_branch_id,
                projection_hash=projection_hash,
                pane_render_spec=pane_render_spec,
                objects_by_id=objects_by_id,
            )
            last_commit_id = snapshot_commit.commit_id
            last_head_commit_id = snapshot_commit.head_commit_id
            object_instance_graph_commit_id = snapshot_commit.object_instance_graph_commit_id
            materialized.append(
                MaterializedPaneRenderSpec(
                    source_path=_required_string(row, "source_path"),
                    source_kind=_required_string(row, "source_kind"),
                    render_spec_content_hash_sha256=_required_string(
                        row,
                        "render_spec_content_hash_sha256",
                    ),
                    pane_render_spec=pane_render_spec,
                    branch_id=row_branch_id,
                    last_commit_id=last_commit_id,
                    object_instance_graph_commit_id=object_instance_graph_commit_id,
                )
            )
            runtime_payloads.append(
                pane_render_spec_to_runtime_payload(
                    pane_render_spec=pane_render_spec,
                    pane_kind=_required_string(row, "pane_kind"),
                    pane_name=_required_string(row, "pane_name"),
                    source_kind="materialized_oig",
                )
            )
            continue
        render_lane = await _bind_materialization_runtime_lane(
            runtime=runtime,
            index=index,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=row_branch_id,
            projection=projection_hash,
            actor_id=actor_id,
        )
        with render_lane.activate(commit=commit, publish=publish):
            render_payload = _row_payload(row)
            semantic_object_ids = _semantic_object_ids(row=row)
            pane_render_spec = await PaneRenderSpec.create(
                pane_config_id=UUID(_required_string(render_payload, "pane_config_id")),
                name=_required_string(render_payload, "name"),
                spec_version=_required_string(render_payload, "spec_version"),
                root_node_key=_required_string(render_payload, "root_node_key"),
                view_ref=_optional_string(render_payload, "view_ref"),
                projection_view_key=_optional_string(render_payload, "projection_view_key"),
                state_model_id=_optional_uuid(render_payload, "state_model_id"),
                description=_optional_string(render_payload, "description"),
            )
            _expect_uuid(
                actual=pane_render_spec.id,
                expected=UUID(str(semantic_object_ids["pane_render_spec_id"])),
                label="PaneRenderSpec.id",
            )
            await _materialize_nodes(
                pane_render_spec=pane_render_spec,
                render_payload=render_payload,
                semantic_object_ids=semantic_object_ids,
            )
            await _materialize_renderer_requirements(
                pane_render_spec=pane_render_spec,
                render_payload=render_payload,
                semantic_object_ids=semantic_object_ids,
            )
            materialized.append(
                MaterializedPaneRenderSpec(
                    source_path=_required_string(row, "source_path"),
                    source_kind=_required_string(row, "source_kind"),
                    render_spec_content_hash_sha256=_required_string(
                        row,
                        "render_spec_content_hash_sha256",
                    ),
                    pane_render_spec=pane_render_spec,
                    branch_id=row_branch_id,
                    last_commit_id=last_commit_id,
                    object_instance_graph_commit_id=(object_instance_graph_commit_id),
                )
            )
            runtime_payloads.append(
                pane_render_spec_to_runtime_payload(
                    pane_render_spec=pane_render_spec,
                    pane_kind=_required_string(row, "pane_kind"),
                    pane_name=_required_string(row, "pane_name"),
                    source_kind="materialized_oig",
                )
            )
        last_commit_id = render_lane.last_commit_id or await _lane_head_commit_id(
            branch_id=row_branch_id,
            projection_hash=projection_hash,
        )
        last_head_commit_id = await _lane_head_commit_id(
            branch_id=row_branch_id,
            projection_hash=projection_hash,
        )
        object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=row_branch_id,
                projection_hash=projection_hash,
                domain_commit_id=last_commit_id,
            )
            if last_commit_id is not None
            else None
        )
        materialized[-1] = MaterializedPaneRenderSpec(
            source_path=materialized[-1].source_path,
            source_kind=materialized[-1].source_kind,
            render_spec_content_hash_sha256=(materialized[-1].render_spec_content_hash_sha256),
            pane_render_spec=materialized[-1].pane_render_spec,
            branch_id=row_branch_id,
            last_commit_id=last_commit_id,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )

    return PaneRenderSpecMaterializationResult(
        materialization_path=materialization_path.resolve(),
        materialization_commit_id=materialization_commit_id,
        materialization_content_hash_sha256=_required_string(
            payload,
            "materialization_content_hash_sha256",
        ),
        branch_id=effective_branch_id,
        projection_hash=projection_hash,
        pane_render_specs=tuple(materialized),
        runtime_payloads=tuple(runtime_payloads),
        last_commit_id=last_commit_id,
        last_head_commit_id=last_head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )


async def load_pane_render_spec_runtime_payloads_from_oig_head(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    pane_render_spec_ids: Iterable[UUID],
    pane_kind_by_pane_config_id: Mapping[UUID | str, str],
    pane_name_by_pane_config_id: Mapping[UUID | str, str] | None = None,
    projection_hash: str | None = None,
) -> tuple[PaneRenderSpecRuntimePayload, ...]:
    resolved_projection_hash = projection_hash or find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="PaneRenderSpec",
    )
    pane_kind_by_binding_id = _normalize_uuid_string_map(
        pane_kind_by_pane_config_id,
        label="pane_kind_by_pane_config_id",
    )
    pane_name_by_binding_id = _normalize_uuid_string_map(
        pane_name_by_pane_config_id or {},
        label="pane_name_by_pane_config_id",
    )

    payloads: list[PaneRenderSpecRuntimePayload] = []
    for pane_render_spec_id in pane_render_spec_ids:
        pane_render_spec = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=resolved_projection_hash,
            root_id=pane_render_spec_id,
            root_type=PaneRenderSpec,
        )
        if pane_render_spec is None:
            raise RuntimeError(
                "Committed PaneRenderSpec root not found in pane_render_spec lane: "
                + f"branch_id={branch_id} projection_hash={resolved_projection_hash} "
                + f"pane_render_spec_id={pane_render_spec_id}"
            )
        binding_id = pane_render_spec.pane_config_id
        pane_kind = pane_kind_by_binding_id.get(binding_id)
        if pane_kind is None:
            raise RuntimeError(
                "Committed PaneRenderSpec runtime projection requires pane kind "
                + "from Interface config metadata: "
                + f"pane_config_id={binding_id}"
            )
        payloads.append(
            pane_render_spec_to_runtime_payload(
                pane_render_spec=pane_render_spec,
                pane_kind=pane_kind,
                pane_name=pane_name_by_binding_id.get(binding_id),
                source_kind="committed_oig",
            )
        )
    return tuple(
        sorted(
            payloads,
            key=lambda item: (
                str(item.payload.get("pane_kind") or "").casefold(),
                str(item.payload.get("view_ref") or "").casefold(),
                str(item.payload.get("name") or "").casefold(),
                str(item.pane_render_spec_id),
            ),
        )
    )


async def load_pane_render_spec_runtime_states_from_materialization_artifact_oig(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    materialization_path: Path,
    pane_kind_by_pane_config_id: Mapping[UUID | str, str],
    pane_name_by_pane_config_id: Mapping[UUID | str, str] | None = None,
) -> tuple[InterfaceRuntimePaneRenderSpecState, ...]:
    payload = _load_materialization_payload(materialization_path=materialization_path)
    materialization_branch_id = UUID(_required_string(payload, "materialization_commit_id"))
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="PaneRenderSpec",
    )
    rows = _render_spec_rows(payload=payload)
    if not rows:
        return ()
    states: list[InterfaceRuntimePaneRenderSpecState] = []
    for row in rows:
        render_spec_id = UUID(_required_string(_row_payload(row), "spec_id"))
        row_branch_id = _row_branch_id(
            materialization_branch_id=materialization_branch_id,
            render_spec_id=render_spec_id,
            render_spec_count=len(rows),
        )
        runtime_payloads = await load_pane_render_spec_runtime_payloads_from_oig_head(
            index=index,
            branch_id=row_branch_id,
            pane_render_spec_ids=(render_spec_id,),
            pane_kind_by_pane_config_id=(
                pane_kind_by_pane_config_id
            ),
            pane_name_by_pane_config_id=(
                pane_name_by_pane_config_id
            ),
            projection_hash=projection_hash,
        )
        last_commit_id = await _lane_head_commit_id(
            branch_id=row_branch_id,
            projection_hash=projection_hash,
        )
        object_instance_graph_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=row_branch_id,
                projection_hash=projection_hash,
                domain_commit_id=last_commit_id,
            )
            if last_commit_id is not None
            else None
        )
        states.extend(
            InterfaceRuntimePaneRenderSpecState(
                source_kind=runtime_payload.source_kind,
                branch_id=row_branch_id,
                projection_hash=projection_hash,
                last_commit_id=last_commit_id,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
                pane_render_spec_id=runtime_payload.pane_render_spec_id,
                pane_config_id=(runtime_payload.pane_config_id),
                render_spec_content_hash_sha256=(runtime_payload.render_spec_content_hash_sha256),
                payload=dict(runtime_payload.payload),
            )
            for runtime_payload in runtime_payloads
        )
    return tuple(states)


def pane_render_spec_to_runtime_payload(
    *,
    pane_render_spec: PaneRenderSpec,
    pane_kind: str,
    pane_name: str | None = None,
    source_kind: str = "committed_oig",
) -> PaneRenderSpecRuntimePayload:
    pane_kind_value = _required_runtime_string(pane_kind, "pane_kind")
    pane_name_value = _optional_runtime_string(pane_name)
    binding_id = pane_render_spec.pane_config_id
    if binding_id is None:
        raise RuntimeError("PaneRenderSpec runtime projection requires pane_config_id")
    if pane_render_spec.id is None:
        raise RuntimeError("PaneRenderSpec runtime projection requires committed PaneRenderSpec.id")

    payload: dict[str, object] = {
        "spec_id": str(pane_render_spec.id),
        "name": _required_runtime_string(pane_render_spec.name, "PaneRenderSpec.name"),
        "spec_version": _required_runtime_string(
            pane_render_spec.spec_version,
            "PaneRenderSpec.spec_version",
        ),
        "pane_kind": pane_kind_value,
        "pane_config_id": str(binding_id),
        "root_node_key": _required_runtime_string(
            pane_render_spec.root_node_key,
            "PaneRenderSpec.root_node_key",
        ),
        "nodes": [
            _pane_render_node_runtime_payload(node)
            for node in sorted(
                pane_render_spec.nodes,
                key=lambda item: (item.order, item.node_key),
            )
        ],
        "renderer_requirements": [
            _pane_renderer_requirement_runtime_payload(requirement)
            for requirement in sorted(
                pane_render_spec.renderer_requirements,
                key=lambda item: (
                    _enum_value(item.capability_kind),
                    item.capability_key,
                ),
            )
        ],
    }
    if pane_name_value is not None:
        payload["pane_name"] = pane_name_value
    _set_optional(payload, "view_ref", pane_render_spec.view_ref)
    _set_optional(payload, "projection_view_key", pane_render_spec.projection_view_key)
    _set_optional_uuid(payload, "state_model_id", pane_render_spec.state_model_id)
    _set_optional(payload, "description", pane_render_spec.description)

    return PaneRenderSpecRuntimePayload(
        source_kind=source_kind,
        pane_render_spec_id=pane_render_spec.id,
        pane_config_id=binding_id,
        render_spec_content_hash_sha256=_canonical_json_sha256(payload),
        payload=payload,
    )


def _build_pane_render_spec_snapshot_objects(
    *,
    row: Mapping[str, object],
) -> tuple[PaneRenderSpec, Mapping[UUID, BaseORMModel]]:
    render_payload = _row_payload(row)
    semantic_object_ids = _semantic_object_ids(row=row)
    spec_id = UUID(str(semantic_object_ids["pane_render_spec_id"]))
    pane_render_spec = PaneRenderSpec(
        id=spec_id,
        nodes=[],
        renderer_requirements=[],
        pane_config_id=UUID(_required_string(render_payload, "pane_config_id")),
        name=_required_string(render_payload, "name"),
        spec_version=_required_string(render_payload, "spec_version"),
        root_node_key=_required_string(render_payload, "root_node_key"),
        view_ref=_optional_string(render_payload, "view_ref"),
        projection_view_key=_optional_string(render_payload, "projection_view_key"),
        state_model_id=_optional_uuid(render_payload, "state_model_id"),
        description=_optional_string(render_payload, "description"),
    )
    objects_by_id: dict[UUID, BaseORMModel] = {pane_render_spec.id: pane_render_spec}
    _build_snapshot_nodes(
        pane_render_spec=pane_render_spec,
        render_payload=render_payload,
        semantic_object_ids=semantic_object_ids,
        objects_by_id=objects_by_id,
    )
    _build_snapshot_renderer_requirements(
        pane_render_spec=pane_render_spec,
        render_payload=render_payload,
        semantic_object_ids=semantic_object_ids,
        objects_by_id=objects_by_id,
    )
    return pane_render_spec, objects_by_id


def _build_snapshot_nodes(
    *,
    pane_render_spec: PaneRenderSpec,
    render_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
    objects_by_id: dict[UUID, BaseORMModel],
) -> None:
    node_ids = _semantic_id_map(semantic_object_ids, "pane_render_node_ids_by_key")
    raw_nodes = render_payload.get("nodes")
    if not isinstance(raw_nodes, list):
        raise RuntimeError("PaneRenderSpec materialization requires payload.nodes list")
    pane_render_spec.nodes = []
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            raise RuntimeError("PaneRenderSpec materialization requires node objects")
        node_payload = cast(Mapping[str, object], raw_node)
        node_key = _required_string(node_payload, "node_key")
        node = PaneRenderNode(
            id=UUID(node_ids[node_key]),
            state_bindings=[],
            action_bindings=[],
            style_tokens=[],
            pane_render_spec_id=pane_render_spec.id,
            node_key=node_key,
            node_kind=PaneRenderNodeKind(_required_string(node_payload, "node_kind")),
            semantic_role=_optional_enum(
                node_payload,
                "semantic_role",
                PaneRenderSemanticRole,
            ),
            parent_node_key=_optional_string(node_payload, "parent_node_key"),
            slot_key=_optional_string(node_payload, "slot_key"),
            order=_optional_int(node_payload, "order") or 0,
            label=_optional_string(node_payload, "label"),
            text=_optional_string(node_payload, "text"),
            placeholder=_optional_string(node_payload, "placeholder"),
            component_ref=_optional_string(node_payload, "component_ref"),
            component_contract_id=_optional_uuid(
                node_payload,
                "component_contract_id",
            ),
            fallback_node_kind=_optional_enum(
                node_payload,
                "fallback_node_kind",
                PaneRenderNodeKind,
            ),
            fallback_text=_optional_string(node_payload, "fallback_text"),
        )
        _remember_snapshot_object(objects_by_id, node)
        pane_render_spec.nodes.append(node)
        _build_snapshot_state_bindings(
            node=node,
            node_payload=node_payload,
            semantic_object_ids=semantic_object_ids,
            objects_by_id=objects_by_id,
        )
        _build_snapshot_action_bindings(
            node=node,
            node_payload=node_payload,
            semantic_object_ids=semantic_object_ids,
            objects_by_id=objects_by_id,
        )
        _build_snapshot_style_tokens(
            node=node,
            node_payload=node_payload,
            semantic_object_ids=semantic_object_ids,
            objects_by_id=objects_by_id,
        )


def _build_snapshot_state_bindings(
    *,
    node: PaneRenderNode,
    node_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
    objects_by_id: dict[UUID, BaseORMModel],
) -> None:
    state_binding_ids = _semantic_id_map(semantic_object_ids, "pane_state_binding_ids_by_ref")
    node_key = _required_string(node_payload, "node_key")
    raw_bindings = node_payload.get("state_bindings")
    if raw_bindings is None:
        return
    if not isinstance(raw_bindings, list):
        raise RuntimeError(f"PaneRenderNode[{node_key}] state_bindings must be a list")
    for raw_binding in raw_bindings:
        if not isinstance(raw_binding, dict):
            raise RuntimeError(f"PaneRenderNode[{node_key}] state_bindings must contain objects")
        binding_payload = cast(Mapping[str, object], raw_binding)
        binding_key = _required_string(binding_payload, "binding_key")
        binding = PaneStateBinding(
            id=UUID(state_binding_ids[f"{node_key}.{binding_key}"]),
            pane_render_node_id=node.id,
            binding_key=binding_key,
            target_property=PaneStateBindingTargetProperty(_required_string(binding_payload, "target_property")),
            json_path=_required_string(binding_payload, "json_path"),
            state_model_id=_optional_uuid(binding_payload, "state_model_id"),
            state_attribute_config_id=_optional_uuid(
                binding_payload,
                "state_attribute_config_id",
            ),
            component_input_port_key=_optional_string(
                binding_payload,
                "component_input_port_key",
            ),
            transform=PaneStateBindingTransform(_optional_string(binding_payload, "transform") or "raw"),
            fallback_value=_optional_string(binding_payload, "fallback_value"),
        )
        _remember_snapshot_object(objects_by_id, binding)
        node.state_bindings.append(binding)


def _build_snapshot_action_bindings(
    *,
    node: PaneRenderNode,
    node_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
    objects_by_id: dict[UUID, BaseORMModel],
) -> None:
    action_binding_ids = _semantic_id_map(semantic_object_ids, "pane_action_binding_ids_by_ref")
    node_key = _required_string(node_payload, "node_key")
    raw_bindings = node_payload.get("action_bindings")
    if raw_bindings is None:
        return
    if not isinstance(raw_bindings, list):
        raise RuntimeError(f"PaneRenderNode[{node_key}] action_bindings must be a list")
    for raw_binding in raw_bindings:
        if not isinstance(raw_binding, dict):
            raise RuntimeError(f"PaneRenderNode[{node_key}] action_bindings must contain objects")
        binding_payload = cast(Mapping[str, object], raw_binding)
        binding_key = _required_string(binding_payload, "binding_key")
        binding = PaneActionBinding(
            id=UUID(action_binding_ids[f"{node_key}.{binding_key}"]),
            input_bindings=[],
            pane_render_node_id=node.id,
            binding_key=binding_key,
            event=PaneActionEvent(_optional_string(binding_payload, "event") or "activate"),
            action_key=_required_string(binding_payload, "action_key"),
            projection_experience_view_invocation_action_id=_optional_uuid(
                binding_payload,
                "projection_experience_view_invocation_action_id",
            ),
            component_action_port_key=_optional_string(
                binding_payload,
                "component_action_port_key",
            ),
            label=_optional_string(binding_payload, "label"),
            confirmation_policy=_optional_string(binding_payload, "confirmation_policy"),
            optimistic_policy=_optional_string(binding_payload, "optimistic_policy"),
            receipt_policy=_optional_string(binding_payload, "receipt_policy"),
        )
        _remember_snapshot_object(objects_by_id, binding)
        node.action_bindings.append(binding)
        _build_snapshot_input_bindings(
            binding=binding,
            node_key=node_key,
            binding_payload=binding_payload,
            semantic_object_ids=semantic_object_ids,
            objects_by_id=objects_by_id,
        )


def _build_snapshot_input_bindings(
    *,
    binding: PaneActionBinding,
    node_key: str,
    binding_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
    objects_by_id: dict[UUID, BaseORMModel],
) -> None:
    input_binding_ids = _semantic_id_map(semantic_object_ids, "pane_input_binding_ids_by_ref")
    binding_key = _required_string(binding_payload, "binding_key")
    raw_bindings = binding_payload.get("input_bindings")
    if raw_bindings is None:
        return
    if not isinstance(raw_bindings, list):
        raise RuntimeError(f"PaneActionBinding[{node_key}.{binding_key}] input_bindings must be a list")
    for raw_input in raw_bindings:
        if not isinstance(raw_input, dict):
            raise RuntimeError(f"PaneActionBinding[{node_key}.{binding_key}] input_bindings must contain objects")
        input_payload = cast(Mapping[str, object], raw_input)
        payload_path = _required_string(input_payload, "payload_path")
        input_binding = PaneInputBinding(
            id=UUID(input_binding_ids[f"{node_key}.{binding_key}.{payload_path}"]),
            pane_action_binding_id=binding.id,
            payload_path=payload_path,
            source_node_key=_optional_string(input_payload, "source_node_key"),
            source_json_path=_optional_string(input_payload, "source_json_path"),
            literal_value=_optional_string(input_payload, "literal_value"),
        )
        _remember_snapshot_object(objects_by_id, input_binding)
        binding.input_bindings.append(input_binding)


def _build_snapshot_style_tokens(
    *,
    node: PaneRenderNode,
    node_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
    objects_by_id: dict[UUID, BaseORMModel],
) -> None:
    style_token_ids = _semantic_id_map(semantic_object_ids, "pane_style_token_ref_ids_by_ref")
    node_key = _required_string(node_payload, "node_key")
    raw_tokens = node_payload.get("style_tokens")
    if raw_tokens is None:
        return
    if not isinstance(raw_tokens, list):
        raise RuntimeError(f"PaneRenderNode[{node_key}] style_tokens must be a list")
    for raw_token in raw_tokens:
        if not isinstance(raw_token, dict):
            raise RuntimeError(f"PaneRenderNode[{node_key}] style_tokens must contain objects")
        token_payload = cast(Mapping[str, object], raw_token)
        token_key = _required_string(token_payload, "token_key")
        token = PaneStyleTokenRef(
            id=UUID(style_token_ids[f"{node_key}.{token_key}"]),
            pane_render_node_id=node.id,
            token_key=token_key,
            token_value=_optional_string(token_payload, "token_value"),
        )
        _remember_snapshot_object(objects_by_id, token)
        node.style_tokens.append(token)


def _build_snapshot_renderer_requirements(
    *,
    pane_render_spec: PaneRenderSpec,
    render_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
    objects_by_id: dict[UUID, BaseORMModel],
) -> None:
    requirement_ids = _semantic_id_map(
        semantic_object_ids,
        "pane_renderer_capability_requirement_ids_by_ref",
    )
    raw_requirements = render_payload.get("renderer_requirements")
    if raw_requirements is None:
        pane_render_spec.renderer_requirements = []
        return
    if not isinstance(raw_requirements, list):
        raise RuntimeError("PaneRenderSpec renderer_requirements must be a list")
    pane_render_spec.renderer_requirements = []
    for raw_requirement in raw_requirements:
        if not isinstance(raw_requirement, dict):
            raise RuntimeError("PaneRenderSpec renderer_requirements must contain objects")
        requirement_payload = cast(Mapping[str, object], raw_requirement)
        capability_kind = _required_string(requirement_payload, "capability_kind")
        capability_key = _required_string(requirement_payload, "capability_key")
        requirement = PaneRendererCapabilityRequirement(
            id=UUID(requirement_ids[f"{capability_kind}:{capability_key}"]),
            pane_render_spec_id=pane_render_spec.id,
            capability_kind=PaneRenderCapabilityKind(capability_kind),
            capability_key=capability_key,
            is_required=_optional_bool(requirement_payload, "is_required", default=True),
        )
        _remember_snapshot_object(objects_by_id, requirement)
        pane_render_spec.renderer_requirements.append(requirement)


async def _materialize_nodes(
    *,
    pane_render_spec: PaneRenderSpec,
    render_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
) -> None:
    node_ids = _semantic_id_map(semantic_object_ids, "pane_render_node_ids_by_key")
    raw_nodes = render_payload.get("nodes")
    if not isinstance(raw_nodes, list):
        raise RuntimeError("PaneRenderSpec materialization requires payload.nodes list")
    pane_render_spec.nodes = []
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            raise RuntimeError("PaneRenderSpec materialization requires node objects")
        node_payload = cast(Mapping[str, object], raw_node)
        node_key = _required_string(node_payload, "node_key")
        node = await pane_render_spec.add_node(
            node_key=node_key,
            node_kind=PaneRenderNodeKind(_required_string(node_payload, "node_kind")),
            semantic_role=_optional_enum(
                node_payload,
                "semantic_role",
                PaneRenderSemanticRole,
            ),
            parent_node_key=_optional_string(node_payload, "parent_node_key"),
            slot_key=_optional_string(node_payload, "slot_key"),
            order=_optional_int(node_payload, "order") or 0,
            label=_optional_string(node_payload, "label"),
            text=_optional_string(node_payload, "text"),
            placeholder=_optional_string(node_payload, "placeholder"),
            component_ref=_optional_string(node_payload, "component_ref"),
            component_contract_id=_optional_uuid(
                node_payload,
                "component_contract_id",
            ),
            fallback_node_kind=_optional_enum(
                node_payload,
                "fallback_node_kind",
                PaneRenderNodeKind,
            ),
            fallback_text=_optional_string(node_payload, "fallback_text"),
        )
        _append_unique_by_id(pane_render_spec.nodes, node)
        _expect_uuid(
            actual=node.id,
            expected=UUID(node_ids[node_key]),
            label=f"PaneRenderNode[{node_key}].id",
        )
        await _materialize_state_bindings(
            node=node,
            node_payload=node_payload,
            semantic_object_ids=semantic_object_ids,
        )
        await _materialize_action_bindings(
            node=node,
            node_payload=node_payload,
            semantic_object_ids=semantic_object_ids,
        )
        await _materialize_style_tokens(
            node=node,
            node_payload=node_payload,
            semantic_object_ids=semantic_object_ids,
        )


async def _materialize_state_bindings(
    *,
    node: PaneRenderNode,
    node_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
) -> None:
    state_binding_ids = _semantic_id_map(semantic_object_ids, "pane_state_binding_ids_by_ref")
    node_key = _required_string(node_payload, "node_key")
    raw_bindings = node_payload.get("state_bindings")
    if raw_bindings is None:
        return
    if not isinstance(raw_bindings, list):
        raise RuntimeError(f"PaneRenderNode[{node_key}] state_bindings must be a list")
    for raw_binding in raw_bindings:
        if not isinstance(raw_binding, dict):
            raise RuntimeError(f"PaneRenderNode[{node_key}] state_bindings must contain objects")
        binding_payload = cast(Mapping[str, object], raw_binding)
        binding_key = _required_string(binding_payload, "binding_key")
        binding = await node.bind_state(
            binding_key=binding_key,
            target_property=PaneStateBindingTargetProperty(_required_string(binding_payload, "target_property")),
            json_path=_required_string(binding_payload, "json_path"),
            state_model_id=_optional_uuid(binding_payload, "state_model_id"),
            state_attribute_config_id=_optional_uuid(binding_payload, "state_attribute_config_id"),
            component_input_port_key=_optional_string(
                binding_payload,
                "component_input_port_key",
            ),
            transform=PaneStateBindingTransform(_optional_string(binding_payload, "transform") or "raw"),
            fallback_value=_optional_string(binding_payload, "fallback_value"),
        )
        _append_unique_by_id(node.state_bindings, binding)
        _expect_uuid(
            actual=binding.id,
            expected=UUID(state_binding_ids[f"{node_key}.{binding_key}"]),
            label=f"PaneStateBinding[{node_key}.{binding_key}].id",
        )


async def _materialize_action_bindings(
    *,
    node: PaneRenderNode,
    node_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
) -> None:
    action_binding_ids = _semantic_id_map(semantic_object_ids, "pane_action_binding_ids_by_ref")
    node_key = _required_string(node_payload, "node_key")
    raw_bindings = node_payload.get("action_bindings")
    if raw_bindings is None:
        return
    if not isinstance(raw_bindings, list):
        raise RuntimeError(f"PaneRenderNode[{node_key}] action_bindings must be a list")
    for raw_binding in raw_bindings:
        if not isinstance(raw_binding, dict):
            raise RuntimeError(f"PaneRenderNode[{node_key}] action_bindings must contain objects")
        binding_payload = cast(Mapping[str, object], raw_binding)
        binding_key = _required_string(binding_payload, "binding_key")
        binding = await node.bind_action(
            binding_key=binding_key,
            event=PaneActionEvent(_optional_string(binding_payload, "event") or "activate"),
            action_key=_required_string(binding_payload, "action_key"),
            projection_experience_view_invocation_action_id=_optional_uuid(
                binding_payload,
                "projection_experience_view_invocation_action_id",
            ),
            label=_optional_string(binding_payload, "label"),
            component_action_port_key=_optional_string(binding_payload, "component_action_port_key"),
            confirmation_policy=_optional_string(binding_payload, "confirmation_policy"),
            optimistic_policy=_optional_string(binding_payload, "optimistic_policy"),
            receipt_policy=_optional_string(binding_payload, "receipt_policy"),
        )
        _append_unique_by_id(node.action_bindings, binding)
        _expect_uuid(
            actual=binding.id,
            expected=UUID(action_binding_ids[f"{node_key}.{binding_key}"]),
            label=f"PaneActionBinding[{node_key}.{binding_key}].id",
        )
        await _materialize_input_bindings(
            binding=binding,
            node_key=node_key,
            binding_payload=binding_payload,
            semantic_object_ids=semantic_object_ids,
        )


async def _materialize_input_bindings(
    *,
    binding: PaneActionBinding,
    node_key: str,
    binding_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
) -> None:
    input_binding_ids = _semantic_id_map(semantic_object_ids, "pane_input_binding_ids_by_ref")
    binding_key = _required_string(binding_payload, "binding_key")
    raw_bindings = binding_payload.get("input_bindings")
    if raw_bindings is None:
        return
    if not isinstance(raw_bindings, list):
        raise RuntimeError(f"PaneActionBinding[{node_key}.{binding_key}] input_bindings must be a list")
    for raw_input in raw_bindings:
        if not isinstance(raw_input, dict):
            raise RuntimeError(f"PaneActionBinding[{node_key}.{binding_key}] input_bindings must contain objects")
        input_payload = cast(Mapping[str, object], raw_input)
        payload_path = _required_string(input_payload, "payload_path")
        input_binding = await binding.bind_input(
            payload_path=payload_path,
            source_node_key=_optional_string(input_payload, "source_node_key"),
            source_json_path=_optional_string(input_payload, "source_json_path"),
            literal_value=_optional_string(input_payload, "literal_value"),
        )
        _append_unique_by_id(binding.input_bindings, input_binding)
        _expect_uuid(
            actual=input_binding.id,
            expected=UUID(input_binding_ids[f"{node_key}.{binding_key}.{payload_path}"]),
            label=f"PaneInputBinding[{node_key}.{binding_key}.{payload_path}].id",
        )


async def _materialize_style_tokens(
    *,
    node: PaneRenderNode,
    node_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
) -> None:
    style_token_ids = _semantic_id_map(semantic_object_ids, "pane_style_token_ref_ids_by_ref")
    node_key = _required_string(node_payload, "node_key")
    raw_tokens = node_payload.get("style_tokens")
    if raw_tokens is None:
        return
    if not isinstance(raw_tokens, list):
        raise RuntimeError(f"PaneRenderNode[{node_key}] style_tokens must be a list")
    for raw_token in raw_tokens:
        if not isinstance(raw_token, dict):
            raise RuntimeError(f"PaneRenderNode[{node_key}] style_tokens must contain objects")
        token_payload = cast(Mapping[str, object], raw_token)
        token_key = _required_string(token_payload, "token_key")
        token = await node.add_style_token(
            token_key=token_key,
            token_value=_optional_string(token_payload, "token_value"),
        )
        _append_unique_by_id(node.style_tokens, token)
        _expect_uuid(
            actual=token.id,
            expected=UUID(style_token_ids[f"{node_key}.{token_key}"]),
            label=f"PaneStyleTokenRef[{node_key}.{token_key}].id",
        )


async def _materialize_renderer_requirements(
    *,
    pane_render_spec: PaneRenderSpec,
    render_payload: Mapping[str, object],
    semantic_object_ids: Mapping[str, object],
) -> None:
    requirement_ids = _semantic_id_map(
        semantic_object_ids,
        "pane_renderer_capability_requirement_ids_by_ref",
    )
    raw_requirements = render_payload.get("renderer_requirements")
    if raw_requirements is None:
        pane_render_spec.renderer_requirements = []
        return
    if not isinstance(raw_requirements, list):
        raise RuntimeError("PaneRenderSpec renderer_requirements must be a list")
    pane_render_spec.renderer_requirements = []
    for raw_requirement in raw_requirements:
        if not isinstance(raw_requirement, dict):
            raise RuntimeError("PaneRenderSpec renderer_requirements must contain objects")
        requirement_payload = cast(Mapping[str, object], raw_requirement)
        capability_kind = _required_string(requirement_payload, "capability_kind")
        capability_key = _required_string(requirement_payload, "capability_key")
        requirement = await pane_render_spec.require_renderer_capability(
            capability_kind=PaneRenderCapabilityKind(capability_kind),
            capability_key=capability_key,
            is_required=_optional_bool(requirement_payload, "is_required", default=True),
        )
        _append_unique_by_id(pane_render_spec.renderer_requirements, requirement)
        _expect_uuid(
            actual=requirement.id,
            expected=UUID(requirement_ids[f"{capability_kind}:{capability_key}"]),
            label=f"PaneRendererCapabilityRequirement[{capability_kind}:{capability_key}].id",
        )


def _pane_render_node_runtime_payload(node: PaneRenderNode) -> dict[str, object]:
    node_payload: dict[str, object] = {
        "node_key": _required_runtime_string(node.node_key, "PaneRenderNode.node_key"),
        "node_kind": _enum_value(node.node_kind),
        "order": node.order,
    }
    _set_optional(node_payload, "parent_node_key", node.parent_node_key)
    _set_optional(node_payload, "semantic_role", _optional_enum_value(node.semantic_role))
    _set_optional(node_payload, "slot_key", node.slot_key)
    _set_optional(node_payload, "label", node.label)
    _set_optional(node_payload, "text", node.text)
    _set_optional(node_payload, "placeholder", node.placeholder)
    state_bindings = [
        _pane_state_binding_runtime_payload(binding)
        for binding in sorted(node.state_bindings, key=lambda item: item.binding_key)
    ]
    if state_bindings:
        node_payload["state_bindings"] = state_bindings
    action_bindings = [
        _pane_action_binding_runtime_payload(binding)
        for binding in sorted(node.action_bindings, key=lambda item: item.binding_key)
    ]
    if action_bindings:
        node_payload["action_bindings"] = action_bindings
    style_tokens = [
        _pane_style_token_runtime_payload(token) for token in sorted(node.style_tokens, key=lambda item: item.token_key)
    ]
    if style_tokens:
        node_payload["style_tokens"] = style_tokens
    return node_payload


def _pane_state_binding_runtime_payload(binding: Any) -> dict[str, object]:
    payload: dict[str, object] = {
        "binding_key": _required_runtime_string(
            binding.binding_key,
            "PaneStateBinding.binding_key",
        ),
        "target_property": _enum_value(binding.target_property),
        "json_path": _required_runtime_string(
            binding.json_path,
            "PaneStateBinding.json_path",
        ),
        "transform": _enum_value(binding.transform),
    }
    _set_optional_uuid(payload, "state_model_id", binding.state_model_id)
    _set_optional_uuid(
        payload,
        "state_attribute_config_id",
        binding.state_attribute_config_id,
    )
    _set_optional(payload, "fallback_value", binding.fallback_value)
    return payload


def _pane_action_binding_runtime_payload(
    binding: PaneActionBinding,
) -> dict[str, object]:
    view_action = getattr(binding, "projection_experience_view_invocation_action", None)
    payload: dict[str, object] = {
        "binding_key": _required_runtime_string(
            binding.binding_key,
            "PaneActionBinding.binding_key",
        ),
        "event": _enum_value(binding.event),
        "action_key": _required_runtime_string(
            binding.action_key,
            "PaneActionBinding.action_key",
        ),
        "action_kind": _pane_action_kind(binding, view_action=view_action),
    }
    _set_optional_uuid(
        payload,
        "projection_experience_view_invocation_action_id",
        getattr(binding, "projection_experience_view_invocation_action_id", None),
    )
    _set_optional(payload, "view_action_key", binding.action_key)
    if view_action is not None:
        target_ref = getattr(view_action, "target_ref", None)
        action_kind = getattr(view_action, "action_kind", None)
        if action_kind != "view":
            _set_optional(payload, "target_ref", target_ref)
        if action_kind == "sdk":
            _set_optional(payload, "operation_ref", target_ref)
        elif action_kind == "api":
            _set_optional(payload, "endpoint_ref", target_ref)
    _set_optional(payload, "label", binding.label)
    _set_optional(payload, "component_action_port_key", binding.component_action_port_key)
    _set_optional(payload, "confirmation_policy", binding.confirmation_policy)
    _set_optional(payload, "optimistic_policy", binding.optimistic_policy)
    _set_optional(payload, "receipt_policy", binding.receipt_policy)
    input_bindings = [
        _pane_input_binding_runtime_payload(input_binding)
        for input_binding in sorted(binding.input_bindings, key=lambda item: item.payload_path)
    ]
    if input_bindings:
        payload["input_bindings"] = input_bindings
    return payload


def _pane_input_binding_runtime_payload(binding: Any) -> dict[str, object]:
    payload: dict[str, object] = {
        "payload_path": _required_runtime_string(
            binding.payload_path,
            "PaneInputBinding.payload_path",
        )
    }
    _set_optional(payload, "source_node_key", binding.source_node_key)
    _set_optional(payload, "source_json_path", binding.source_json_path)
    _set_optional(payload, "literal_value", binding.literal_value)
    return payload


def _pane_style_token_runtime_payload(token: Any) -> dict[str, object]:
    payload: dict[str, object] = {
        "token_key": _required_runtime_string(
            token.token_key,
            "PaneStyleTokenRef.token_key",
        )
    }
    _set_optional(payload, "token_value", token.token_value)
    return payload


def _pane_renderer_requirement_runtime_payload(requirement: Any) -> dict[str, object]:
    return {
        "capability_kind": _enum_value(requirement.capability_kind),
        "capability_key": _required_runtime_string(
            requirement.capability_key,
            "PaneRendererCapabilityRequirement.capability_key",
        ),
        "is_required": bool(requirement.is_required),
    }


def _load_materialization_payload(*, materialization_path: Path) -> Mapping[str, object]:
    path = materialization_path.resolve()
    payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    if not isinstance(payload, dict):
        raise ValueError(f"Pane render spec materialization must be a JSON object: {path}")
    rows = payload.get("render_specs")
    if not isinstance(rows, list):
        raise ValueError(f"Pane render spec materialization must declare render_specs: {path}")
    _validate_pane_render_spec_materialization_commit(
        payload=cast(Mapping[str, object], payload),
        materialization_path=path,
        rows=rows,
    )
    return cast(Mapping[str, object], payload)


def _render_spec_rows(*, payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = payload.get("render_specs")
    if not isinstance(rows, list):
        raise ValueError("Pane render spec materialization must declare render_specs")
    normalized: list[Mapping[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Pane render spec materialization render_specs rows must be objects")
        normalized.append(cast(Mapping[str, object], row))
    return tuple(normalized)


def _row_payload(row: Mapping[str, object]) -> Mapping[str, object]:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Pane render spec materialization row must declare payload")
    return cast(Mapping[str, object], payload)


def _semantic_object_ids(*, row: Mapping[str, object]) -> Mapping[str, object]:
    semantic_object_ids = row.get("semantic_object_ids")
    if not isinstance(semantic_object_ids, dict):
        raise ValueError("Pane render spec materialization row must declare semantic_object_ids")
    return cast(Mapping[str, object], semantic_object_ids)


def _semantic_id_map(payload: Mapping[str, object], key: str) -> Mapping[str, str]:
    raw = payload.get(key)
    if not isinstance(raw, dict):
        raise ValueError(f"Pane render spec materialization semantic_object_ids.{key} must be an object")
    return {
        str(item_key): _coerce_uuid_string(item_value, key=f"{key}.{item_key}") for item_key, item_value in raw.items()
    }


def _required_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    raise ValueError(f"Pane render spec materialization requires non-empty {key!r}")


def _optional_string(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _optional_bool(payload: Mapping[str, object], key: str, *, default: bool) -> bool:
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    return default


def _optional_uuid(payload: Mapping[str, object], key: str) -> UUID | None:
    value = _optional_string(payload, key)
    return UUID(value) if value is not None else None


def _optional_enum(payload: Mapping[str, object], key: str, enum_type: type[Any]) -> Any | None:
    value = _optional_string(payload, key)
    return enum_type(value) if value is not None else None


def _coerce_uuid_string(value: object, *, key: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Pane render spec materialization {key} must be a UUID string")
    return str(UUID(value))


def _expect_uuid(*, actual: UUID | None, expected: UUID, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} mismatch: expected={expected} actual={actual}")


def _normalize_uuid_string_map(
    payload: Mapping[UUID | str, str],
    *,
    label: str,
) -> dict[UUID, str]:
    normalized: dict[UUID, str] = {}
    for raw_key, raw_value in payload.items():
        value = _optional_runtime_string(raw_value)
        if value is None:
            raise ValueError(f"{label}[{raw_key!r}] must be a non-empty string")
        normalized[UUID(str(raw_key))] = value
    return normalized


def _set_optional(payload: dict[str, object], key: str, value: object) -> None:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            payload[key] = normalized
    elif value is not None:
        payload[key] = value


def _set_optional_uuid(payload: dict[str, object], key: str, value: UUID | None) -> None:
    if value is not None:
        payload[key] = str(value)


def _required_runtime_string(value: object, label: str) -> str:
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    raise ValueError(f"{label} must be a non-empty string")


def _optional_runtime_string(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None


def _enum_value(value: Any) -> str:
    enum_value = getattr(value, "value", value)
    return _required_runtime_string(enum_value, f"{type(value).__name__}.value")


def _optional_enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return _enum_value(value)


def _pane_action_kind(binding: PaneActionBinding, *, view_action: object | None) -> str:
    if view_action is not None:
        action_kind = _required_runtime_string(
            getattr(view_action, "action_kind", None),
            "ProjectionExperienceViewInvocationAction.action_kind",
        )
        if action_kind == "view":
            return "view_action"
        return action_kind
    if getattr(binding, "projection_experience_view_invocation_action_id", None) is not None:
        return "view_action"
    return "action"


def _append_unique_by_id(items: list[Any], item: Any) -> None:
    item_id = getattr(item, "id", None)
    if item_id is not None:
        for existing in items:
            if getattr(existing, "id", None) == item_id:
                return
    if item not in items:
        items.append(item)


def _remember_snapshot_object(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: BaseORMModel,
) -> None:
    obj_id = obj.id
    if obj_id in objects_by_id and objects_by_id[obj_id] is not obj:
        raise RuntimeError(
            "PaneRenderSpec snapshot duplicate object id: " f"object_id={obj_id} class={type(obj).__name__}"
        )
    objects_by_id[obj_id] = obj


def _row_branch_id(
    *,
    materialization_branch_id: UUID,
    render_spec_id: UUID,
    render_spec_count: int,
) -> UUID:
    if render_spec_count <= 1:
        return materialization_branch_id
    return uuid5(
        materialization_branch_id,
        f"pane-render-spec:{render_spec_id}",
    )


async def _lane_head_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> UUID | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None
    return UUID(str(head["commit_id"]))


async def _object_instance_graph_commit_id_from_domain_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
) -> UUID | None:
    domain_commit = await FSCommitStore().get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    if domain_commit is None:
        return None
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=domain_commit.object_instance_graph_identity_id,
        commit_id=domain_commit_id,
    )


async def _hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot | None:
    head_commit_id = await _lane_head_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head_commit_id is None:
        return None

    return await reify_meta_orm_root_from_oig_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=getattr(root_type, "__name__", ""),
        commit_id=head_commit_id,
        root_id=root_id,
        root_type=root_type,
        commit_store=FSCommitStore(),
        snapshot_store=FSSnapshotStore(),
    )


async def _bind_materialization_runtime_lane(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndexSnapshot,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
    projection: str,
    actor_id: UUID | None,
) -> Any:
    del index
    runtime_bind = getattr(runtime, "bind", None)
    if callable(runtime_bind):
        lane = runtime_bind(
            branch_id=branch_id,
            projection=projection,
            actor_id=actor_id,
            context=getattr(runtime, "context", None),
        )
        if inspect.isawaitable(lane):
            lane = await lane
        if hasattr(lane, "activate"):
            return lane

    raise RuntimeError("Pane render spec materialization requires a Meta runtime with bind(...).")


__all__ = [
    "MaterializedPaneRenderSpec",
    "PaneRenderSpecRuntimePayload",
    "PaneRenderSpecMaterializationResult",
    "load_pane_render_spec_runtime_payloads_from_oig_head",
    "load_pane_render_spec_runtime_states_from_materialization_artifact_oig",
    "materialize_pane_render_specs_from_materialization_artifact",
    "pane_render_spec_to_runtime_payload",
]
