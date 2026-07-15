from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext

from aware_experience_service.actor_action_policy_service import (
    ExperienceInvocationActionRolePolicyBackend,
    ExperienceInvocationActionRolePolicySpec,
)
from aware_experience_service.actor_admission_service import (
    ExperienceActorConfigRoleAdmissionBindingSpec,
)


class ExperienceInvocationActionTargetSpec(BaseModel):
    experience_name: str
    projection_experience_view_instance_id: UUID
    view_invocation_action_config_id: UUID
    experience_invocation_action_config_id: UUID
    action_key: str | None = None


class InvokeExperienceViewInvocationActionPreflightRequestSpec(BaseModel):
    request_id: UUID | None = None
    experience_name: str
    projection_experience_view_instance_id: UUID
    view_invocation_action_config_id: UUID
    invocation_key: UUID
    actor_id: UUID | None = None
    admitted_actor_role_bindings: list[
        ExperienceActorConfigRoleAdmissionBindingSpec
    ] = Field(default_factory=list)
    admission_evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceInvocationActionAdmissionPreflightSpec(BaseModel):
    accepted: bool = False
    status: str
    actor_id: UUID | None = None
    experience_invocation_action_config_id: UUID | None = None
    action_key: str | None = None
    matched_role_config_id: UUID | None = None
    matched_role_config_name: str | None = None
    matched_actor_role_id: UUID | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceInvocationActionTargetBackend(Protocol):
    async def resolve_invocation_action_target(
        self,
        *,
        experience_name: str,
        projection_experience_view_instance_id: UUID,
        view_invocation_action_config_id: UUID,
    ) -> ExperienceInvocationActionTargetSpec | None: ...


async def preflight_experience_view_invocation_action(
    *,
    request: InvokeExperienceViewInvocationActionPreflightRequestSpec,
    host_context: ServiceApiHostContext,
    target_backend: ExperienceInvocationActionTargetBackend | None = None,
    policy_backend: ExperienceInvocationActionRolePolicyBackend | None = None,
) -> ExperienceInvocationActionAdmissionPreflightSpec:
    base_evidence: dict[str, Any] = {
        "source": "aware_experience_service.invocation_action_admission_preflight",
        "host_actor_id": str(host_context.operation_context.actor_id),
        "experience_name": request.experience_name,
        "projection_experience_view_instance_id": str(
            request.projection_experience_view_instance_id
        ),
        "view_invocation_action_config_id": str(
            request.view_invocation_action_config_id
        ),
        **dict(request.admission_evidence),
    }

    if not request.experience_name.strip():
        return _blocked_preflight(
            request=request,
            reason="experience_name_missing",
            blockers=["experience_name_missing"],
            evidence=base_evidence,
        )
    if request.actor_id is None:
        return _blocked_preflight(
            request=request,
            reason="actor_id_missing",
            blockers=["actor_id_missing"],
            evidence=base_evidence,
        )
    if not request.admitted_actor_role_bindings:
        return _blocked_preflight(
            request=request,
            reason="admitted_actor_role_bindings_missing",
            blockers=["admitted_actor_role_bindings_missing"],
            evidence=base_evidence,
        )
    if target_backend is None:
        return _blocked_preflight(
            request=request,
            reason="experience_invocation_action_target_backend_unavailable",
            blockers=["experience_invocation_action_target_backend_unavailable"],
            evidence=base_evidence,
        )
    if policy_backend is None:
        return _blocked_preflight(
            request=request,
            reason="experience_invocation_action_role_policy_backend_unavailable",
            blockers=["experience_invocation_action_role_policy_backend_unavailable"],
            evidence=base_evidence,
        )

    actor_bindings = _actor_bindings(
        actor_id=request.actor_id,
        bindings=request.admitted_actor_role_bindings,
    )
    if not actor_bindings:
        return _blocked_preflight(
            request=request,
            reason="admitted_actor_role_actor_mismatch",
            blockers=["admitted_actor_role_actor_mismatch"],
            evidence={
                **base_evidence,
                "admitted_actor_role_binding_count": len(
                    request.admitted_actor_role_bindings
                ),
            },
        )

    target = await target_backend.resolve_invocation_action_target(
        experience_name=request.experience_name,
        projection_experience_view_instance_id=(
            request.projection_experience_view_instance_id
        ),
        view_invocation_action_config_id=request.view_invocation_action_config_id,
    )
    if target is None:
        return _blocked_preflight(
            request=request,
            reason="experience_invocation_action_target_not_found",
            blockers=["experience_invocation_action_target_not_found"],
            evidence=base_evidence,
        )

    policies = tuple(
        await policy_backend.resolve_invocation_action_role_policies(
            experience_name=request.experience_name,
            experience_invocation_action_config_id=(
                target.experience_invocation_action_config_id
            ),
            action_key=target.action_key,
        )
    )
    if not policies:
        return _blocked_preflight(
            request=request,
            reason="experience_invocation_action_role_policy_not_found",
            blockers=["experience_invocation_action_role_policy_not_found"],
            evidence={
                **base_evidence,
                "experience_invocation_action_config_id": str(
                    target.experience_invocation_action_config_id
                ),
                "action_key": target.action_key,
            },
            target=target,
        )

    match = _first_policy_match(bindings=actor_bindings, policies=policies)
    if match is None:
        return _blocked_preflight(
            request=request,
            reason="admitted_actor_role_not_authorized_for_action",
            blockers=["admitted_actor_role_not_authorized_for_action"],
            evidence={
                **base_evidence,
                "experience_invocation_action_config_id": str(
                    target.experience_invocation_action_config_id
                ),
                "action_key": target.action_key,
                "allowed_role_config_ids": [
                    str(policy.role_config_id) for policy in policies
                ],
                "admitted_role_config_ids": [
                    str(binding.role_config_id) for binding in actor_bindings
                ],
            },
            target=target,
        )

    binding, policy = match
    return ExperienceInvocationActionAdmissionPreflightSpec(
        accepted=True,
        status="authorized",
        actor_id=request.actor_id,
        experience_invocation_action_config_id=(
            target.experience_invocation_action_config_id
        ),
        action_key=target.action_key,
        matched_role_config_id=binding.role_config_id,
        matched_role_config_name=binding.role_config_name or policy.role_config_name,
        matched_actor_role_id=binding.actor_role_id,
        evidence={
            **base_evidence,
            "experience_invocation_action_config_id": str(
                target.experience_invocation_action_config_id
            ),
            "action_key": target.action_key,
            "allowed_policy_count": len(policies),
            "admitted_actor_role_binding_count": len(actor_bindings),
            "matched_actor_config_role_config_id": str(
                binding.actor_config_role_config_id
            ),
            "matched_role_policy_id": (
                str(policy.role_policy_id)
                if policy.role_policy_id is not None
                else None
            ),
        },
    )


def _actor_bindings(
    *,
    actor_id: UUID,
    bindings: Sequence[ExperienceActorConfigRoleAdmissionBindingSpec],
) -> tuple[ExperienceActorConfigRoleAdmissionBindingSpec, ...]:
    return tuple(binding for binding in bindings if binding.actor_id == actor_id)


def _first_policy_match(
    *,
    bindings: Sequence[ExperienceActorConfigRoleAdmissionBindingSpec],
    policies: Sequence[ExperienceInvocationActionRolePolicySpec],
) -> (
    tuple[
        ExperienceActorConfigRoleAdmissionBindingSpec,
        ExperienceInvocationActionRolePolicySpec,
    ]
    | None
):
    policies_by_role_config_id = {policy.role_config_id: policy for policy in policies}
    for binding in bindings:
        policy = policies_by_role_config_id.get(binding.role_config_id)
        if policy is not None:
            return binding, policy
    return None


def _blocked_preflight(
    *,
    request: InvokeExperienceViewInvocationActionPreflightRequestSpec,
    reason: str,
    blockers: list[str],
    evidence: dict[str, Any],
    target: ExperienceInvocationActionTargetSpec | None = None,
) -> ExperienceInvocationActionAdmissionPreflightSpec:
    return ExperienceInvocationActionAdmissionPreflightSpec(
        accepted=False,
        status=reason,
        actor_id=request.actor_id,
        experience_invocation_action_config_id=(
            target.experience_invocation_action_config_id
            if target is not None
            else None
        ),
        action_key=target.action_key if target is not None else None,
        blockers=blockers,
        evidence=evidence,
    )


__all__ = [
    "ExperienceInvocationActionAdmissionPreflightSpec",
    "ExperienceInvocationActionTargetBackend",
    "ExperienceInvocationActionTargetSpec",
    "InvokeExperienceViewInvocationActionPreflightRequestSpec",
    "preflight_experience_view_invocation_action",
]
