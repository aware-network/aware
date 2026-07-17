from __future__ import annotations

from uuid import uuid4

from aware_service_runtime.materialization.snapshot_commit import _snapshot_commit_id


def test_snapshot_commit_id_distinguishes_repeated_historical_state() -> None:
    namespace = uuid4()
    branch_id = uuid4()
    root_object_id = uuid4()
    first_parent_id = uuid4()
    later_parent_id = uuid4()

    first_commit_id = _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash="service-package-projection",
        root_object_id=root_object_id,
        parent_commit_id=first_parent_id,
        graph_hash_pre="state-before-first",
        graph_hash_post="repeated-state",
    )
    repeated_state_commit_id = _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash="service-package-projection",
        root_object_id=root_object_id,
        parent_commit_id=later_parent_id,
        graph_hash_pre="state-before-later",
        graph_hash_post="repeated-state",
    )

    assert repeated_state_commit_id != first_commit_id
    assert repeated_state_commit_id == _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash="service-package-projection",
        root_object_id=root_object_id,
        parent_commit_id=later_parent_id,
        graph_hash_pre="state-before-later",
        graph_hash_post="repeated-state",
    )
