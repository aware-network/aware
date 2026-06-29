from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history.stable_ids import stable_lane_id
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.lane.lane import Lane
from aware_history_ontology.stable_ids import (
    stable_commit_id,
    stable_commit_parent_id,
)
from aware_meta.runtime.commit.identity_history import (
    _canonicalize_domain_commit_identity_for_history,
    _project_oigi_history_direct,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_orm.session.session import Session


@pytest.mark.asyncio
async def test_oigi_history_canonicalizes_stale_domain_commit_identity() -> None:
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    domain_oig_id = uuid4()
    expected_oigi_id = uuid4()
    stale_oigi_id = uuid4()
    domain_commit_id = uuid4()
    persisted: list[ObjectInstanceGraphCommit] = []
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=expected_oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )
    domain_commit = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=stale_oigi_id,
            commit_id=domain_commit_id,
        ),
        object_instance_graph_identity_id=stale_oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=Commit(
            id=domain_commit_id,
            lane_id=uuid4(),
            key=str(domain_commit_id),
            author_id=uuid4(),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
        ),
        commit_id=domain_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash=domain_projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )

    class _Store:
        async def put_commit_file(
            self,
            *,
            branch_id: object,
            projection_hash: object,
            commit: ObjectInstanceGraphCommit,
        ) -> bool:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            persisted.append(commit)
            return True

    canonical_commit = await _canonicalize_domain_commit_identity_for_history(
        store=_Store(),  # type: ignore[arg-type]
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit=domain_commit,
    )

    assert canonical_commit.object_instance_graph_id == domain_oig_id
    assert canonical_commit.object_instance_graph_identity_id == expected_oigi_id
    assert canonical_commit.id == stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=expected_oigi_id,
        commit_id=domain_commit_id,
    )
    assert persisted == [canonical_commit]


@pytest.mark.asyncio
async def test_oigi_history_leaves_unrelated_domain_oig_mismatch_to_validator() -> None:
    expected_oigi_id = uuid4()
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=expected_oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
    )
    domain_commit_id = uuid4()
    domain_commit = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=uuid4(),
            commit_id=domain_commit_id,
        ),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
        commit=Commit(
            id=domain_commit_id,
            lane_id=uuid4(),
            key=str(domain_commit_id),
            author_id=uuid4(),
            created_at=datetime.now(UTC),
            status=CommitStatus.local,
        ),
        commit_id=domain_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash="sha256:test:domain",
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )

    class _Store:
        async def put_commit_file(self, **_: object) -> bool:
            raise AssertionError("unrelated domain OIG mismatch must not be rewritten")

    unchanged_commit = await _canonicalize_domain_commit_identity_for_history(
        store=_Store(),  # type: ignore[arg-type]
        domain_branch_id=uuid4(),
        domain_projection_hash="sha256:test:domain",
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit=domain_commit,
    )

    assert unchanged_commit is domain_commit


@pytest.mark.asyncio
async def test_oigi_history_direct_stops_at_already_projected_parent() -> None:
    oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    author_id = uuid4()
    parent_domain_commit_id = uuid4()
    head_domain_commit_id = uuid4()
    parent_history_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(parent_domain_commit_id),
    )
    head_history_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(head_domain_commit_id),
    )
    parent_history_commit = Commit(
        id=parent_history_commit_id,
        lane_id=lane_id,
        key=str(parent_domain_commit_id),
        author_id=author_id,
        created_at=datetime.now(UTC),
        status=CommitStatus.local,
    )
    parent_wrapper = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=parent_domain_commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=parent_history_commit,
        commit_id=parent_history_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:parent-pre",
        graph_hash_post="sha256:test:parent-post",
        projection_hash=domain_projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
        object_instance_graph_commits=[parent_wrapper],
    )
    session = Session(branch_id=domain_branch_id, skip_db=True)
    session.imap_add(object_instance_graph_identity)
    session.imap_add(parent_history_commit)
    session.imap_add(parent_wrapper)

    domain_head_commit = Commit(
        id=head_domain_commit_id,
        lane_id=uuid4(),
        key=str(head_domain_commit_id),
        author_id=author_id,
        created_at=datetime.now(UTC),
        status=CommitStatus.local,
        commit_parents=[
            CommitParent(
                id=stable_commit_parent_id(
                    commit_id=head_domain_commit_id,
                    parent_commit_id=parent_domain_commit_id,
                ),
                commit_id=head_domain_commit_id,
                parent_commit_id=parent_domain_commit_id,
            )
        ],
    )
    domain_commit = ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=head_domain_commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=domain_head_commit,
        commit_id=head_domain_commit_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:head-pre",
        graph_hash_post="sha256:test:head-post",
        projection_hash=domain_projection_hash,
        source_language=CodeLanguage.aware,
        object_instance_graph_changes=[],
    )

    class _Store:
        calls: list[object] = []

        async def get_commit(
            self,
            *,
            branch_id: object,
            projection_hash: object,
            commit_id: object,
        ) -> ObjectInstanceGraphCommit | None:
            self.calls.append(commit_id)
            raise AssertionError(
                "already projected parent commits must not be replayed"
            )

        async def get_commit_identity_sidecar(self, **_: object) -> None:
            return None

        async def put_commit_file(self, **_: object) -> bool:
            return True

    store = _Store()

    await _project_oigi_history_direct(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        head_commit_id=head_domain_commit_id,
        domain_commit=domain_commit,
        store=store,  # type: ignore[arg-type]
    )

    projected_domain_commit_ids = {
        wrapper.commit.key
        for wrapper in object_instance_graph_identity.object_instance_graph_commits
    }
    assert projected_domain_commit_ids == {
        str(parent_domain_commit_id),
        str(head_domain_commit_id),
    }
    assert store.calls == []
    lane = session.imap_get(Lane, lane_id)
    assert lane is not None
    assert lane.head_commit_id == head_history_commit_id
