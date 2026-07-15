from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar
from uuid import UUID

from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.interface.interface_config_pane_config import (
    InterfaceConfigPaneConfig,
)
from aware_interface_ontology.interface.interface_config_pane_config_section_config import (
    InterfaceConfigPaneConfigSectionConfig,
)
from aware_interface_ontology.interface.interface_config_window_config import (
    InterfaceConfigWindowConfig,
)
from aware_interface_ontology.interface.pane_config import PaneConfig
from aware_interface_ontology.interface.window_config import WindowConfig
from aware_interface_ontology.interface.window_config_layout_config import (
    WindowConfigLayoutConfig,
)
from aware_interface_ontology.stable_ids import (
    stable_interface_config_pane_config_id,
    stable_interface_config_window_config_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime import (
    MetaGraphBoundRuntimeLane,
    MetaGraphRuntimeIndexSnapshot,
    find_meta_graph_projection_hash_by_name,
    reify_meta_orm_root_from_oig_commit,
)

from aware_interface.materialization.snapshot_commit import (
    commit_interface_config_snapshot,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)

_TRoot = TypeVar(
    "_TRoot",
    InterfaceConfig,
    WindowConfig,
    PaneConfig,
)


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
class InterfaceConfigMaterializationResult:
    bundle: InterfaceConfigBundle
    interface_config: InterfaceConfig
    window_configs: tuple[WindowConfig, ...]
    interface_config_window_configs: tuple[InterfaceConfigWindowConfig, ...]
    window_config_layout_configs: tuple[WindowConfigLayoutConfig, ...]
    pane_configs: tuple[PaneConfig, ...]
    interface_config_pane_configs: tuple[InterfaceConfigPaneConfig, ...]
    projection_experience_view_bindings: tuple[PaneConfig, ...]
    section_mounts: tuple[InterfaceConfigPaneConfigSectionConfig, ...]
    branch_id: UUID
    last_commit_id: UUID | None
    last_head_commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None


async def materialize_interface_config_bundle(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndexSnapshot,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    bundle: InterfaceConfigBundle,
    branch_id: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
    prefer_snapshot_materialization: bool = False,
) -> InterfaceConfigMaterializationResult:
    effective_branch_id = branch_id or bundle.interface_config_id
    window_configs: list[WindowConfig] = []
    interface_config_window_configs: list[InterfaceConfigWindowConfig] = []
    window_config_layout_configs: list[WindowConfigLayoutConfig] = []
    pane_configs: list[PaneConfig] = []
    interface_config_pane_configs: list[InterfaceConfigPaneConfig] = []
    projection_bindings: list[PaneConfig] = []
    section_mounts: list[InterfaceConfigPaneConfigSectionConfig] = []
    interface_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="InterfaceConfig",
    )
    window_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="WindowConfig",
    )
    pane_config_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="PaneConfig",
    )
    if prefer_snapshot_materialization or not hasattr(runtime, "bind"):
        snapshot = await commit_interface_config_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=effective_branch_id,
            interface_config_projection_hash=interface_config_projection_hash,
            window_config_projection_hash=window_config_projection_hash,
            pane_config_projection_hash=pane_config_projection_hash,
            bundle=bundle,
        )
        return InterfaceConfigMaterializationResult(
            bundle=bundle,
            interface_config=snapshot.interface_config,
            window_configs=snapshot.window_configs,
            interface_config_window_configs=snapshot.interface_config_window_configs,
            window_config_layout_configs=snapshot.window_config_layout_configs,
            pane_configs=snapshot.pane_configs,
            interface_config_pane_configs=snapshot.interface_config_pane_configs,
            projection_experience_view_bindings=(
                snapshot.projection_experience_view_bindings
            ),
            section_mounts=snapshot.section_mounts,
            branch_id=effective_branch_id,
            last_commit_id=snapshot.commit_id,
            last_head_commit_id=snapshot.head_commit_id,
            object_instance_graph_commit_id=(snapshot.object_instance_graph_commit_id),
        )
    interface_config = await _hydrate_lane_root_from_head(
        index=index,
        branch_id=effective_branch_id,
        projection_hash=interface_config_projection_hash,
        root_id=bundle.interface_config_id,
        root_type=InterfaceConfig,
    )
    window_configs_by_id = {
        window_bundle.window_config_id: await _hydrate_lane_root_from_head(
            index=index,
            branch_id=effective_branch_id,
            projection_hash=window_config_projection_hash,
            root_id=window_bundle.window_config_id,
            root_type=WindowConfig,
        )
        for window_bundle in bundle.window_configs
    }
    pane_configs_by_id = {
        pane_bundle.pane_config_id: await _hydrate_lane_root_from_head(
            index=index,
            branch_id=effective_branch_id,
            projection_hash=pane_config_projection_hash,
            root_id=pane_bundle.pane_config_id,
            root_type=PaneConfig,
        )
        for pane_bundle in bundle.pane_configs
    }

    interface_config_lane = runtime.bind(
        branch_id=effective_branch_id,
        projection="InterfaceConfig",
        actor_id=actor_id,
    )
    window_config_lane = runtime.bind(
        branch_id=effective_branch_id,
        projection="WindowConfig",
        actor_id=actor_id,
    )
    pane_config_lane = runtime.bind(
        branch_id=effective_branch_id,
        projection="PaneConfig",
        actor_id=actor_id,
    )

    with interface_config_lane.activate(commit=commit, publish=publish):
        if interface_config is None:
            interface_config = await InterfaceConfig.build(
                name=bundle.name,
                description=bundle.description,
            )
        _require_expected_id(
            actual=interface_config.id,
            expected=bundle.interface_config_id,
            label="InterfaceConfig.id",
        )

    with window_config_lane.activate(commit=commit, publish=publish):
        for window_bundle in bundle.window_configs:
            window_config = window_configs_by_id.get(window_bundle.window_config_id)
            if window_config is None:
                window_config = await WindowConfig.build(
                    key=window_bundle.key,
                    description=window_bundle.description,
                )
            _require_expected_id(
                actual=window_config.id,
                expected=window_bundle.window_config_id,
                label=f"WindowConfig[{window_bundle.key}].id",
            )
            window_configs.append(window_config)

            for layout_bundle in window_bundle.layout_configs:
                window_config_layout_config = await window_config.attach_layout_config(
                    layout_config_id=layout_bundle.layout_config_id,
                    is_default=layout_bundle.is_default,
                )
                _require_expected_id(
                    actual=window_config_layout_config.id,
                    expected=layout_bundle.window_config_layout_config_id,
                    label=f"WindowConfigLayoutConfig[{window_bundle.key}:{layout_bundle.key}].id",
                )
                _require_expected_id(
                    actual=window_config_layout_config.layout_config_id,
                    expected=layout_bundle.layout_config_id,
                    label=(
                        "WindowConfigLayoutConfig"
                        f"[{window_bundle.key}:{layout_bundle.key}].layout_config_id"
                    ),
                )
                window_config_layout_configs.append(window_config_layout_config)

    with pane_config_lane.activate(commit=commit, publish=publish):
        for pane_bundle in bundle.pane_configs:
            pane_config = pane_configs_by_id.get(pane_bundle.pane_config_id)
            if len(pane_bundle.projection_experience_views) != 1:
                raise ValueError(
                    "Interface PaneConfig materialization requires exactly one "
                    "ProjectionExperienceView per pane; "
                    f"pane={pane_bundle.name!r} got {len(pane_bundle.projection_experience_views)}"
                )
            view_bundle = pane_bundle.projection_experience_views[0]
            if pane_config is None:
                pane_config = await PaneConfig.build(
                    name=pane_bundle.name,
                    projection_experience_view_id=view_bundle.projection_experience_view_id,
                    pane_kind=pane_bundle.pane_kind,
                    view_ref=view_bundle.view_ref,
                    description=pane_bundle.description,
                )
            _require_expected_id(
                actual=pane_config.id,
                expected=pane_bundle.pane_config_id,
                label=f"PaneConfig[{pane_bundle.name}].id",
            )
            pane_configs.append(pane_config)
            _require_expected_id(
                actual=pane_config.projection_experience_view_id,
                expected=view_bundle.projection_experience_view_id,
                label=f"PaneConfig[{pane_bundle.name}].projection_experience_view_id",
            )
            _require_expected_id(
                actual=pane_config.id,
                expected=view_bundle.binding_id,
                label=f"PaneConfig[{pane_bundle.name}].binding_id",
            )
            projection_bindings.append(pane_config)

    projection_bindings_by_id = {
        binding.id: binding for binding in projection_bindings if binding.id is not None
    }

    with interface_config_lane.activate(commit=commit, publish=publish):
        for window_bundle, window_config in zip(
            bundle.window_configs, window_configs, strict=False
        ):
            interface_config_window_config = await _attach_window_config_hydrated(
                lane=interface_config_lane,
                interface_config=interface_config,
                window_config=window_config,
                commit=commit,
                publish=publish,
            )
            _require_expected_id(
                actual=interface_config_window_config.id,
                expected=window_bundle.interface_config_window_config_id,
                label=f"InterfaceConfigWindowConfig[{window_bundle.key}].id",
            )
            _require_expected_id(
                actual=interface_config_window_config.interface_config_id,
                expected=bundle.interface_config_id,
                label=f"InterfaceConfigWindowConfig[{window_bundle.key}].interface_config_id",
            )
            _require_expected_id(
                actual=interface_config_window_config.window_config.id,
                expected=window_bundle.window_config_id,
                label=f"InterfaceConfigWindowConfig[{window_bundle.key}].window_config.id",
            )
            _require_expected_id(
                actual=interface_config_window_config.window_config_id,
                expected=window_bundle.window_config_id,
                label=f"InterfaceConfigWindowConfig[{window_bundle.key}].window_config_id",
            )
            interface_config_window_configs.append(interface_config_window_config)

        for pane_bundle, pane_config in zip(
            bundle.pane_configs, pane_configs, strict=False
        ):
            interface_config_pane_config = await _attach_pane_config_hydrated(
                lane=interface_config_lane,
                interface_config=interface_config,
                pane_config=pane_config,
                narrative_key=pane_bundle.narrative_key,
                commit=commit,
                publish=publish,
            )
            _require_expected_id(
                actual=interface_config_pane_config.id,
                expected=stable_interface_config_pane_config_id(
                    interface_config_id=bundle.interface_config_id,
                    pane_config_id=pane_bundle.pane_config_id,
                ),
                label=f"InterfaceConfigPaneConfig[{pane_bundle.name}].id",
            )
            _require_expected_id(
                actual=interface_config_pane_config.pane_config_id,
                expected=pane_bundle.pane_config_id,
                label=f"InterfaceConfigPaneConfig[{pane_bundle.name}].pane_config_id",
            )
            interface_config_pane_configs.append(interface_config_pane_config)

            for view_bundle in pane_bundle.projection_experience_views:
                projection_binding = projection_bindings_by_id.get(
                    view_bundle.binding_id
                )
                if projection_binding is None:
                    raise RuntimeError(
                        "PaneConfig missing after PaneConfig materialization: "
                        f"binding_id={view_bundle.binding_id}"
                    )
                for mount_bundle in view_bundle.section_mounts:
                    section_mount = await interface_config_pane_config.add_section_mount(
                        layout_config_section_config_id=mount_bundle.layout_config_section_config_id,
                    )
                    _require_expected_id(
                        actual=section_mount.id,
                        expected=mount_bundle.mount_id,
                        label=(
                            "InterfaceConfigPaneConfigSectionConfig"
                            f"[{pane_bundle.name}:{mount_bundle.layout_config_section_config_id}].id"
                        ),
                    )
                    section_mounts.append(section_mount)

    return InterfaceConfigMaterializationResult(
        bundle=bundle,
        interface_config=interface_config,
        window_configs=tuple(window_configs),
        interface_config_window_configs=tuple(interface_config_window_configs),
        window_config_layout_configs=tuple(window_config_layout_configs),
        pane_configs=tuple(pane_configs),
        interface_config_pane_configs=tuple(interface_config_pane_configs),
        projection_experience_view_bindings=tuple(projection_bindings),
        section_mounts=tuple(section_mounts),
        branch_id=effective_branch_id,
        last_commit_id=interface_config_lane.last_commit_id,
        last_head_commit_id=(
            interface_config_lane.last_head_commit_id
            or await _resolve_lane_head_commit_id(
                branch_id=effective_branch_id,
                projection_hash=interface_config_projection_hash,
            )
        ),
        object_instance_graph_commit_id=None,
    )


def _require_expected_id(*, actual: UUID | None, expected: UUID, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} mismatch: expected={expected} actual={actual}")


async def _resolve_lane_head_commit_id(
    *, branch_id: UUID, projection_hash: str
) -> UUID | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    commit_id = head.get("commit_id") if head is not None else None
    if commit_id is None:
        return None
    return UUID(str(commit_id))


async def _hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot | None:
    head_commit_id = await _resolve_lane_head_commit_id(
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


async def _attach_window_config_hydrated(
    *,
    lane,
    interface_config: InterfaceConfig,
    window_config: WindowConfig,
    commit: bool,
    publish: bool,
) -> InterfaceConfigWindowConfig:
    if interface_config.id is None or window_config.id is None:
        raise RuntimeError(
            "InterfaceConfig.attach_window_config requires hydrated InterfaceConfig "
            "and WindowConfig ids"
        )
    binding_id = stable_interface_config_window_config_id(
        interface_config_id=interface_config.id,
        window_config_id=window_config.id,
    )
    hydrated_binding: InterfaceConfigWindowConfig | None = None
    for existing in interface_config.interface_config_window_configs:
        if existing.id == binding_id or existing.window_config_id == window_config.id:
            existing.window_config = window_config
            existing.window_config_id = window_config.id
            hydrated_binding = existing
            break
    if hydrated_binding is None:
        hydrated_binding = InterfaceConfigWindowConfig.model_construct(
            id=binding_id,
            interface_config_id=interface_config.id,
            window_config=window_config,
            window_config_id=window_config.id,
        )
        interface_config.interface_config_window_configs.append(hydrated_binding)

    response = await lane.invoke_instance(
        orm_model=interface_config,
        function_name="attach_window_config",
        payload={"window_config_id": window_config.id},
        commit=commit,
        publish=publish,
    )
    payload: Any = response.payload
    if isinstance(payload, dict) and "value" in payload:
        payload = payload["value"]
    if not isinstance(payload, dict):
        raise RuntimeError(
            "InterfaceConfig.attach_window_config returned invalid payload for hydrated materialization: "
            + f"{payload!r}"
        )
    return InterfaceConfigWindowConfig.model_construct(
        id=UUID(str(payload["id"])),
        interface_config_id=interface_config.id,
        window_config=window_config,
        window_config_id=window_config.id,
    )


async def _attach_pane_config_hydrated(
    *,
    lane,
    interface_config: InterfaceConfig,
    pane_config: PaneConfig,
    narrative_key: str | None,
    commit: bool,
    publish: bool,
) -> InterfaceConfigPaneConfig:
    if interface_config.id is None or pane_config.id is None:
        raise RuntimeError(
            "InterfaceConfig.attach_pane_config requires hydrated InterfaceConfig "
            "and PaneConfig ids"
        )
    binding_id = stable_interface_config_pane_config_id(
        interface_config_id=interface_config.id,
        pane_config_id=pane_config.id,
    )
    hydrated_binding: InterfaceConfigPaneConfig | None = None
    for existing in interface_config.interface_config_pane_configs:
        if existing.id == binding_id or existing.pane_config_id == pane_config.id:
            existing.pane_config = pane_config
            existing.pane_config_id = pane_config.id
            if narrative_key is not None:
                existing.narrative_key = narrative_key
            hydrated_binding = existing
            break
    if hydrated_binding is None:
        hydrated_binding = InterfaceConfigPaneConfig.model_construct(
            id=binding_id,
            interface_config_id=interface_config.id,
            pane_config=pane_config,
            pane_config_id=pane_config.id,
            section_mounts=[],
            narrative_key=narrative_key,
        )
        interface_config.interface_config_pane_configs.append(hydrated_binding)

    response = await lane.invoke_instance(
        orm_model=interface_config,
        function_name="attach_pane_config",
        payload={"pane_config_id": pane_config.id, "narrative_key": narrative_key},
        commit=commit,
        publish=publish,
    )
    payload: Any = response.payload
    if isinstance(payload, dict) and "value" in payload:
        payload = payload["value"]
    if not isinstance(payload, dict):
        raise RuntimeError(
            "InterfaceConfig.attach_pane_config returned invalid payload for hydrated materialization: "
            + f"{payload!r}"
        )
    return InterfaceConfigPaneConfig.model_construct(
        id=UUID(str(payload["id"])),
        interface_config_id=interface_config.id,
        pane_config=pane_config,
        pane_config_id=pane_config.id,
        section_mounts=(hydrated_binding.section_mounts),
        narrative_key=payload.get("narrative_key"),
    )
