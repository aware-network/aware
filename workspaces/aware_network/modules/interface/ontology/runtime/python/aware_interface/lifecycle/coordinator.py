from __future__ import annotations

from typing import Any, TYPE_CHECKING, Protocol
from uuid import UUID

from aware_interface.lifecycle.models import (
    InterfaceActionReceipt,
    InterfaceActionRequest,
    InterfaceBackendState,
    InterfaceRuntimeState,
)
from aware_interface.lifecycle.state import compose_interface_runtime_state


class _InterfaceCoordinatorRuntime(Protocol):
    async def describe_backend_state(self) -> InterfaceBackendState: ...

    def build_lane_sync_service(
        self,
        *,
        session_port: "InterfaceSessionPort",
        include_commit_payload: bool = True,
    ) -> "InterfaceLaneSyncService": ...


if TYPE_CHECKING:
    from aware_interface.lane_sync import InterfaceLaneSyncService
    from aware_interface.ports import (
        InterfaceActionPort,
        InterfaceExperiencePort,
        InterfaceGatePort,
        InterfaceSessionPort,
        InterfaceNavigationContextLayoutPort,
    )


class InterfaceRuntimeCoordinator:
    """Host-neutral lifecycle coordinator over the committed interface backend."""

    _runtime: _InterfaceCoordinatorRuntime
    _session_port: "InterfaceSessionPort | None"
    _gate_port: "InterfaceGatePort | None"
    _experience_port: "InterfaceExperiencePort | None"
    _navigation_context_layout_port: "InterfaceNavigationContextLayoutPort | None"
    _action_port: "InterfaceActionPort | None"

    def __init__(
        self,
        *,
        runtime: _InterfaceCoordinatorRuntime,
        session_port: "InterfaceSessionPort | None" = None,
        gate_port: "InterfaceGatePort | None" = None,
        experience_port: "InterfaceExperiencePort | None" = None,
        navigation_context_layout_port: "InterfaceNavigationContextLayoutPort | None" = None,
        action_port: "InterfaceActionPort | None" = None,
    ) -> None:
        self._runtime = runtime
        self._session_port = session_port
        self._gate_port = gate_port
        self._experience_port = experience_port
        self._navigation_context_layout_port = navigation_context_layout_port
        self._action_port = action_port

    async def snapshot(self) -> InterfaceRuntimeState:
        backend: InterfaceBackendState = await self._runtime.describe_backend_state()
        gate_state = None
        if self._gate_port is not None:
            gate_state = await self._gate_port.load_gate_state(backend=backend)

        warnings: list[str] = []
        state = compose_interface_runtime_state(
            backend=backend,
            gate_state=gate_state,
        )
        resolved_view = None
        if self._experience_port is not None:
            resolved_view = await self._experience_port.resolve_view(state=state)
            state = compose_interface_runtime_state(
                backend=backend,
                gate_state=gate_state,
                resolved_view=resolved_view,
            )

        navigation_context_layout_target = None
        if self._navigation_context_layout_port is not None:
            navigation_context_layout_target = (
                await self._navigation_context_layout_port.resolve_navigation_context_layout_target(
                    state=state,
                )
            )
            state = compose_interface_runtime_state(
                backend=backend,
                gate_state=gate_state,
                resolved_view=resolved_view,
                navigation_context_layout_target=navigation_context_layout_target,
            )

        if self._session_port is None:
            warnings.append("session_port_unbound")
        if not backend.available:
            warnings.append("interface_backend_unavailable")

        return compose_interface_runtime_state(
            backend=backend,
            gate_state=gate_state,
            resolved_view=resolved_view,
            navigation_context_layout_target=navigation_context_layout_target,
            warnings=tuple(warnings),
        )

    def build_lane_sync_service(
        self,
        *,
        include_commit_payload: bool = True,
    ) -> "InterfaceLaneSyncService":
        if self._session_port is None:
            raise RuntimeError(
                "Interface runtime coordinator is missing a session port; cannot build lane sync service."
            )
        return self._runtime.build_lane_sync_service(
            session_port=self._session_port,
            include_commit_payload=include_commit_payload,
        )

    async def ensure_boot_interface_graph(self) -> UUID:
        if self._session_port is None:
            raise RuntimeError(
                "Interface runtime coordinator is missing a session port; cannot ensure interface boot graph."
            )
        return await self._session_port.ensure_boot_interface_graph()

    async def resolve_projection_hash(self, *, opg_name: str) -> str:
        if self._session_port is None:
            raise RuntimeError(
                "Interface runtime coordinator is missing a session port; cannot resolve projection hashes."
            )
        return await self._session_port.resolve_projection_hash(opg_name=opg_name)

    async def resolve_focus_scope_lane(
        self,
        *,
        window_key: str,
    ) -> Any:
        if self._session_port is None:
            raise RuntimeError(
                "Interface runtime coordinator is missing a session port; cannot resolve focus scope lane."
            )
        return await self._session_port.resolve_focus_scope_lane(window_key=window_key)

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> Any:
        if self._session_port is None:
            raise RuntimeError(
                "Interface runtime coordinator is missing a session port; cannot resolve section focus scope lane."
            )
        return await self._session_port.resolve_section_focus_scope_lane(
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
        )

    def context_ids(self) -> tuple[UUID | None, UUID | None]:
        if self._session_port is None:
            raise RuntimeError(
                "Interface runtime coordinator is missing a session port; cannot resolve context ids."
            )
        return self._session_port.context_ids()

    async def perform_action(
        self,
        request: InterfaceActionRequest,
    ) -> InterfaceActionReceipt:
        if self._action_port is None:
            return InterfaceActionReceipt(
                status="unavailable",
                error="Interface runtime coordinator is missing an action port.",
            )
        return await self._action_port.perform_action(request)


__all__ = [
    "InterfaceRuntimeCoordinator",
]
