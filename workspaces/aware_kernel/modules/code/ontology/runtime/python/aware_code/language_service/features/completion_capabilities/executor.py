from __future__ import annotations

from aware_code.language_service.features.completion_capabilities.contracts import CompletionItemDict
from aware_code.language_service.features.completion_capabilities.environment import (
    collect_environment_context_completion_items,
)
from aware_code.language_service.features.completion_capabilities.experience import (
    collect_experience_context_completion_items,
)
from aware_code.language_service.features.completion_capabilities.role_actor import (
    collect_role_actor_context_completion_items,
)
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def collect_context_completion_items(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
) -> list[CompletionItemDict] | None:
    # Keep completion precedence stable with the monolith implementation.
    role_items = collect_role_actor_context_completion_items(
        snapshot=snapshot,
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
    )
    if role_items is not None:
        return role_items

    environment_items = collect_environment_context_completion_items(
        byte_offset=byte_offset,
        document_bytes=document_bytes,
    )
    if environment_items is not None:
        return environment_items

    return collect_experience_context_completion_items(
        snapshot=snapshot,
        uri=uri,
        byte_offset=byte_offset,
        document_bytes=document_bytes,
    )
