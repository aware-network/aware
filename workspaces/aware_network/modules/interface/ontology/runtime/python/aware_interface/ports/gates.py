from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from aware_identity.gate import build_identity_gate_step
from aware_interface.session_state import InterfaceRuntimeSessionStateStore
from aware_interface_sdk.attachment import InterfaceAttachmentStore
from aware_network.gate import build_community_gate_step
from aware_environment.gate import compose_environment_gate_flow

from aware_interface.lifecycle.models import (
    InterfaceBackendState,
    InterfaceGateState,
    InterfaceGateStep,
)


class InterfaceGatePort(Protocol):
    """Host-neutral gate-state dependency for interface runtime coordination."""

    async def load_gate_state(
        self,
        *,
        backend: InterfaceBackendState | None = None,
    ) -> "InterfaceGateState | None":
        ...


class EnvironmentInterfaceGatePort:
    """Concrete interface gate adapter over session/auth/local-backend truth."""

    _repository_root: Path
    _state_home: Path
    _namespace: str
    _endpoint: str
    _actor_id: UUID
    _environment_config_id: UUID | None
    _auth_session_available: bool
    _auth_actor_id: UUID | None

    def __init__(
        self,
        *,
        repository_root: Path,
        state_home: Path,
        namespace: str,
        endpoint: str,
        actor_id: UUID,
        environment_config_id: UUID | None,
        auth_session_available: bool,
        auth_actor_id: UUID | None,
    ) -> None:
        self._repository_root = repository_root
        self._state_home = state_home
        self._namespace = namespace
        self._endpoint = endpoint
        self._actor_id = actor_id
        self._environment_config_id = environment_config_id
        self._auth_session_available = auth_session_available
        self._auth_actor_id = auth_actor_id

    async def load_gate_state(
        self,
        *,
        backend: InterfaceBackendState | None = None,
    ) -> InterfaceGateState | None:
        authority_snapshot_available = False
        interface_boot_identity_available = False

        if self._environment_config_id is not None:
            try:
                state_store = InterfaceRuntimeSessionStateStore(
                    state_root=self._state_home,
                    namespace=self._namespace,
                )
                snapshot = await state_store.aload_latest_authority_snapshot(
                    actor_id=self._actor_id,
                    endpoint=self._endpoint,
                    environment_config_id=self._environment_config_id,
                )
                authority_snapshot_available = snapshot is not None
                interface_store = InterfaceAttachmentStore(
                    state_root=self._state_home,
                    namespace=self._namespace,
                )
                interface_boot_identity_available = (
                    await interface_store.aload_interface_id(
                        actor_id=self._actor_id,
                        endpoint=self._endpoint,
                    )
                    is not None
                )
            except Exception:
                authority_snapshot_available = False
                interface_boot_identity_available = False

        network_step = build_community_gate_step(
            endpoint=self._endpoint,
            auth_session_available=self._auth_session_available,
            authority_snapshot_available=authority_snapshot_available,
        )
        identity_step = build_identity_gate_step(
            expected_actor_id=self._actor_id,
            auth_session_available=self._auth_session_available,
            auth_actor_id=self._auth_actor_id,
        )

        boot_crossed, boot_locked_description, boot_crossed_description = _resolve_boot_state(
            environment_config_id=self._environment_config_id,
            authority_snapshot_available=authority_snapshot_available,
            interface_boot_identity_available=interface_boot_identity_available,
            backend=backend,
        )
        flow = compose_environment_gate_flow(
            network_step=network_step,
            identity_step=identity_step,
            boot_crossed=boot_crossed,
            boot_locked_description=boot_locked_description,
            boot_crossed_description=boot_crossed_description,
        )
        return InterfaceGateState(
            destination_key=flow.destination_key,
            active_step_key=flow.active_step_key,
            blocked=flow.blocked,
            steps=tuple(
                InterfaceGateStep(
                    key=step.key,
                    status=step.status,
                    title=step.title,
                    description=step.description,
                )
                for step in flow.steps
            ),
            reason=flow.reason,
        )


def _resolve_boot_state(
    *,
    environment_config_id: UUID | None,
    authority_snapshot_available: bool,
    interface_boot_identity_available: bool,
    backend: InterfaceBackendState | None,
) -> tuple[bool, str | None, str | None]:
    if environment_config_id is None:
        return (
            False,
            "Resolve an environment target before crossing Boot.",
            None,
        )
    if not authority_snapshot_available:
        return (
            False,
            "Bootstrap authority for the selected environment before crossing Boot.",
            None,
        )
    if not interface_boot_identity_available:
        return (
            False,
            "Ensure the boot interface graph before crossing Boot.",
            None,
        )
    if backend is None or not backend.available:
        return (
            False,
            "Local interface backend is unavailable for Boot.",
            None,
        )
    return (
        True,
        None,
        "Boot interface state and local backend are ready.",
    )


__all__ = [
    "InterfaceGatePort",
    "EnvironmentInterfaceGatePort",
]
