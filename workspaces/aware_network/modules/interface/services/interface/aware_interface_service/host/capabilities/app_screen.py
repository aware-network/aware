from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_experience_sdk import build_experience_sdk_client
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
)
from aware_interface.materialization.app_screen_entry import (
    CommittedAppScreenEntryRequest,
    CommittedAppScreenEntryResolution,
    resolve_committed_app_screen_entry,
)
from aware_interface_sdk.transport import InterfaceTransportSession
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex

from aware_interface_service.models import InterfaceAppScreenState


class CommittedAppScreenResolver(Protocol):
    async def resolve(
        self,
        request: CommittedAppScreenEntryRequest,
    ) -> CommittedAppScreenEntryResolution: ...


class ExperienceAppScreenActivator(Protocol):
    async def activate(
        self,
        *,
        experience_name: str,
        layout_binding_key: str,
        rationale: str,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class MetaCommittedAppScreenResolver:
    index: MetaGraphRuntimeIndex

    async def resolve(
        self,
        request: CommittedAppScreenEntryRequest,
    ) -> CommittedAppScreenEntryResolution:
        return await resolve_committed_app_screen_entry(
            index=self.index,
            request=request,
        )


@dataclass(frozen=True, slots=True)
class ServiceApiExperienceAppScreenActivator:
    transport_session: InterfaceTransportSession

    async def activate(
        self,
        *,
        experience_name: str,
        layout_binding_key: str,
        rationale: str,
    ) -> object:
        client = build_experience_sdk_client(
            AwareExperienceServiceApiClient(self.transport_session.client)
        )
        return await client.activate_layout_graph_binding(
            ActivateExperienceLayoutGraphBindingRequest(
                experience_name=experience_name,
                layout_binding_key=layout_binding_key,
                rationale=rationale,
            )
        )


def app_screen_state_from_resolution(
    *,
    resolution: CommittedAppScreenEntryResolution,
    reason: str | None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> InterfaceAppScreenState:
    return InterfaceAppScreenState(
        status="resolved",
        accepted=True,
        app_package_id=resolution.app_package_id,
        app_package_branch_id=resolution.app_package_branch_id,
        app_package_object_instance_graph_commit_id=(
            resolution.app_package_object_instance_graph_commit_id
        ),
        app_config_id=resolution.app_config_id,
        app_config_object_instance_graph_commit_id=(
            resolution.app_config_object_instance_graph_commit_id
        ),
        app_config_screen_config_id=resolution.app_config_screen_config_id,
        screen_key=resolution.screen_key,
        projection_experience_id=resolution.projection_experience_id,
        projection_experience_branch_id=(resolution.projection_experience_branch_id),
        projection_experience_head_commit_id=(
            resolution.projection_experience_head_commit_id
        ),
        projection_experience_layout_graph_binding_id=(
            resolution.projection_experience_layout_graph_binding_id
        ),
        experience_name=resolution.experience_name,
        layout_binding_key=resolution.layout_binding_key,
        reason=reason,
        updated_at=updated_at,
        evidence={
            "source": "interface_host_committed_app_screen",
            **_jsonish_mapping(evidence or {}),
        },
    )


def blocked_app_screen_state(
    *,
    blocker: str,
    app_package_id: UUID,
    app_package_branch_id: UUID,
    app_package_object_instance_graph_commit_id: UUID,
    app_config_screen_config_id: UUID,
    reason: str | None,
    updated_at: str,
    evidence: Mapping[str, object] | None = None,
) -> InterfaceAppScreenState:
    return InterfaceAppScreenState(
        status="blocked",
        accepted=False,
        app_package_id=app_package_id,
        app_package_branch_id=app_package_branch_id,
        app_package_object_instance_graph_commit_id=(
            app_package_object_instance_graph_commit_id
        ),
        app_config_screen_config_id=app_config_screen_config_id,
        blockers=(blocker,),
        error=blocker,
        reason=reason,
        updated_at=updated_at,
        evidence={
            "source": "interface_host_committed_app_screen",
            **_jsonish_mapping(evidence or {}),
        },
    )


def experience_activation_succeeded(response: object) -> bool:
    return bool(getattr(response, "success", False))


def experience_activation_error(response: object) -> str:
    return str(
        getattr(response, "error", None)
        or "experience_layout_graph_binding_activation_failed"
    )


def _jsonish_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _jsonish_value(item) for key, item in value.items()}


def _jsonish_value(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonish_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonish_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


__all__ = [
    "app_screen_state_from_resolution",
    "blocked_app_screen_state",
    "CommittedAppScreenResolver",
    "ExperienceAppScreenActivator",
    "experience_activation_error",
    "experience_activation_succeeded",
    "MetaCommittedAppScreenResolver",
    "ServiceApiExperienceAppScreenActivator",
]
