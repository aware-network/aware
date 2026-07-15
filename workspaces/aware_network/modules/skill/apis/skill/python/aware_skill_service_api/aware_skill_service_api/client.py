# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import SKILL__INVOKE__INVOKE_ENDPOINT_REF
from aware_skill_service_dto.skill.service_operation import SkillInvokeRequest, SkillInvokeResponse


class SkillInvokeCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def invoke(self, request: SkillInvokeRequest) -> SkillInvokeResponse:
        """Invoke one committed SkillPackage through the canonical Skill Service boundary."""
        return cast(
            SkillInvokeResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=SKILL__INVOKE__INVOKE_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class SkillApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.invoke = SkillInvokeCapabilityClient(client)


class AwareSkillServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.skill = SkillApiClient(client)


__all__ = [
    "AwareSkillServiceApiClient",
    "SkillApiClient",
    "SkillInvokeCapabilityClient",
]
