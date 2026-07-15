from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AttentionSdkClient:
    api_client: Any

    async def get_section_state(self, request: object) -> object:
        return await self._invoke(
            "get_section_state",
            "get_section_state",
            request,
        )

    async def activate_section_observable(self, request: object) -> object:
        return await self._invoke(
            "activate_section_observable",
            "activate_section_observable",
            request,
        )

    async def get_focus_scope_commits(self, request: object) -> object:
        return await self._invoke(
            "get_focus_scope_commits",
            "get_focus_scope_commits",
            request,
        )

    async def describe_attention_session(self, request: object) -> object:
        return await self._invoke(
            "describe_attention_session",
            "describe_attention_session",
            request,
        )

    async def start_attention_session(self, request: object) -> object:
        return await self._invoke(
            "start_attention_session",
            "start_attention_session",
            request,
        )

    async def mount_attention_session_layout(self, request: object) -> object:
        return await self._invoke(
            "mount_attention_session_layout",
            "mount_attention_session_layout",
            request,
        )

    async def mount_attention_session_section(self, request: object) -> object:
        return await self._invoke(
            "mount_attention_session_section",
            "mount_attention_session_section",
            request,
        )

    async def apply_session_layout_transition(self, request: object) -> object:
        return await self._invoke(
            "apply_session_layout_transition",
            "apply_session_layout_transition",
            request,
        )

    async def apply_session_layout_topology_transition(self, request: object) -> object:
        return await self._invoke(
            "apply_session_layout_topology_transition",
            "apply_session_layout_topology_transition",
            request,
        )

    async def describe_attention_transition(self, request: object) -> object:
        return await self._invoke(
            "describe_attention_transition",
            "describe_attention_transition",
            request,
        )

    async def list_attention_transitions(self, request: object) -> object:
        return await self._invoke(
            "list_attention_transitions",
            "list_attention_transitions",
            request,
        )

    async def validate_attention_transition(self, request: object) -> object:
        return await self._invoke(
            "validate_attention_transition",
            "validate_attention_transition",
            request,
        )

    async def get_runtime_mount(self, request: object) -> object:
        return await self._invoke(
            "get_runtime_mount",
            "get_runtime_mount",
            request,
        )

    async def watch_runtime_mount(self, request: object) -> object:
        return await self._invoke(
            "watch_runtime_mount",
            "watch_runtime_mount",
            request,
        )

    async def _invoke(
        self,
        capability_name: str,
        endpoint_name: str,
        request: object,
    ) -> object:
        capability = getattr(self.api_client.attention, capability_name)
        endpoint = getattr(capability, endpoint_name)
        return await endpoint(request)


def build_attention_sdk_client(api_client: Any) -> AttentionSdkClient:
    return AttentionSdkClient(api_client=api_client)
