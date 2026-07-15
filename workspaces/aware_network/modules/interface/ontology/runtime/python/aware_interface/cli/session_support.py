"""Interface-owned session support helpers for the mounted CLI command."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from uuid import UUID

from aware_cli.shared.authority_cache import authority_root
from aware_cli.session.models import (
    AuthSessionStatus,
    AuthoritySnapshotStatus,
    InterfaceBackendStatus,
    ResolvedCliSession,
)
from aware_cli.session.resolver import (
    iter_session_namespaces,
    load_persisted_context,
    resolve_provider_binding,
    resolve_state_root,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentStatusResponse,
    EnvironmentStatusAuthority,
    EnvironmentStatusAuthorityKind,
    EnvironmentStatusBlock,
)
from aware_interface import (
    InterfaceBackendState,
    InterfaceHostRuntime,
    InterfaceRuntimeCoordinator,
    EnvironmentInterfaceGatePort,
    describe_interface_backend_state as describe_interface_backend_runtime_state,
)
from aware_interface.session_port import InterfaceRuntimeSessionPort
from aware_interface.session_state import InterfaceRuntimeSessionStateStore
from aware_interface.session_target import (
    resolve_interface_session_target,
    resolve_interface_session_target_coordinates,
)
from aware_interface_sdk.attachment import InterfaceAttachment
from aware_interface_sdk.auth_store import (
    load_interface_auth_session,
    login_interface_token_attachment,
)


def resolve_cli_session(
    *,
    repository_root: Path,
    endpoint: str | None = None,
    environment_config_id: UUID | None = None,
    agent_identity_id: UUID | None = None,
    namespace: str | None = None,
    state_home: str | None = None,
    provider: str | None = None,
    provider_session_id: str | None = None,
) -> ResolvedCliSession:
    effective_namespace = (
        (namespace or "").strip()
        or (os.environ.get("AWARE_STATE_NAMESPACE") or "").strip()
        or "cli"
    )
    resolved_state_home = resolve_state_root(state_home)
    try:
        coordinates = resolve_interface_session_target_coordinates(
            repository_root=repository_root,
            endpoint=endpoint,
            environment_config_id=environment_config_id,
        )
    except RuntimeError as exc:
        if "Node endpoint missing" not in str(exc):
            raise
        target = resolve_interface_session_target(
            repository_root=repository_root,
            endpoint=endpoint,
            environment_config_id=environment_config_id,
            agent_identity_id=agent_identity_id,
        )
        auth_status = _resolve_auth_session_status(
            endpoint=target.endpoint,
            preferred_namespace=effective_namespace,
            state_home=str(resolved_state_home),
        )
    else:
        auth_status = _resolve_auth_session_status(
            endpoint=coordinates.endpoint,
            preferred_namespace=effective_namespace,
            state_home=str(resolved_state_home),
        )
        target = resolve_interface_session_target(
            repository_root=repository_root,
            endpoint=coordinates.endpoint,
            environment_config_id=coordinates.environment_config_id,
            agent_identity_id=agent_identity_id,
            auth_actor_id=auth_status.actor_id,
        )
    provider_binding = resolve_provider_binding(
        provider=provider,
        provider_session_id=provider_session_id,
    )
    persisted_context = load_persisted_context(
        actor_id=target.actor_id,
        endpoint=target.endpoint,
        environment_config_id=target.environment_config_id,
        preferred_namespace=effective_namespace,
        state_home=state_home,
    )
    authority_status = _resolve_authority_snapshot_status(
        actor_id=target.actor_id,
        endpoint=target.endpoint,
        environment_config_id=target.environment_config_id,
        preferred_namespace=effective_namespace,
        state_home=state_home,
    )
    return ResolvedCliSession(
        repository_root=repository_root,
        endpoint=target.endpoint,
        environment_config_id=target.environment_config_id,
        actor_id=target.actor_id,
        agent_identity_id=target.agent_identity_id,
        namespace=effective_namespace,
        state_home=resolved_state_home,
        provider_binding=provider_binding,
        persisted_context=persisted_context,
        auth_session=auth_status,
        authority_snapshot=authority_status,
        environment_target_reason=target.environment_target_reason,
    )


async def login_cli_session(
    *,
    repository_root: Path,
    endpoint: str | None = None,
    namespace: str | None = None,
    state_home: str | None = None,
    auth_token: str | None = None,
) -> ResolvedCliSession:
    effective_namespace = (
        (namespace or "").strip()
        or (os.environ.get("AWARE_STATE_NAMESPACE") or "").strip()
        or "cli"
    )
    resolved_state_home = resolve_state_root(state_home)
    token = _resolve_auth_token(auth_token)
    await login_interface_token_session(
        repository_root=repository_root,
        endpoint=endpoint,
        token=token,
        namespace=effective_namespace,
        state_home=str(resolved_state_home),
    )
    return resolve_cli_session(
        repository_root=repository_root,
        endpoint=endpoint,
        namespace=effective_namespace,
        state_home=str(resolved_state_home),
    )


async def login_interface_token_session(
    *,
    repository_root: Path,
    endpoint: str | None,
    token: str,
    namespace: str,
    state_home: str,
):
    return await login_interface_token_attachment(
        repository_root=repository_root,
        endpoint=endpoint,
        token=token,
        namespace=namespace,
        state_home=state_home,
    )


def describe_local_session_status(
    *,
    resolved: ResolvedCliSession,
) -> object:
    if resolved.environment_config_id is None:
        reason = (
            resolved.environment_target_reason
            or "Environment target is not resolved yet."
        )
        return {
            "status": "partial",
            "status_version": "aware.status.v1",
            "error": None,
            "blocks": [
                {
                    "name": "environment_session",
                    "authority": {
                        "kind": EnvironmentStatusAuthorityKind.local_fs_view,
                        "source_artifact": "aware_interface.cli.session_support",
                    },
                    "payload": {
                        "endpoint": resolved.endpoint,
                        "actor_id": str(resolved.actor_id),
                        "agent_identity_id": (
                            str(resolved.agent_identity_id)
                            if resolved.agent_identity_id is not None
                            else None
                        ),
                    },
                    "available": False,
                    "unavailable_reason": reason,
                },
            ],
            "refusals": [
                {
                    "code": "environment_target_unresolved",
                    "message": "Environment target is not resolved yet.",
                    "reason": reason,
                    "metadata": {
                        "endpoint": resolved.endpoint,
                        "actor_id": str(resolved.actor_id),
                    },
                },
            ],
        }

    return DescribeEnvironmentStatusResponse(
        environment_id=resolved.environment_config_id,
        status="succeeded",
        status_version="aware.status.v1",
        blocks=[
            EnvironmentStatusBlock(
                name="environment_session",
                authority=EnvironmentStatusAuthority(
                    kind=EnvironmentStatusAuthorityKind.local_fs_view,
                    source_artifact="aware_interface.cli.session_support",
                ),
                payload={
                    "endpoint": resolved.endpoint,
                    "actor_id": str(resolved.actor_id),
                    "environment_config_id": (
                        str(resolved.environment_config_id)
                        if resolved.environment_config_id is not None
                        else None
                    ),
                },
                available=resolved.environment_config_id is not None,
                unavailable_reason=(
                    None
                    if resolved.environment_config_id is not None
                    else "environment_config_id_required"
                ),
            ),
            EnvironmentStatusBlock(
                name="interface_boot_identity",
                authority=EnvironmentStatusAuthority(
                    kind=EnvironmentStatusAuthorityKind.local_fs_view,
                    source_artifact="aware_interface.cli.session_support",
                ),
                payload={
                    "endpoint": resolved.endpoint,
                    "actor_id": str(resolved.actor_id),
                },
                available=resolved.auth_session.available,
                unavailable_reason=(
                    None
                    if resolved.auth_session.available
                    else "no_persisted_auth_session"
                ),
            ),
            EnvironmentStatusBlock(
                name="authority_snapshot",
                authority=EnvironmentStatusAuthority(
                    kind=EnvironmentStatusAuthorityKind.local_fs_view,
                    source_artifact="aware_interface.cli.session_support",
                ),
                payload={
                    "root": (
                        str(resolved.authority_snapshot.root)
                        if resolved.authority_snapshot.root is not None
                        else None
                    ),
                    "latest": (
                        str(resolved.authority_snapshot.latest_path)
                        if resolved.authority_snapshot.latest_path is not None
                        else None
                    ),
                },
                available=(
                    resolved.authority_snapshot.available
                    and resolved.authority_snapshot.latest_present
                ),
                unavailable_reason=(
                    None
                    if resolved.authority_snapshot.latest_present
                    else resolved.authority_snapshot.reason
                    or "no_persisted_authority_snapshot"
                ),
            ),
        ],
    )


def resolve_interface_host_runtime(
    *,
    resolved: ResolvedCliSession,
) -> InterfaceHostRuntime:
    _ = resolved
    raise RuntimeError(
        "CLI Interface host runtime construction requires ontology runtime "
        "artifact-set refs. Legacy Environment runtime manifest boot is retired."
    )


def build_interface_runtime_coordinator(
    *,
    resolved: ResolvedCliSession,
    attachment: InterfaceAttachment | None = None,
) -> InterfaceRuntimeCoordinator:
    runtime = resolve_interface_host_runtime(resolved=resolved)
    session_port = (
        InterfaceRuntimeSessionPort(
            client=attachment.client,
            interface_id=attachment.interface_id,
            endpoint=attachment.endpoint,
            state_store=InterfaceRuntimeSessionStateStore(
                state_root=resolved.state_home,
                namespace=resolved.namespace,
            ),
        )
        if attachment is not None
        else None
    )
    gate_port = EnvironmentInterfaceGatePort(
        repository_root=resolved.repository_root,
        state_home=resolved.state_home,
        namespace=resolved.namespace,
        endpoint=resolved.endpoint,
        actor_id=resolved.actor_id,
        environment_config_id=resolved.environment_config_id,
        auth_session_available=resolved.auth_session.available,
        auth_actor_id=resolved.auth_session.actor_id,
    )
    return runtime.build_coordinator(session_port=session_port, gate_port=gate_port)


def describe_interface_backend_status(
    *,
    resolved: ResolvedCliSession,
) -> InterfaceBackendStatus:
    try:
        coordinator = build_interface_runtime_coordinator(resolved=resolved)
        state = _run(coordinator.snapshot()).backend
    except Exception:
        state = _run(
            describe_interface_backend_runtime_state(
                repository_root=resolved.repository_root,
                state_home=resolved.state_home,
                namespace=resolved.namespace,
            )
        )
    return _to_cli_backend_status(state=state)


def _resolve_auth_token(explicit_token: str | None = None) -> str:
    token = (explicit_token or os.environ.get("AWARE_AUTH_TOKEN") or "").strip()
    if not token:
        raise RuntimeError(
            "Auth token is required. Set `AWARE_AUTH_TOKEN` or pass `--auth-token`."
        )
    return token


def _resolve_auth_session_status(
    *,
    endpoint: str,
    preferred_namespace: str,
    state_home: str | None,
) -> AuthSessionStatus:
    for namespace in iter_session_namespaces(preferred_namespace):
        auth_session = load_interface_auth_session(
            endpoint=endpoint,
            namespace=namespace,
            state_home=state_home,
        )
        if auth_session is None:
            continue
        return AuthSessionStatus(
            available=True,
            method=auth_session.method,
            actor_id=auth_session.actor_id,
            public_key=auth_session.public_key,
            token_id=auth_session.token_id,
            token_type=auth_session.token_type,
            scopes=auth_session.scopes,
            context_environment_id=auth_session.context_environment_id,
            context_process_id=auth_session.context_process_id,
            context_thread_id=auth_session.context_thread_id,
            path=auth_session.path,
        )

    return AuthSessionStatus(
        available=False,
        method=None,
        actor_id=None,
        public_key=None,
        token_id=None,
        token_type=None,
        path=None,
        reason="No persisted auth session.",
    )


def _resolve_authority_snapshot_status(
    *,
    actor_id: UUID,
    endpoint: str,
    environment_config_id: UUID | None,
    preferred_namespace: str,
    state_home: str | None,
) -> AuthoritySnapshotStatus:
    if environment_config_id is None:
        return AuthoritySnapshotStatus(
            available=False,
            namespace=preferred_namespace,
            root=None,
            latest_path=None,
            latest_present=False,
            reason="Environment target is not resolved yet.",
        )

    for namespace in iter_session_namespaces(preferred_namespace):
        root = authority_root(
            actor_id=actor_id,
            endpoint=endpoint,
            environment_config_id=environment_config_id,
            namespace=namespace,
            state_home=state_home,
        )
        latest_path = root / "latest.json"
        if latest_path.exists():
            return AuthoritySnapshotStatus(
                available=True,
                namespace=namespace,
                root=root,
                latest_path=latest_path,
                latest_present=True,
            )

    root = authority_root(
        actor_id=actor_id,
        endpoint=endpoint,
        environment_config_id=environment_config_id,
        namespace=preferred_namespace,
        state_home=state_home,
    )
    latest_path = root / "latest.json"
    return AuthoritySnapshotStatus(
        available=True,
        namespace=preferred_namespace,
        root=root,
        latest_path=latest_path,
        latest_present=False,
    )


def _to_cli_backend_status(*, state: InterfaceBackendState) -> InterfaceBackendStatus:
    return InterfaceBackendStatus(
        available=state.available,
        manifest_path=state.manifest_path,
        registry_path=state.registry_path,
        database_path=state.database_path,
        database_exists=state.database_exists,
        environment_id=state.environment_id,
        opg_count=state.opg_count,
        projection_bundle_available=state.projection_bundle_available,
        projection_plan_count=state.projection_plan_count,
        table_count=state.table_count,
        reason=state.reason,
    )


def _run(coro):  # type: ignore[no-untyped-def]
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError(
        "CLI interface host helpers cannot run inside an existing event loop"
    )


__all__ = [
    "build_interface_runtime_coordinator",
    "describe_interface_backend_status",
    "describe_local_session_status",
    "login_interface_token_session",
    "login_cli_session",
    "resolve_cli_session",
    "resolve_interface_host_runtime",
]
