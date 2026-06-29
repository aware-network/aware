from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_meta.graph.instance.commit.fs_store import FSCommitStore, FSSnapshotStore
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


def test_commit_store_requires_explicit_root_or_aware_root_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_ROOT", raising=False)

    with pytest.raises(
        RuntimeError,
        match="FSCommitStore requires explicit root_dir or AWARE_ROOT",
    ):
        FSCommitStore()


def test_snapshot_store_requires_explicit_root_or_aware_root_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_ROOT", raising=False)

    with pytest.raises(
        RuntimeError,
        match="FSCommitStore requires explicit root_dir or AWARE_ROOT",
    ):
        FSSnapshotStore()


def test_commit_store_uses_aware_root_env(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path))

    assert FSCommitStore().aware_root == tmp_path.resolve()
    assert FSSnapshotStore().aware_root == tmp_path.resolve()


@pytest.mark.asyncio
async def test_commit_store_finds_oig_commit_ref_across_branches(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "ServicePackage"
    branch_id = uuid4()
    other_branch_id = uuid4()
    commit = _make_commit(projection_hash=projection_hash)
    other_commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    await store.put_commit_file(
        branch_id=other_branch_id,
        projection_hash=projection_hash,
        commit=other_commit,
    )
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )

    refs = await store.domain_commit_refs_for_object_instance_graph_commit_id(
        projection_hash=projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )

    assert len(refs) == 1
    assert refs[0].branch_id == branch_id
    assert refs[0].projection_hash == projection_hash
    assert refs[0].object_instance_graph_commit_id == object_instance_graph_commit_id
    assert refs[0].domain_commit_id == commit.commit.id


@pytest.mark.asyncio
async def test_commit_store_resolves_oig_commit_refs_in_one_index_pass(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "CodePackage"
    first_branch_id = uuid4()
    second_branch_id = uuid4()
    first_commit = _make_commit(projection_hash=projection_hash)
    second_commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=first_branch_id,
        projection_hash=projection_hash,
        commit=first_commit,
    )
    await store.put_commit_file(
        branch_id=second_branch_id,
        projection_hash=projection_hash,
        commit=second_commit,
    )
    first_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=first_commit.object_instance_graph_identity_id,
        commit_id=first_commit.commit.id,
    )
    second_oig_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=second_commit.object_instance_graph_identity_id,
        commit_id=second_commit.commit.id,
    )

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("indexed batch ref resolution must not read lane HEAD")

    monkeypatch.setattr(FSCommitStore, "head_commit", _boom, raising=True)

    refs_by_id = await store.domain_commit_refs_for_object_instance_graph_commit_ids(
        projection_hash=projection_hash,
        object_instance_graph_commit_ids=(first_oig_commit_id, second_oig_commit_id),
    )

    assert refs_by_id[first_oig_commit_id][0].branch_id == first_branch_id
    assert refs_by_id[first_oig_commit_id][0].domain_commit_id == first_commit.commit.id
    assert refs_by_id[second_oig_commit_id][0].branch_id == second_branch_id
    assert (
        refs_by_id[second_oig_commit_id][0].domain_commit_id == second_commit.commit.id
    )


@pytest.mark.asyncio
async def test_commit_store_batch_ref_resolution_can_disable_head_fallback(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "CodePackage"
    missing_oig_commit_id = uuid4()

    async def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("strict indexed resolution must not read lane HEAD")

    monkeypatch.setattr(FSCommitStore, "head_commit", _boom, raising=True)

    refs_by_id = await store.domain_commit_refs_for_object_instance_graph_commit_ids(
        projection_hash=projection_hash,
        object_instance_graph_commit_ids=(missing_oig_commit_id,),
        allow_head_fallback=False,
    )

    assert refs_by_id == {missing_oig_commit_id: ()}


@pytest.mark.asyncio
async def test_commit_store_reports_ambiguous_oig_commit_ref_matches(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    projection_hash = "ServicePackage"
    first_branch_id = uuid4()
    second_branch_id = uuid4()
    commit = _make_commit(projection_hash=projection_hash)
    await store.put_commit_file(
        branch_id=first_branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    await store.put_commit_file(
        branch_id=second_branch_id,
        projection_hash=projection_hash,
        commit=commit,
    )
    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )

    refs = await store.domain_commit_refs_for_object_instance_graph_commit_id(
        projection_hash=projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )

    assert {ref.branch_id for ref in refs} == {first_branch_id, second_branch_id}


@pytest.mark.asyncio
async def test_put_commit_file_repairs_legacy_oigi_metadata(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    projection_hash = "ObjectConfigGraphPackage"
    commit_id = uuid4()
    object_instance_graph_id = uuid4()
    legacy_oigi_id = uuid4()
    canonical_oigi_id = uuid4()
    graph_hash_post = "sha256:graph-post"
    legacy_commit = _make_commit(
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_identity_id=legacy_oigi_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash_post,
    )
    canonical_commit = _make_commit(
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_identity_id=canonical_oigi_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash_post,
    )

    assert (
        await store.put_commit_file(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=legacy_commit,
        )
        is True
    )
    assert (
        await store.put_commit_file(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=canonical_commit,
        )
        is True
    )

    repaired = await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    assert repaired is not None
    assert repaired.object_instance_graph_identity_id == canonical_oigi_id
    canonical_ref_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=canonical_oigi_id,
        commit_id=commit_id,
    )
    assert repaired.id == canonical_ref_id
    legacy_ref_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=legacy_oigi_id,
        commit_id=commit_id,
    )
    assert await store.domain_commit_refs_for_object_instance_graph_commit_id(
        projection_hash=projection_hash,
        object_instance_graph_commit_id=canonical_ref_id,
    )
    assert (
        await store.domain_commit_refs_for_object_instance_graph_commit_id(
            projection_hash=projection_hash,
            object_instance_graph_commit_id=legacy_ref_id,
        )
        == ()
    )


def _make_commit(
    *,
    projection_hash: str,
    commit_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    graph_hash_post: str | None = None,
) -> ObjectInstanceGraphCommit:
    commit_id = commit_id or uuid4()
    object_instance_graph_identity_id = object_instance_graph_identity_id or uuid4()
    return ObjectInstanceGraphCommit.model_construct(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            commit_id=commit_id,
        ),
        commit=Commit.model_construct(
            id=commit_id,
            author_id=uuid4(),
            key=str(commit_id),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
            lane_id=uuid4(),
            commit_parents=[],
        ),
        object_instance_graph_key="service-package",
        object_instance_graph_name="service-package",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_post=graph_hash_post or f"sha256:{uuid4().hex}",
        graph_hash_pre="",
        projection_hash=projection_hash,
        source_language=CodeLanguage.python,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id or uuid4(),
        commit_id=commit_id,
        object_instance_graph_changes=[],
    )
