from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Callable
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_service_service_dto.comms.models.service import ServiceOperationResponse
from aware_service_runtime.duplex_client import ServiceHostDuplexRequestHandle
from aware_utils.logging import logger

from aware_interface_service.app import (
    InterfaceHostServiceApp,
    InterfaceHostServiceBundleFactory,
    InterfaceHostServiceConfig,
    build_namespaced_service_config,
)
from aware_interface_service.host.actions import InterfaceActionTarget
from aware_interface_service.host.capabilities.attention import (
    AttentionLayoutIntentSection,
    AttentionLayoutTopologyIntentSection,
)
from aware_interface_service.models import (
    InterfaceAppScreenEntryResult,
    InterfaceEnvironmentEntryResult,
    InterfaceEnvironmentNavigationSelectResult,
    InterfaceHostedNamespaceState,
    InterfaceEnvironmentSessionJoinResult,
    InterfaceHostServiceRendererCapabilitiesState,
    InterfaceHostAttentionLayoutTransitionResult,
    InterfaceHostAttentionLayoutTopologyTransitionResult,
    InterfaceHostServiceState,
)


@dataclass(slots=True)
class HostedInterfaceNamespace:
    config: InterfaceHostServiceConfig
    app: InterfaceHostServiceApp


@dataclass(frozen=True, slots=True)
class PersistedHostedNamespaceConfig:
    namespace: str
    host_label: str
    endpoint: str | None = None
    environment_config_id: UUID | None = None

    @classmethod
    def from_config(
        cls, config: InterfaceHostServiceConfig
    ) -> "PersistedHostedNamespaceConfig":
        return cls(
            namespace=config.namespace,
            host_label=config.host_label,
            endpoint=config.endpoint,
            environment_config_id=config.environment_config_id,
        )

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> "PersistedHostedNamespaceConfig":
        raw_environment_config_id = payload.get("environment_config_id")
        environment_config_id = (
            UUID(str(raw_environment_config_id))
            if isinstance(raw_environment_config_id, str)
            and raw_environment_config_id.strip()
            else None
        )
        return cls(
            namespace=str(payload["namespace"]),
            host_label=str(payload["host_label"]),
            endpoint=(
                str(payload["endpoint"])
                if isinstance(payload.get("endpoint"), str)
                and str(payload["endpoint"]).strip()
                else None
            ),
            environment_config_id=environment_config_id,
        )

    def to_json(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "host_label": self.host_label,
            "endpoint": self.endpoint,
            "environment_config_id": (
                str(self.environment_config_id)
                if self.environment_config_id is not None
                else None
            ),
        }

    def to_config(
        self,
        *,
        base_config: InterfaceHostServiceConfig,
    ) -> InterfaceHostServiceConfig:
        return build_namespaced_service_config(
            base_config,
            namespace=self.namespace,
            host_label=self.host_label,
            endpoint=self.endpoint,
            environment_config_id=self.environment_config_id,
        )


@dataclass(frozen=True, slots=True)
class PersistedWorkspaceSessionState:
    namespace: str
    selected_workspace_root: str | None = None
    joined_workspace_root: str | None = None
    selected_runtime_focus_section_key: str | None = None
    selected_runtime_focus_observable_id: UUID | None = None

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> "PersistedWorkspaceSessionState":
        return cls(
            namespace=str(payload["namespace"]),
            selected_workspace_root=(
                str(payload["selected_workspace_root"])
                if isinstance(payload.get("selected_workspace_root"), str)
                and str(payload["selected_workspace_root"]).strip()
                else None
            ),
            joined_workspace_root=(
                str(payload["joined_workspace_root"])
                if isinstance(payload.get("joined_workspace_root"), str)
                and str(payload["joined_workspace_root"]).strip()
                else None
            ),
            selected_runtime_focus_section_key=(
                str(payload["selected_runtime_focus_section_key"])
                if isinstance(payload.get("selected_runtime_focus_section_key"), str)
                and str(payload["selected_runtime_focus_section_key"]).strip()
                else None
            ),
            selected_runtime_focus_observable_id=(
                UUID(str(payload["selected_runtime_focus_observable_id"]))
                if isinstance(payload.get("selected_runtime_focus_observable_id"), str)
                and str(payload["selected_runtime_focus_observable_id"]).strip()
                else None
            ),
        )

    def to_json(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "selected_workspace_root": self.selected_workspace_root,
            "joined_workspace_root": self.joined_workspace_root,
            "selected_runtime_focus_section_key": self.selected_runtime_focus_section_key,
            "selected_runtime_focus_observable_id": (
                str(self.selected_runtime_focus_observable_id)
                if self.selected_runtime_focus_observable_id is not None
                else None
            ),
        }


class InterfaceNamespaceRegistry:
    def __init__(
        self,
        *,
        bundle_factory: InterfaceHostServiceBundleFactory | None = None,
        base_config: InterfaceHostServiceConfig | None = None,
        state_home: Path | None = None,
    ) -> None:
        self._bundle_factory = bundle_factory
        self._base_config = base_config
        self._state_home = (
            state_home.expanduser().resolve()
            if state_home is not None
            else (base_config.state_home.resolve() if base_config is not None else None)
        )
        self._entries: dict[str, HostedInterfaceNamespace] = {}
        self._entry_locks: dict[str, asyncio.Lock] = {}
        self._refresh_locks: dict[str, asyncio.Lock] = {}
        self._persisted_configs = self._load_persisted_configs()
        self._persisted_workspace_sessions = self._load_persisted_workspace_sessions()

    async def ensure_namespace(
        self,
        *,
        config: InterfaceHostServiceConfig,
    ) -> InterfaceHostServiceState:
        entry = await self._ensure_entry(config=config)
        self._remember_workspace_session(
            namespace=config.namespace, state=entry.app.state()
        )
        await self._sync_workspace_sessions()
        return entry.app.state()

    def list_namespaces(self) -> tuple[InterfaceHostedNamespaceState, ...]:
        namespaces = set(self._persisted_configs) | set(self._entries)
        summaries: list[InterfaceHostedNamespaceState] = []
        for namespace in sorted(namespaces):
            entry = self._entries.get(namespace)
            if entry is not None:
                summaries.append(_namespace_summary(entry.config, entry.app.state()))
                continue
            persisted = self._persisted_configs.get(namespace)
            if persisted is None:
                continue
            summaries.append(_pending_namespace_summary(persisted))
        return tuple(summaries)

    async def status(
        self,
        *,
        namespace: str,
        refresh: bool = False,
    ) -> InterfaceHostServiceState:
        if not refresh:
            entry = await self._require_entry(namespace=namespace)
            return entry.app.state()
        lock = self._refresh_locks.setdefault(namespace, asyncio.Lock())
        async with lock:
            entry = await self._require_entry(namespace=namespace)
            return await entry.app.refresh_state()

    async def follow_namespace(
        self,
        *,
        namespace: str,
        poll_interval_s: float,
        last_state: InterfaceHostServiceState | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> AsyncIterator[InterfaceHostServiceState]:
        entry = await self._require_entry(namespace=namespace)
        current_state = last_state or await self.status(
            namespace=namespace, refresh=True
        )
        current_signature = _follow_signature(current_state)
        current_revision = entry.app.state_revision()
        while True:
            if should_stop is not None and should_stop():
                break
            state_changed = await entry.app.wait_for_state_change(
                after_revision=current_revision,
                timeout_s=max(poll_interval_s, 0.25),
            )
            if should_stop is not None and should_stop():
                break
            if state_changed:
                state = entry.app.state()
            else:
                state = await self.status(namespace=namespace, refresh=True)
            current_revision = entry.app.state_revision()
            signature = _follow_signature(state)
            if signature != current_signature:
                yield state
                current_state = state
                current_signature = signature

    async def perform_action(
        self,
        *,
        namespace: str,
        pane_ref: str | None = None,
        action_key: str,
        action_target: InterfaceActionTarget | None = None,
        payload: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        if action_target is not None:
            state = await entry.app.perform_action(
                pane_ref=pane_ref,
                action_key=action_key,
                action_target=action_target,
                payload=payload,
            )
        else:
            state = await entry.app.perform_action(
                pane_ref=pane_ref,
                action_key=action_key,
                payload=payload,
            )
        if action_key in {
            "join_selected_workspace",
            "ensure_selected_workspace_running",
            "leave_selected_workspace",
            "recover_selected_workspace",
            "stop_selected_workspace",
        }:
            self._remember_workspace_session(namespace=namespace, state=state)
            await self._sync_workspace_sessions()
            return entry.app.state()
        return state

    async def invoke_api(
        self,
        *,
        namespace: str,
        endpoint_ref: str,
        discriminant: str,
        request_payload: dict[str, object],
        invocation_context: dict[str, object] | None = None,
    ) -> ServiceOperationResponse:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.invoke_api(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
            invocation_context=invocation_context,
        )

    async def open_api_stream(
        self,
        *,
        namespace: str,
        endpoint_ref: str,
        discriminant: str,
        request_payload: dict[str, object],
    ) -> ServiceHostDuplexRequestHandle:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.open_api_stream(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
        )

    async def select_control_plane_step(
        self,
        *,
        namespace: str,
        step_id: str | None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.select_control_plane_step(step_id=step_id)

    async def select_control_plane_profile(
        self,
        *,
        namespace: str,
        profile_id: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.select_control_plane_profile(profile_id=profile_id)

    async def select_control_plane_workspace(
        self,
        *,
        namespace: str,
        workspace_root: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.select_control_plane_workspace(
            workspace_root=workspace_root
        )
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def select_control_plane_semantic_package(
        self,
        *,
        namespace: str,
        selector_key: str | None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.select_control_plane_semantic_package(
            selector_key=selector_key
        )

    async def select_control_plane_runtime_layout(
        self,
        *,
        namespace: str,
        layout_config_id: UUID | None = None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.select_control_plane_runtime_layout(
            layout_config_id=layout_config_id,
        )
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def activate_control_plane_runtime_focus(
        self,
        *,
        namespace: str,
        representation_id: UUID | None = None,
        layout_config_id: UUID | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | None = None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.activate_control_plane_runtime_focus(
            representation_id=representation_id,
            layout_config_id=layout_config_id,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
        )
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def request_interface_window_layout(
        self,
        *,
        namespace: str,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
        window_key: str | None = None,
        layout_config_id: UUID | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | None = None,
        representation_id: UUID | None = None,
        requested_by_service: str | None = None,
        requested_by_operation: str | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.request_interface_window_layout(
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
            window_key=window_key,
            layout_config_id=layout_config_id,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
            representation_id=representation_id,
            requested_by_service=requested_by_service,
            requested_by_operation=requested_by_operation,
            reason=reason,
            idempotency_key=idempotency_key,
        )
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def apply_attention_layout_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_layout_transition_id: UUID | None,
        topology_transition_id: UUID | None = None,
        section_states: Sequence[AttentionLayoutIntentSection],
        source_ref: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InterfaceHostAttentionLayoutTransitionResult:
        entry = await self._require_entry(namespace=namespace)
        result = await entry.app.apply_attention_layout_transition(
            client_intent_id=client_intent_id,
            expected_previous_layout_transition_id=(
                expected_previous_layout_transition_id
            ),
            topology_transition_id=topology_transition_id,
            section_states=section_states,
            source_ref=source_ref,
            metadata=metadata,
        )
        self._remember_workspace_session(namespace=namespace, state=result.state)
        await self._sync_workspace_sessions()
        return result

    async def apply_attention_layout_topology_transition(
        self,
        *,
        namespace: str,
        client_intent_id: str,
        expected_previous_topology_transition_id: UUID | None,
        section_states: Sequence[AttentionLayoutTopologyIntentSection],
        source_ref: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InterfaceHostAttentionLayoutTopologyTransitionResult:
        entry = await self._require_entry(namespace=namespace)
        result = await entry.app.apply_attention_layout_topology_transition(
            client_intent_id=client_intent_id,
            expected_previous_topology_transition_id=(
                expected_previous_topology_transition_id
            ),
            section_states=section_states,
            source_ref=source_ref,
            metadata=metadata,
        )
        self._remember_workspace_session(namespace=namespace, state=result.state)
        await self._sync_workspace_sessions()
        return result

    async def admit_environment_actor(
        self,
        *,
        namespace: str,
        environment_profile_id: UUID,
        actor_config_id: UUID,
        class_instance_identity_id: UUID,
        environment_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: tuple[UUID, ...] = (),
        requested_role_config_names: tuple[str, ...] = (),
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.admit_environment_actor(
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            environment_id=environment_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids,
            requested_role_config_names=requested_role_config_names,
            reason=reason,
            evidence=evidence,
        )

    async def enter_environment(
        self,
        *,
        namespace: str,
        environment_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        actor_config_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: tuple[UUID, ...] = (),
        requested_role_config_names: tuple[str, ...] = (),
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        environment_session_id: UUID | None = None,
        environment_session_config_id: UUID | None = None,
        session_key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnvironmentEntryResult:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.enter_environment(
            environment_id=environment_id,
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids,
            requested_role_config_names=requested_role_config_names,
            environment_admission_receipt=environment_admission_receipt,
            environment_session_id=environment_session_id,
            environment_session_config_id=environment_session_config_id,
            session_key=session_key,
            title=title,
            description=description,
            purpose=purpose,
            source_kind=source_kind,
            source_ref=source_ref,
            reason=reason,
            evidence=evidence,
        )

    async def enter_app_screen(
        self,
        *,
        namespace: str,
        app_package_id: UUID,
        app_package_branch_id: UUID,
        app_package_object_instance_graph_commit_id: UUID,
        app_config_screen_config_id: UUID,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
        committed_app_screen_resolver: object | None = None,
    ) -> InterfaceAppScreenEntryResult:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.enter_app_screen(
            app_package_id=app_package_id,
            app_package_branch_id=app_package_branch_id,
            app_package_object_instance_graph_commit_id=(
                app_package_object_instance_graph_commit_id
            ),
            app_config_screen_config_id=app_config_screen_config_id,
            reason=reason,
            evidence=evidence,
            committed_app_screen_resolver=committed_app_screen_resolver,
        )

    async def join_environment_session(
        self,
        *,
        namespace: str,
        environment_session_id: UUID,
        environment_profile_id: UUID | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnvironmentSessionJoinResult:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.join_environment_session(
            environment_session_id=environment_session_id,
            environment_profile_id=environment_profile_id,
            environment_admission_receipt=environment_admission_receipt,
            reason=reason,
            evidence=evidence,
        )

    async def select_environment_navigation_target(
        self,
        *,
        namespace: str,
        environment_navigation_context_id: UUID | None = None,
        selected_process_id: UUID | None = None,
        selected_thread_id: UUID | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnvironmentNavigationSelectResult:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.select_environment_navigation_target(
            environment_navigation_context_id=environment_navigation_context_id,
            selected_process_id=selected_process_id,
            selected_thread_id=selected_thread_id,
            reason=reason,
            evidence=evidence,
        )

    async def resolve_experience_lens(
        self,
        *,
        namespace: str,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None,
        environment_navigation_context: EnvironmentNavigationContextView | None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
        experience_identity_session_config_id: UUID | None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.resolve_experience_lens(
            environment_session_join_receipt=environment_session_join_receipt,
            environment_navigation_context=environment_navigation_context,
            experience_actor_admission=experience_actor_admission,
            experience_identity_session_config_id=experience_identity_session_config_id,
            reason=reason,
            evidence=evidence,
        )

    async def ensure_selected_workspace_running(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.ensure_selected_workspace_running()
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def join_selected_workspace(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.join_selected_workspace()
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def leave_selected_workspace(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.leave_selected_workspace()
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def recover_selected_workspace(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.recover_selected_workspace()
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def stop_selected_workspace(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        state = await entry.app.stop_selected_workspace()
        self._remember_workspace_session(namespace=namespace, state=state)
        await self._sync_workspace_sessions()
        return entry.app.state()

    async def report_renderer_capabilities(
        self,
        *,
        namespace: str,
        renderer_capabilities: InterfaceHostServiceRendererCapabilitiesState,
    ) -> InterfaceHostServiceState:
        entry = await self._require_entry(namespace=namespace)
        return await entry.app.report_renderer_capabilities(
            renderer_capabilities=renderer_capabilities,
        )

    async def stop_namespace(self, *, namespace: str) -> InterfaceHostedNamespaceState:
        persisted = self._persisted_configs.get(namespace)
        entry = self._entries.pop(namespace, None)
        if entry is None:
            if persisted is None:
                raise KeyError(f"Unknown namespace: {namespace}")
            self._forget_persisted_config(namespace=namespace)
            self._forget_workspace_session(namespace=namespace)
            await self._sync_workspace_sessions()
            return InterfaceHostedNamespaceState(
                namespace=namespace,
                host_label=persisted.host_label,
                started=False,
                environment_config_id=persisted.environment_config_id,
                warnings=("daemon_rehydration_pending",),
            )
        self._forget_persisted_config(namespace=namespace)
        self._forget_workspace_session(namespace=namespace)
        state = entry.app.state()
        await entry.app.close()
        await self._sync_workspace_sessions()
        return InterfaceHostedNamespaceState(
            namespace=namespace,
            host_label=entry.config.host_label,
            started=False,
            actor_id=state.transport.actor_id,
            interface_id=state.transport.interface_id,
            interface_session_id=state.transport.interface_session_id,
            environment_id=state.environment_id,
            environment_config_id=state.environment_config_id,
            warnings=state.warnings,
        )

    async def close(self) -> None:
        entries = tuple(self._entries.values())
        self._entries.clear()
        self._refresh_locks.clear()
        for entry in entries:
            await entry.app.close()

    async def _require_entry(self, *, namespace: str) -> HostedInterfaceNamespace:
        entry = self._entries.get(namespace)
        if entry is not None:
            return entry
        lock = self._entry_locks.get(namespace)
        if lock is not None and lock.locked():
            async with lock:
                entry = self._entries.get(namespace)
                if entry is not None:
                    return entry
        persisted = self._persisted_configs.get(namespace)
        if persisted is None or self._base_config is None:
            raise KeyError(f"Unknown namespace: {namespace}")
        logger.info(
            "aware_interface_service rehydrating namespace=%s from persisted descriptor",
            namespace,
        )
        return await self._ensure_entry(
            config=persisted.to_config(base_config=self._base_config)
        )

    async def _ensure_entry(
        self,
        *,
        config: InterfaceHostServiceConfig,
    ) -> HostedInterfaceNamespace:
        lock = self._entry_locks.setdefault(config.namespace, asyncio.Lock())
        async with lock:
            return await self._ensure_entry_locked(config=config)

    async def _ensure_entry_locked(
        self,
        *,
        config: InterfaceHostServiceConfig,
    ) -> HostedInterfaceNamespace:
        existing = self._entries.get(config.namespace)
        if existing is not None:
            existing_state = existing.app.state()
            if not _should_rebind_namespace(existing_state):
                return existing
            await existing.app.close()
            self._entries.pop(config.namespace, None)

        app = await InterfaceHostServiceApp.create(
            config=config,
            bundle_factory=self._bundle_factory,
        )
        await app.start()
        entry = HostedInterfaceNamespace(config=config, app=app)
        self._entries[config.namespace] = entry
        self._remember_persisted_config(config=config)
        await self._sync_workspace_sessions()
        return entry

    def _remember_persisted_config(self, *, config: InterfaceHostServiceConfig) -> None:
        persisted = PersistedHostedNamespaceConfig.from_config(config)
        previous = self._persisted_configs.get(config.namespace)
        if previous == persisted:
            return
        self._persisted_configs[config.namespace] = persisted
        self._write_persisted_configs()

    def _forget_persisted_config(self, *, namespace: str) -> None:
        if self._persisted_configs.pop(namespace, None) is None:
            return
        self._write_persisted_configs()

    def _remember_workspace_session(
        self,
        *,
        namespace: str,
        state: InterfaceHostServiceState,
    ) -> None:
        runtime_state = getattr(state, "runtime", None)
        selected_workspace_root = (
            state.selected_workspace.workspace_root.as_posix()
            if state.selected_workspace is not None
            else None
        )
        joined_workspace_root = (
            selected_workspace_root
            if (
                state.selected_workspace is not None
                and state.selected_workspace.lifecycle is not None
                and state.selected_workspace.lifecycle.joined
            )
            else None
        )
        next_state = PersistedWorkspaceSessionState(
            namespace=namespace,
            selected_workspace_root=selected_workspace_root,
            joined_workspace_root=joined_workspace_root,
            selected_runtime_focus_section_key=(
                runtime_state.active_focus.section_key
                if runtime_state is not None and runtime_state.active_focus is not None
                else None
            ),
            selected_runtime_focus_observable_id=(
                runtime_state.active_focus.observable_id
                if runtime_state is not None and runtime_state.active_focus is not None
                else None
            ),
        )
        if (
            next_state.selected_workspace_root is None
            and next_state.joined_workspace_root is None
        ):
            self._forget_workspace_session(namespace=namespace)
            return
        previous = self._persisted_workspace_sessions.get(namespace)
        if previous == next_state:
            return
        self._persisted_workspace_sessions[namespace] = next_state
        self._write_persisted_workspace_sessions()

    def _forget_workspace_session(self, *, namespace: str) -> None:
        if self._persisted_workspace_sessions.pop(namespace, None) is None:
            return
        self._write_persisted_workspace_sessions()

    def _persisted_config_path(self) -> Path | None:
        if self._state_home is None:
            return None
        return (self._state_home / "hosted-namespaces.json").resolve()

    def _workspace_session_path(self) -> Path | None:
        if self._state_home is None:
            return None
        return (self._state_home / "workspace-sessions.json").resolve()

    def _load_persisted_configs(self) -> dict[str, PersistedHostedNamespaceConfig]:
        path = self._persisted_config_path()
        if path is None or not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(
                "aware_interface_service failed to load namespace descriptors: %s", exc
            )
            return {}
        if not isinstance(payload, list):
            logger.warning(
                "aware_interface_service namespace descriptor file is not a list: %s",
                path,
            )
            return {}
        records: dict[str, PersistedHostedNamespaceConfig] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                record = PersistedHostedNamespaceConfig.from_json(item)
            except Exception as exc:
                logger.warning(
                    "aware_interface_service skipping invalid namespace descriptor %s: %s",
                    item,
                    exc,
                )
                continue
            records[record.namespace] = record
        return records

    def _load_persisted_workspace_sessions(
        self,
    ) -> dict[str, PersistedWorkspaceSessionState]:
        path = self._workspace_session_path()
        if path is None or not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(
                "aware_interface_service failed to load workspace sessions: %s", exc
            )
            return {}
        if not isinstance(payload, list):
            logger.warning(
                "aware_interface_service workspace session file is not a list: %s", path
            )
            return {}
        records: dict[str, PersistedWorkspaceSessionState] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                record = PersistedWorkspaceSessionState.from_json(item)
            except Exception as exc:
                logger.warning(
                    "aware_interface_service skipping invalid workspace session %s: %s",
                    item,
                    exc,
                )
                continue
            records[record.namespace] = record
        return records

    def _write_persisted_configs(self) -> None:
        path = self._persisted_config_path()
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            self._persisted_configs[namespace].to_json()
            for namespace in sorted(self._persisted_configs)
        ]
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _write_persisted_workspace_sessions(self) -> None:
        path = self._workspace_session_path()
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            self._persisted_workspace_sessions[namespace].to_json()
            for namespace in sorted(self._persisted_workspace_sessions)
        ]
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _attached_namespace_counts_by_workspace(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for session in self._persisted_workspace_sessions.values():
            joined_workspace_root = session.joined_workspace_root
            if joined_workspace_root is None:
                continue
            normalized = Path(joined_workspace_root).expanduser().resolve().as_posix()
            counts[normalized] = counts.get(normalized, 0) + 1
        return counts

    async def _sync_workspace_sessions(self) -> None:
        counts = self._attached_namespace_counts_by_workspace()
        for namespace, entry in tuple(self._entries.items()):
            session = self._persisted_workspace_sessions.get(namespace)
            selected_workspace_root = (
                Path(session.selected_workspace_root).expanduser().resolve()
                if session is not None and session.selected_workspace_root is not None
                else None
            )
            joined_workspace_root = (
                Path(session.joined_workspace_root).expanduser().resolve()
                if session is not None and session.joined_workspace_root is not None
                else None
            )
            selected_runtime_focus_section_key = (
                session.selected_runtime_focus_section_key
                if session is not None
                else None
            )
            selected_runtime_focus_observable_id = (
                session.selected_runtime_focus_observable_id
                if session is not None
                else None
            )
            await entry.app.apply_workspace_session(
                selected_workspace_root=selected_workspace_root,
                joined_workspace_root=joined_workspace_root,
                selected_runtime_focus_section_key=selected_runtime_focus_section_key,
                selected_runtime_focus_observable_id=selected_runtime_focus_observable_id,
                attached_namespace_counts_by_workspace=counts,
            )


def _namespace_summary(
    config: InterfaceHostServiceConfig,
    state: InterfaceHostServiceState,
) -> InterfaceHostedNamespaceState:
    return InterfaceHostedNamespaceState(
        namespace=config.namespace,
        host_label=config.host_label,
        started=state.started,
        actor_id=state.transport.actor_id,
        interface_id=state.transport.interface_id,
        interface_session_id=state.transport.interface_session_id,
        environment_id=state.environment_id,
        environment_config_id=state.environment_config_id,
        warnings=state.warnings,
    )


def _pending_namespace_summary(
    config: PersistedHostedNamespaceConfig,
) -> InterfaceHostedNamespaceState:
    return InterfaceHostedNamespaceState(
        namespace=config.namespace,
        host_label=config.host_label,
        started=False,
        environment_config_id=config.environment_config_id,
        warnings=("daemon_rehydration_pending",),
    )


def _follow_signature(state: InterfaceHostServiceState) -> InterfaceHostServiceState:
    return replace(
        state,
        local_service_host=(
            replace(state.local_service_host, last_checked_at=None)
            if state.local_service_host is not None
            else None
        ),
        local_node_runtime=(
            replace(state.local_node_runtime, updated_at=None)
            if state.local_node_runtime is not None
            else None
        ),
        current_operation=(
            replace(state.current_operation, updated_at=None)
            if state.current_operation is not None
            else None
        ),
    )


def _should_rebind_namespace(state: InterfaceHostServiceState) -> bool:
    warnings = set(state.warnings)
    return {
        "transport_unbound",
        "runtime_unbound",
        "host_runtime_unbound",
    }.issubset(warnings)


__all__ = [
    "HostedInterfaceNamespace",
    "InterfaceNamespaceRegistry",
]
