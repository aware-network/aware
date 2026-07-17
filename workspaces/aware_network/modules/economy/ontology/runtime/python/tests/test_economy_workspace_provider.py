from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

import aware_economy.materialization.workspace_provider as workspace_provider
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


@pytest.mark.asyncio
async def test_idempotent_package_receipts_hydrate_committed_lane_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "sha256:economy-package"
    domain_commit_id = uuid4()
    object_instance_graph_identity_id = uuid4()

    class _CommitStore:
        async def head(self, *, branch_id, projection_hash):  # type: ignore[no-untyped-def]
            return {"commit_id": domain_commit_id}

        async def get_commit_identity_metadata(
            self,
            *,
            branch_id,
            projection_hash,
            commit_id,
        ):  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
            )

    monkeypatch.setattr(workspace_provider, "FSCommitStore", _CommitStore)

    resolved_domain_commit_id, resolved_oig_commit_id = (
        await workspace_provider._resolve_committed_package_receipts(
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=None,
            object_instance_graph_commit_id=None,
        )
    )

    assert resolved_domain_commit_id == domain_commit_id
    assert resolved_oig_commit_id == stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        commit_id=domain_commit_id,
    )


@pytest.mark.asyncio
async def test_new_package_receipts_do_not_read_persisted_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain_commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()

    class _UnexpectedCommitStore:
        async def head(self, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError(f"unexpected head read: {kwargs!r}")

        async def get_commit_identity_metadata(self, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError(f"unexpected metadata read: {kwargs!r}")

    monkeypatch.setattr(
        workspace_provider,
        "FSCommitStore",
        _UnexpectedCommitStore,
    )

    assert await workspace_provider._resolve_committed_package_receipts(
        branch_id=uuid4(),
        projection_hash="sha256:economy-package",
        domain_commit_id=domain_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    ) == (domain_commit_id, object_instance_graph_commit_id)
