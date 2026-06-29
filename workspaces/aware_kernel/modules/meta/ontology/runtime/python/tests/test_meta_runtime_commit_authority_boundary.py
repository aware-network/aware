from __future__ import annotations

from aware_meta.runtime.commit.identity_history import (
    upsert_object_instance_graph_identity_history_from_domain_commit,
)
from aware_meta.runtime.commit.identity_lane import (
    ensure_object_instance_graph_identity_lane_head,
    resolve_object_instance_graph_identity_lane_context,
)
from aware_meta.runtime.graph_identity_lane import (
    register_domain_commit_in_graph_identity_lane,
)
from aware_meta.runtime.commit.required_reactions import (
    MetaCommitReactionContext,
    RuntimeCommitReactionContext,
    run_required_meta_commit_reactions,
    run_required_runtime_commit_reactions,
)


def test_meta_commit_authority_exports_oigi_helpers() -> None:
    assert ensure_object_instance_graph_identity_lane_head.__module__ == (
        "aware_meta.runtime.commit.identity_lane"
    )
    assert (
        upsert_object_instance_graph_identity_history_from_domain_commit.__module__
        == ("aware_meta.runtime.commit.identity_history")
    )
    assert (
        register_domain_commit_in_graph_identity_lane.__module__
        == "aware_meta.runtime.graph_identity_lane"
    )
    assert callable(resolve_object_instance_graph_identity_lane_context)


def test_meta_required_reaction_names_are_compatibility_stable() -> None:
    assert MetaCommitReactionContext is RuntimeCommitReactionContext
    assert run_required_meta_commit_reactions is run_required_runtime_commit_reactions
