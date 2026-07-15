from __future__ import annotations

from uuid import UUID

import pytest

from aware_history_ontology.stable_ids import (
    stable_branch_id as stable_history_branch_id,
)
from aware_meta.graph.projection.branching import (
    normalize_branch_name,
    resolve_portal_target_branch_key,
    resolve_projection_root_named_branch_key,
    stable_portal_target_branch_id,
)


def test_portal_target_branch_key_and_id_are_deterministic() -> None:
    object_instance_graph_id = UUID("00000000-0000-0000-0000-000000000111")
    object_projection_graph_identity_id = UUID("00000000-0000-0000-0000-000000000222")
    target_object_id = UUID("00000000-0000-0000-0000-000000000333")
    key = resolve_portal_target_branch_key(
        object_instance_graph_id=object_instance_graph_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        target_object_id=target_object_id,
    )
    assert (
        key
        == f"portal:{object_instance_graph_id}:{object_projection_graph_identity_id}:{target_object_id}"
    )
    assert stable_portal_target_branch_id(
        object_instance_graph_id=object_instance_graph_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        target_object_id=target_object_id,
    ) == stable_history_branch_id(key=key)


def test_projection_root_branch_key_enforces_branchable_and_token_validation() -> None:
    opgi_id = UUID("00000000-0000-0000-0000-000000000444")
    root_id = UUID("00000000-0000-0000-0000-000000000555")
    assert normalize_branch_name(branch_name=None) == "default"
    assert normalize_branch_name(branch_name="  Main/Dev  ") == "main/dev"

    assert (
        resolve_projection_root_named_branch_key(
            object_projection_graph_identity_id=opgi_id,
            projection_root_id=root_id,
            branch_name="main/dev",
            is_branchable=True,
        )
        == f"projection_root:{opgi_id}:{root_id}:branch:main/dev"
    )

    with pytest.raises(ValueError):
        _ = resolve_projection_root_named_branch_key(
            object_projection_graph_identity_id=opgi_id,
            projection_root_id=root_id,
            branch_name="main/dev",
            is_branchable=False,
        )

    with pytest.raises(ValueError):
        _ = resolve_projection_root_named_branch_key(
            object_projection_graph_identity_id=opgi_id,
            projection_root_id=root_id,
            branch_name="bad token with spaces",
            is_branchable=True,
        )
