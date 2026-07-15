from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aware_experience.environment_profile.api_models import (
    UpsertExperienceEnvironmentProfileRequest,
)
from aware_experience.environment_profile.reactivity_policy import (
    build_environment_profile_reactivity_policy_bundle_request,
)
from aware_reactivity_sdk import ReactivitySdkClient


@dataclass(frozen=True, slots=True)
class ExperienceReactivitySdkPolicyBackend:
    sdk: ReactivitySdkClient

    async def ensure_environment_profile_policy_bundle(
        self,
        *,
        request: UpsertExperienceEnvironmentProfileRequest,
        profile_key: str,
        validate_only: bool = False,
        host_context: Any | None = None,
    ) -> dict[str, object]:
        _ = host_context
        response = await self.sdk.ensure_policy_bundle(
            build_environment_profile_reactivity_policy_bundle_request(
                request=request,
                profile_key=profile_key,
                validate_only=validate_only,
            )
        )
        if getattr(response, "accepted", True) is False or response.error:
            raise RuntimeError(
                response.error
                or f"Reactivity policy bundle ensure was rejected: {response.status}"
            )
        receipt = response.receipt
        return {
            "accepted": response.accepted,
            "status": response.status,
            "info": response.info,
            "error": response.error,
            "validate_only": response.validate_only,
            "bundle_id": str(receipt.bundle_id) if receipt is not None else None,
            "owner_ref": receipt.owner_ref if receipt is not None else None,
            "policy_key": receipt.policy_key if receipt is not None else None,
            "semantic_source_ref": (
                receipt.semantic_source_ref if receipt is not None else None
            ),
            "idempotency_key": (
                receipt.idempotency_key if receipt is not None else None
            ),
            "condition_config_count": (
                len(receipt.condition_configs) if receipt is not None else 0
            ),
            "event_config_count": (
                len(receipt.event_configs) if receipt is not None else 0
            ),
            "action_config_count": (
                len(receipt.action_configs) if receipt is not None else 0
            ),
            "event_condition_binding_count": (
                len(receipt.event_condition_bindings) if receipt is not None else 0
            ),
            "event_action_binding_count": (
                len(receipt.event_action_bindings) if receipt is not None else 0
            ),
            "condition_config_names": (
                [item.name for item in receipt.condition_configs]
                if receipt is not None
                else []
            ),
            "event_config_names": (
                [item.name for item in receipt.event_configs]
                if receipt is not None
                else []
            ),
            "action_config_names": (
                [item.name for item in receipt.action_configs]
                if receipt is not None
                else []
            ),
            "condition_config_ids": (
                [str(item.condition_config_id) for item in receipt.condition_configs]
                if receipt is not None
                else []
            ),
            "event_config_ids": (
                [str(item.event_config_id) for item in receipt.event_configs]
                if receipt is not None
                else []
            ),
            "action_config_ids": (
                [str(item.action_config_id) for item in receipt.action_configs]
                if receipt is not None
                else []
            ),
        }


__all__ = [
    "ExperienceReactivitySdkPolicyBackend",
]
