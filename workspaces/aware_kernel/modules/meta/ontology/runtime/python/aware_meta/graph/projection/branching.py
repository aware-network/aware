from __future__ import annotations

import re
from uuid import UUID

from aware_history_ontology.stable_ids import stable_branch_id as _stable_branch_id

_BRANCH_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]{0,127}$")


def normalize_branch_name(*, branch_name: str | None) -> str:
    return (branch_name or "").casefold().strip() or "default"


def resolve_portal_target_branch_key(
    *,
    object_instance_graph_id: UUID,
    object_projection_graph_identity_id: UUID,
    target_object_id: UUID,
) -> str:
    return (
        "portal:" + f"{object_instance_graph_id}:" + f"{object_projection_graph_identity_id}:" + f"{target_object_id}"
    )


def stable_portal_target_branch_id(
    *,
    object_instance_graph_id: UUID,
    object_projection_graph_identity_id: UUID,
    target_object_id: UUID,
) -> UUID:
    return _stable_branch_id(
        key=resolve_portal_target_branch_key(
            object_instance_graph_id=object_instance_graph_id,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            target_object_id=target_object_id,
        )
    )


def resolve_projection_root_named_branch_key(
    *,
    object_projection_graph_identity_id: UUID,
    projection_root_id: UUID,
    branch_name: str | None = None,
    is_branchable: bool,
) -> str:
    branch_name_norm = normalize_branch_name(branch_name=branch_name)
    if branch_name_norm != "default" and not is_branchable:
        raise ValueError(
            "Projection-root branch requires branchable projection when branch_name is not default"
            + f" (branch_name={branch_name!r})"
        )
    if not _BRANCH_NAME_RE.fullmatch(branch_name_norm):
        raise ValueError(
            "Projection-root branch name is invalid; expected pattern "
            + f"{_BRANCH_NAME_RE.pattern!r} (branch_name={branch_name!r} normalized={branch_name_norm!r})"
        )
    return (
        "projection_root:"
        + f"{object_projection_graph_identity_id}:"
        + f"{projection_root_id}:"
        + f"branch:{branch_name_norm}"
    )


def stable_projection_root_named_branch_id(
    *,
    object_projection_graph_identity_id: UUID,
    projection_root_id: UUID,
    branch_name: str | None = None,
    is_branchable: bool,
) -> UUID:
    return _stable_branch_id(
        key=resolve_projection_root_named_branch_key(
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            projection_root_id=projection_root_id,
            branch_name=branch_name,
            is_branchable=is_branchable,
        )
    )


__all__ = [
    "normalize_branch_name",
    "resolve_portal_target_branch_key",
    "stable_portal_target_branch_id",
    "resolve_projection_root_named_branch_key",
    "stable_projection_root_named_branch_id",
]
