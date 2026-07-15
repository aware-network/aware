from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext


class ExperienceInvocationActionRolePolicySpec(BaseModel):
    role_policy_id: UUID | None = None
    experience_invocation_action_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = None
    policy_key: str = "invoke"
    requirement_kind: str = "admitted_actor_role"
    description: str | None = None


class ExperienceInvocationActionRolePolicyResolutionSpec(BaseModel):
    experience_name: str
    experience_invocation_action_config_id: UUID
    action_key: str | None = None
    allowed_policies: list[ExperienceInvocationActionRolePolicySpec] = Field(
        default_factory=list
    )
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ResolveExperienceInvocationActionRolePolicyRequestSpec(BaseModel):
    request_id: UUID | None = None
    experience_name: str
    experience_invocation_action_config_id: UUID
    action_key: str | None = None


class ResolveExperienceInvocationActionRolePolicyResponseSpec(BaseModel):
    request_id: UUID | None = None
    success: bool = True
    error: str | None = None
    experience_name: str
    accepted: bool = False
    status: str
    resolution: ExperienceInvocationActionRolePolicyResolutionSpec


class ExperienceInvocationActionRolePolicyBackend(Protocol):
    async def resolve_invocation_action_role_policies(
        self,
        *,
        experience_name: str,
        experience_invocation_action_config_id: UUID,
        action_key: str | None,
    ) -> Sequence[ExperienceInvocationActionRolePolicySpec]: ...


async def resolve_experience_invocation_action_role_policy(
    *,
    request: ResolveExperienceInvocationActionRolePolicyRequestSpec,
    host_context: ServiceApiHostContext,
    policy_backend: ExperienceInvocationActionRolePolicyBackend | None = None,
) -> ResolveExperienceInvocationActionRolePolicyResponseSpec:
    base_evidence: dict[str, Any] = {
        "source": "aware_experience_service.invocation_action_role_policy",
        "actor_id": str(host_context.operation_context.actor_id),
        "experience_name": request.experience_name,
        "experience_invocation_action_config_id": str(
            request.experience_invocation_action_config_id
        ),
    }
    if request.action_key is not None:
        base_evidence["action_key"] = request.action_key

    if not request.experience_name.strip():
        return _blocked_response(
            request=request,
            reason="experience_name_missing",
            blockers=["experience_name_missing"],
            evidence=base_evidence,
        )

    if policy_backend is None:
        return _blocked_response(
            request=request,
            reason="experience_invocation_action_role_policy_backend_unavailable",
            blockers=["experience_invocation_action_role_policy_backend_unavailable"],
            evidence=base_evidence,
        )

    policies = tuple(
        await policy_backend.resolve_invocation_action_role_policies(
            experience_name=request.experience_name,
            experience_invocation_action_config_id=(
                request.experience_invocation_action_config_id
            ),
            action_key=request.action_key,
        )
    )
    if not policies:
        return _blocked_response(
            request=request,
            reason="experience_invocation_action_role_policy_not_found",
            blockers=["experience_invocation_action_role_policy_not_found"],
            evidence={
                **base_evidence,
                "allowed_policy_count": 0,
            },
        )

    resolution = ExperienceInvocationActionRolePolicyResolutionSpec(
        experience_name=request.experience_name,
        experience_invocation_action_config_id=(
            request.experience_invocation_action_config_id
        ),
        action_key=request.action_key,
        allowed_policies=list(policies),
        evidence={
            **base_evidence,
            "allowed_policy_count": len(policies),
        },
    )
    return ResolveExperienceInvocationActionRolePolicyResponseSpec(
        request_id=request.request_id,
        success=True,
        experience_name=request.experience_name,
        accepted=True,
        status="resolved",
        resolution=resolution,
    )


def _blocked_response(
    *,
    request: ResolveExperienceInvocationActionRolePolicyRequestSpec,
    reason: str,
    blockers: list[str],
    evidence: dict[str, Any],
) -> ResolveExperienceInvocationActionRolePolicyResponseSpec:
    resolution = ExperienceInvocationActionRolePolicyResolutionSpec(
        experience_name=request.experience_name,
        experience_invocation_action_config_id=(
            request.experience_invocation_action_config_id
        ),
        action_key=request.action_key,
        blockers=blockers,
        evidence=evidence,
    )
    return ResolveExperienceInvocationActionRolePolicyResponseSpec(
        request_id=request.request_id,
        success=False,
        error=reason,
        experience_name=request.experience_name,
        accepted=False,
        status="blocked",
        resolution=resolution,
    )


__all__ = [
    "ExperienceInvocationActionRolePolicyBackend",
    "ExperienceInvocationActionRolePolicyResolutionSpec",
    "ExperienceInvocationActionRolePolicySpec",
    "ResolveExperienceInvocationActionRolePolicyRequestSpec",
    "ResolveExperienceInvocationActionRolePolicyResponseSpec",
    "resolve_experience_invocation_action_role_policy",
]
