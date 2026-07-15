from __future__ import annotations

"""Compatibility re-exports for compiler-owned attention stable-id formulas."""

from uuid import UUID

from aware_attention_ontology.stable_ids import (
    stable_focus_id as _stable_focus_id,
    stable_focus_scope_commit_id as _stable_focus_scope_commit_id,
    stable_focus_scope_request_id as _stable_focus_scope_request_id,
    stable_focus_scope_request_response_id as _stable_focus_scope_request_response_id,
    stable_layout_id as _stable_layout_id,
    stable_layout_section_id as _stable_layout_section_id,
    stable_section_focus_scope_id as _stable_section_focus_scope_id,
    stable_section_id as _stable_section_id,
)


def stable_focus_id(
    *, object_projection_graph_identity_id: UUID, focus_scope_id: UUID
) -> UUID:
    return _stable_focus_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        focus_scope_id=focus_scope_id,
    )


def stable_focus_scope_request_id(*, focus_scope_id: UUID, focus_id: UUID) -> UUID:
    return _stable_focus_scope_request_id(
        focus_scope_id=focus_scope_id,
        focus_id=focus_id,
    )


def stable_focus_scope_commit_id(
    *, focus_scope_id: UUID, focus_id: UUID, object_instance_graph_commit_id: UUID
) -> UUID:
    return _stable_focus_scope_commit_id(
        focus_scope_id=focus_scope_id,
        focus_id=focus_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )


def stable_focus_scope_request_response_id(*, focus_scope_request_id: UUID) -> UUID:
    return _stable_focus_scope_request_response_id(
        focus_scope_request_id=focus_scope_request_id
    )


def stable_layout_id(*, key: str | None = None, layout_key: str | None = None) -> UUID:
    canonical_key = key if key is not None else layout_key
    if canonical_key is None:
        raise TypeError("stable_layout_id requires `key` (or legacy `layout_key`)")
    return _stable_layout_id(key=canonical_key)


def stable_section_id(
    *, key: str | None = None, section_key: str | None = None
) -> UUID:
    canonical_key = key if key is not None else section_key
    if canonical_key is None:
        raise TypeError("stable_section_id requires `key` (or legacy `section_key`)")
    return _stable_section_id(key=canonical_key)


def stable_layout_section_id(*, layout_id: UUID, section_id: UUID) -> UUID:
    return _stable_layout_section_id(layout_id=layout_id, section_id=section_id)


def stable_section_focus_scope_id(*, section_id: UUID, focus_scope_id: UUID) -> UUID:
    return _stable_section_focus_scope_id(
        section_id=section_id, focus_scope_id=focus_scope_id
    )


__all__ = [
    "stable_focus_id",
    "stable_focus_scope_commit_id",
    "stable_focus_scope_request_id",
    "stable_focus_scope_request_response_id",
    "stable_layout_id",
    "stable_section_id",
    "stable_layout_section_id",
    "stable_section_focus_scope_id",
]
