from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Protocol, cast

from aware_interface import InterfaceMaterializedPaneState, InterfaceRuntimeState
from aware_interface.host_runtime import InterfaceHostRuntimeSyncAssets

from aware_interface_service.host.view_state_provider_registry import (
    InterfaceViewStateProviderInput,
    resolve_view_state,
)
from aware_interface_service.models import (
    InterfaceHostServiceLaneSyncState,
    InterfaceHostServiceState,
)

if TYPE_CHECKING:
    from aware_interface import InterfaceLaneSyncResult, InterfaceLaneSyncService
    from aware_interface.session_port import FocusScopeLane, SectionFocusScopeLane


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class InterfaceHostLaneSyncCoordinator(Protocol):
    async def snapshot(self) -> InterfaceRuntimeState: ...

    async def resolve_focus_scope_lane(
        self, *, window_key: str
    ) -> "FocusScopeLane": ...

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> "SectionFocusScopeLane": ...

    def build_lane_sync_service(
        self,
        *,
        include_commit_payload: bool = True,
    ) -> "InterfaceLaneSyncService": ...


class InterfaceHostLaneSyncHostRuntime(Protocol):
    def load_sync_assets(
        self,
        *,
        projection_hash: str,
    ) -> InterfaceHostRuntimeSyncAssets: ...


class InterfaceHostLaneSyncRuntime(Protocol):
    coordinator: InterfaceHostLaneSyncCoordinator | None
    host_runtime: InterfaceHostLaneSyncHostRuntime | None
    _lane_sync_state: InterfaceHostServiceLaneSyncState | None
    _runtime_state: InterfaceRuntimeState | None

    def state(self) -> InterfaceHostServiceState: ...

    async def _refresh_local_runtime_state(self) -> None: ...

    async def _refresh_hosted_service_status(self) -> None: ...

    async def _refresh_host_surface(self) -> None: ...


def lane_sync_state_for_lane(
    *,
    window_key: str,
    lane: "FocusScopeLane",
    watching: bool,
    error: str | None,
) -> InterfaceHostServiceLaneSyncState:
    return InterfaceHostServiceLaneSyncState(
        enabled=True,
        watching=watching,
        window_key=window_key,
        lane_id=str(lane.focus_scope_id),
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        error=error,
    )


def _pane_state_key(
    *,
    window_key: str,
    layout_key: str,
    section_key: str,
    pane_kind: str,
    pane_config_id: object | None,
    projection_hash: str | None,
) -> str:
    return ":".join(
        (
            window_key,
            layout_key,
            section_key,
            pane_kind,
            str(pane_config_id or ""),
            projection_hash or "",
        )
    )


def _pane_state_key_for_descriptor(pane: object) -> str:
    return _pane_state_key(
        window_key=getattr(pane, "window_key"),
        layout_key=getattr(pane, "layout_key"),
        section_key=getattr(pane, "section_key"),
        pane_kind=getattr(pane, "pane_kind"),
        pane_config_id=getattr(pane, "pane_config_id", None),
        projection_hash=getattr(pane, "state_projection_hash", None),
    )


def _graph_hash_post(result: "InterfaceLaneSyncResult") -> str | None:
    materialized = result.materialized_lane
    if materialized is None:
        return None
    return str(materialized.graph.hash or "") or None


def _lane_sync_provenance(
    *,
    result: "InterfaceLaneSyncResult",
    assets: InterfaceHostRuntimeSyncAssets,
    graph_hash_post: str | None,
) -> dict[str, object]:
    object_config_graph_id = getattr(assets.ocg, "id", None)
    provenance: dict[str, object] = {
        "source_kind": "interface_host_fanout_materialization",
        "branch_id": result.branch_id,
        "projection_hash": result.projection_hash,
        "head_commit_id": result.head_commit_id,
        "previous_head_commit_id": result.previous_head_commit_id,
        "fetched_commit_ids": list(result.fetched_commit_ids),
        "advanced": result.advanced,
        "projected": result.projected,
        "object_config_graph_id": str(object_config_graph_id or ""),
        "graph_hash_post": graph_hash_post,
    }
    materialized = result.materialized_lane
    if materialized is not None:
        provenance.update(
            {
                "object_projection_graph_id": str(
                    materialized.graph.object_projection_graph_id
                ),
                "root_class_instance_id": (
                    str(materialized.graph.root_class_instance_id)
                    if materialized.graph.root_class_instance_id is not None
                    else None
                ),
                "class_instance_count": len(materialized.graph.class_instances),
                "relationship_count": len(
                    materialized.graph.class_instance_relationships
                ),
                "applied_commit_ids": list(materialized.applied_commit_ids),
                "snapshot_commit_id": materialized.snapshot_commit_id,
            }
        )
    projection = result.projection_result
    if projection is not None:
        provenance["projection"] = {
            "projector_id": projection.projector_id,
            "projection_hash": projection.projection_hash,
            "head_commit_id": projection.head_commit_id,
            "cursor_id": projection.cursor_id,
            "projected": projection.projected,
            "class_row_count": projection.class_row_count,
            "association_row_count": projection.association_row_count,
        }
    return provenance


def _materialized_pane_states_for_result(
    *,
    runtime_state: InterfaceRuntimeState,
    previous_runtime_state: InterfaceRuntimeState | None,
    result: "InterfaceLaneSyncResult",
    assets: InterfaceHostRuntimeSyncAssets,
    materialized_at: str,
) -> tuple[InterfaceMaterializedPaneState, ...]:
    matched_keys: set[str] = set()
    graph_hash_post = _graph_hash_post(result)
    provenance = _lane_sync_provenance(
        result=result,
        assets=assets,
        graph_hash_post=graph_hash_post,
    )
    status = "materialized" if result.materialized_lane is not None else "synced"

    states: list[InterfaceMaterializedPaneState] = []
    for pane in runtime_state.resolved_panes:
        if pane.branch_id is None:
            continue
        if str(pane.branch_id) != result.branch_id:
            continue
        if pane.state_projection_hash != result.projection_hash:
            continue
        key = _pane_state_key_for_descriptor(pane)
        matched_keys.add(key)
        pane_provenance = dict(provenance)
        _add_pane_view_identity(
            pane_provenance=pane_provenance,
            pane=pane,
        )
        state_payload: dict[str, object] = {}
        state_error: str | None = None
        state_status = status
        state_provider_ref = getattr(pane, "state_provider_ref", None)
        if state_provider_ref is not None and str(state_provider_ref).strip():
            pane_provenance["state_provider_ref"] = str(state_provider_ref).strip()
            pane_provenance["state_provider_kind"] = (
                str(
                    getattr(pane, "state_provider_kind", None)
                    or "runtime_callable"
                ).strip()
                or "runtime_callable"
            )
            try:
                resolved_state = resolve_view_state(
                    InterfaceViewStateProviderInput(
                        pane=pane,
                        result=result,
                        assets=assets,
                        provenance=pane_provenance,
                    )
                )
                state_payload = cast(dict[str, object], dict(resolved_state.state))
                _add_resolved_view_contract_identity(
                    pane_provenance=pane_provenance,
                    resolved_state=resolved_state,
                )
            except Exception as exc:
                state_error = str(exc)
                state_status = "error"
                pane_provenance["state_provider_error"] = state_error
        states.append(
            InterfaceMaterializedPaneState(
                pane_state_key=key,
                window_key=pane.window_key,
                layout_key=pane.layout_key,
                section_key=pane.section_key,
                pane_kind=pane.pane_kind,
                pane_config_id=pane.pane_config_id,
                pane_package_id=pane.pane_package_id,
                focus_scope_id=pane.focus_scope_id,
                branch_id=pane.branch_id,
                projection_experience_view_id=pane.projection_experience_view_id,
                projection_view_id=pane.projection_view_id,
                state_model_id=pane.state_model_id,
                projection_hash=pane.state_projection_hash,
                status=state_status,
                head_commit_id=result.head_commit_id,
                graph_hash_post=graph_hash_post,
                materialized_at=materialized_at,
                state=state_payload,
                provenance=pane_provenance,
                error=state_error,
            )
        )

    if previous_runtime_state is not None:
        current_pane_keys = {
            _pane_state_key_for_descriptor(pane)
            for pane in runtime_state.resolved_panes
        }
        states.extend(
            state
            for state in previous_runtime_state.materialized_pane_states
            if state.pane_state_key in current_pane_keys
            and state.pane_state_key not in matched_keys
        )

    states.sort(key=lambda state: state.pane_state_key)
    return tuple(states)


def _add_pane_view_identity(
    *,
    pane_provenance: dict[str, object],
    pane: object,
) -> None:
    view_ref = _optional_pane_text(pane, "view_ref")
    projection_view_key = _optional_pane_text(pane, "projection_view_key")
    state_model_id = getattr(pane, "state_model_id", None)
    if view_ref is not None:
        pane_provenance["view_ref"] = view_ref
    if projection_view_key is not None:
        pane_provenance["projection_view_key"] = projection_view_key
    if state_model_id is not None:
        pane_provenance["state_model_id"] = str(state_model_id)


def _add_resolved_view_contract_identity(
    *,
    pane_provenance: dict[str, object],
    resolved_state: object,
) -> None:
    state_model_ref = getattr(resolved_state, "state_model_ref", None)
    version = getattr(resolved_state, "version", None)
    registry_module = getattr(resolved_state, "registry_module", None)
    contract_validated = getattr(resolved_state, "contract_validated", False)
    if state_model_ref:
        pane_provenance["state_model_ref"] = str(state_model_ref)
    if version:
        pane_provenance["view_contract_version"] = str(version)
    if registry_module:
        pane_provenance["view_model_registry"] = str(registry_module)
    if contract_validated:
        pane_provenance["view_contract_validated"] = True


def _optional_pane_text(pane: object, attr: str) -> str | None:
    raw = getattr(pane, attr, None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


async def resolve_focus_scope_lane(
    runtime: InterfaceHostLaneSyncRuntime,
    *,
    window_key: str,
) -> "FocusScopeLane":
    coordinator = runtime.coordinator
    if coordinator is None:
        raise RuntimeError(
            "Interface host service runtime is missing a coordinator; cannot resolve focus scope lane."
        )
    if runtime.host_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is missing a host runtime; cannot resolve sync assets."
        )
    return await coordinator.resolve_focus_scope_lane(window_key=window_key)


async def resolve_section_focus_scope_lane_for_layout(
    runtime: InterfaceHostLaneSyncRuntime,
    *,
    window_key: str,
    layout_key: str,
    section_key: str,
) -> "SectionFocusScopeLane":
    coordinator = runtime.coordinator
    if coordinator is None:
        raise RuntimeError(
            "Interface host service runtime is missing a coordinator; cannot resolve section focus scope lanes."
        )
    return await coordinator.resolve_section_focus_scope_lane(
        window_key=window_key,
        layout_key=layout_key,
        section_key=section_key,
    )


async def resolve_lane_sync_context(
    runtime: InterfaceHostLaneSyncRuntime,
    *,
    window_key: str,
    include_commit_payload: bool,
) -> tuple[
    "FocusScopeLane", "InterfaceLaneSyncService", InterfaceHostRuntimeSyncAssets
]:
    lane = await resolve_focus_scope_lane(runtime, window_key=window_key)
    coordinator = runtime.coordinator
    host_runtime = runtime.host_runtime
    if coordinator is None or host_runtime is None:
        raise RuntimeError(
            "Interface host service runtime is missing coordinator/runtime ownership for lane sync."
        )
    sync_service = coordinator.build_lane_sync_service(
        include_commit_payload=include_commit_payload,
    )
    assets = host_runtime.load_sync_assets(projection_hash=lane.projection_hash)
    return lane, sync_service, assets


async def record_lane_sync_result(
    runtime: InterfaceHostLaneSyncRuntime,
    *,
    window_key: str,
    lane: "FocusScopeLane",
    result: "InterfaceLaneSyncResult",
    assets: InterfaceHostRuntimeSyncAssets,
    watching: bool,
) -> None:
    previous = runtime._lane_sync_state
    previous_runtime_state = runtime._runtime_state
    lane_sync_state = lane_sync_state_for_lane(
        window_key=window_key,
        lane=lane,
        watching=watching,
        error=None,
    )
    synced_at = _utc_now_iso()
    updates_received = previous.updates_received + 1 if previous is not None else 1
    advanced_count = (
        previous.advanced_count + (1 if result.advanced else 0)
        if previous is not None
        else (1 if result.advanced else 0)
    )
    graph_hash_post = _graph_hash_post(result)
    runtime._lane_sync_state = replace(
        lane_sync_state,
        updates_received=updates_received,
        advanced_count=advanced_count,
        last_commit_id=result.head_commit_id,
        last_graph_hash_post=(
            graph_hash_post
            if graph_hash_post is not None
            else previous.last_graph_hash_post if previous is not None else None
        ),
        last_synced_at=synced_at,
    )
    coordinator = runtime.coordinator
    if coordinator is None:
        raise RuntimeError(
            "Interface host service runtime is missing a coordinator; cannot refresh runtime state after sync."
        )
    runtime_state = await coordinator.snapshot()
    runtime._runtime_state = replace(
        runtime_state,
        materialized_pane_states=_materialized_pane_states_for_result(
            runtime_state=runtime_state,
            previous_runtime_state=previous_runtime_state,
            result=result,
            assets=assets,
            materialized_at=synced_at,
        ),
    )
    await runtime._refresh_local_runtime_state()
    await runtime._refresh_hosted_service_status()
    await runtime._refresh_host_surface()


async def sync_focus_scope_lane_once(
    runtime: InterfaceHostLaneSyncRuntime,
    *,
    window_key: str = "execution",
    include_commit_payload: bool = True,
    force: bool = False,
) -> InterfaceHostServiceState:
    lane, sync_service, assets = await resolve_lane_sync_context(
        runtime,
        window_key=window_key,
        include_commit_payload=include_commit_payload,
    )
    result = await sync_service.sync_lane_head(
        branch_id=str(lane.branch_id),
        projection_hash=lane.projection_hash,
        lane_id=str(lane.focus_scope_id),
        ocg=assets.ocg,
        opg=assets.opg,
        force=force,
    )
    await record_lane_sync_result(
        runtime,
        window_key=window_key,
        lane=lane,
        result=result,
        assets=assets,
        watching=False,
    )
    return runtime.state()


async def watch_focus_scope_lane(
    runtime: InterfaceHostLaneSyncRuntime,
    *,
    window_key: str = "execution",
    include_initial: bool = False,
    include_commit_payload: bool = True,
    force: bool = False,
) -> None:
    lane, sync_service, assets = await resolve_lane_sync_context(
        runtime,
        window_key=window_key,
        include_commit_payload=include_commit_payload,
    )
    runtime._lane_sync_state = lane_sync_state_for_lane(
        window_key=window_key,
        lane=lane,
        watching=True,
        error=None,
    )
    try:
        async for result in sync_service.watch_lane(
            branch_id=str(lane.branch_id),
            projection_hash=lane.projection_hash,
            lane_id=str(lane.focus_scope_id),
            ocg=assets.ocg,
            opg=assets.opg,
            include_initial=include_initial,
            force=force,
        ):
            await record_lane_sync_result(
                runtime,
                window_key=window_key,
                lane=lane,
                result=result,
                assets=assets,
                watching=True,
            )
    except Exception as exc:
        runtime._lane_sync_state = replace(
            lane_sync_state_for_lane(
                window_key=window_key,
                lane=lane,
                watching=False,
                error=str(exc),
            ),
            updates_received=(
                runtime._lane_sync_state.updates_received
                if runtime._lane_sync_state is not None
                else 0
            ),
            advanced_count=(
                runtime._lane_sync_state.advanced_count
                if runtime._lane_sync_state is not None
                else 0
            ),
            last_commit_id=(
                runtime._lane_sync_state.last_commit_id
                if runtime._lane_sync_state is not None
                else None
            ),
            last_graph_hash_post=(
                runtime._lane_sync_state.last_graph_hash_post
                if runtime._lane_sync_state is not None
                else None
            ),
            last_synced_at=(
                runtime._lane_sync_state.last_synced_at
                if runtime._lane_sync_state is not None
                else None
            ),
        )
        raise
    finally:
        if runtime._lane_sync_state is not None:
            runtime._lane_sync_state = replace(runtime._lane_sync_state, watching=False)


__all__ = [
    "InterfaceHostLaneSyncCoordinator",
    "InterfaceHostLaneSyncHostRuntime",
    "InterfaceHostLaneSyncRuntime",
    "lane_sync_state_for_lane",
    "record_lane_sync_result",
    "resolve_focus_scope_lane",
    "resolve_lane_sync_context",
    "resolve_section_focus_scope_lane_for_layout",
    "sync_focus_scope_lane_once",
    "watch_focus_scope_lane",
]
