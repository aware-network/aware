from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history.stable_ids import stable_lane_id
from aware_history_ontology.commit.commit import Commit
from aware_history_ontology.commit.commit_parent import CommitParent
from aware_history_ontology.commit.commit_enums import CommitStatus
from aware_history_ontology.lane.lane import Lane
from aware_history_ontology.stable_ids import stable_commit_id, stable_commit_parent_id
from aware_meta.graph.instance.commit.fs_store import (
    FSCommitStore,
    OigiHistoryDomainCommitProjection,
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar,
    object_instance_graph_commit_envelope_from_commit,
)
from aware_meta.runtime.commit import identity_history as identity_history_module
from aware_meta.runtime.commit.identity_history import (
    _canonicalize_domain_commit_envelope_identity_for_history,
    _oigi_history_projection_head_index_hit,
    _project_oigi_history_direct,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
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
async def test_commit_store_reads_envelope_without_model_validation(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    parent_commit_id = uuid4()
    domain_commit = _make_domain_commit(
        oigi_id=uuid4(),
        domain_oig_id=uuid4(),
        domain_projection_hash=domain_projection_hash,
        parent_commit_ids=(parent_commit_id,),
    )
    await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=domain_projection_hash,
        commit=domain_commit,
    )

    def _fail_model_validate(*_: object, **__: object) -> None:
        raise AssertionError("envelope reads must not validate the full commit body")

    monkeypatch.setattr(
        ObjectInstanceGraphCommit,
        "model_validate",
        _fail_model_validate,
    )

    envelope = await store.get_commit_envelope(
        branch_id=branch_id,
        projection_hash=domain_projection_hash,
        commit_id=domain_commit.commit.id,
    )

    assert envelope is not None
    assert envelope.commit_id == domain_commit.commit.id
    assert envelope.parent_commit_ids == (parent_commit_id,)
    assert envelope.object_instance_graph_id == domain_commit.object_instance_graph_id
    assert envelope.object_instance_graph_identity_id == (
        domain_commit.object_instance_graph_identity_id
    )
    assert envelope.graph_hash_post == domain_commit.graph_hash_post


@pytest.mark.asyncio
async def test_commit_store_reads_identity_sidecar_without_model_validation(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    class_instance_id = uuid4()
    domain_commit = _make_domain_commit(
        oigi_id=uuid4(),
        domain_oig_id=uuid4(),
        domain_projection_hash=domain_projection_hash,
        object_instance_graph_changes=[
            ObjectInstanceGraphChange.model_construct(
                id=uuid4(),
                class_instance_changes=[
                    ClassInstanceChange.model_construct(
                        id=uuid4(),
                        class_instance_id=class_instance_id,
                    )
                ],
                class_instance_relationship_changes=[],
            )
        ],
    )
    await store.put_commit_file(
        branch_id=branch_id,
        projection_hash=domain_projection_hash,
        commit=domain_commit,
    )

    def _fail_model_validate(*_: object, **__: object) -> None:
        raise AssertionError("sidecar reads must not validate the full commit body")

    monkeypatch.setattr(
        ObjectInstanceGraphCommit,
        "model_validate",
        _fail_model_validate,
    )

    sidecar = await store.get_commit_identity_sidecar(
        branch_id=branch_id,
        projection_hash=domain_projection_hash,
        commit_id=domain_commit.commit.id,
    )

    assert sidecar is not None
    assert sidecar.commit_id == domain_commit.commit.id
    assert sidecar.object_instance_graph_id == domain_commit.object_instance_graph_id
    assert sidecar.object_instance_graph_identity_id == (
        domain_commit.object_instance_graph_identity_id
    )
    assert sidecar.class_instance_ids == (class_instance_id,)


@pytest.mark.asyncio
async def test_commit_store_records_oigi_history_projection_index(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)
    domain_oig_id = uuid4()
    oigi_projection_hash = "sha256:test:oigi"
    domain_commit_id = uuid4()
    projection = OigiHistoryDomainCommitProjection(
        domain_commit_id=domain_commit_id,
        domain_branch_id=uuid4(),
        domain_projection_hash="sha256:test:domain",
        domain_lane_id=uuid4(),
        history_commit_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
        oigi_projection_hash=oigi_projection_hash,
        oigi_lane_commit_id=uuid4(),
        oigi_graph_hash_post="sha256:test:oigi-head",
    )

    assert store.put_oigi_history_domain_commit_projection(
        branch_id=domain_oig_id,
        projection_hash=oigi_projection_hash,
        projection=projection,
    )
    assert not store.put_oigi_history_domain_commit_projection(
        branch_id=domain_oig_id,
        projection_hash=oigi_projection_hash,
        projection=projection,
    )

    actual = await store.get_oigi_history_domain_commit_projection(
        branch_id=domain_oig_id,
        projection_hash=oigi_projection_hash,
        domain_commit_id=domain_commit_id,
    )

    assert actual == projection


@pytest.mark.asyncio
async def test_oigi_history_projection_index_hit_avoids_head_materialization() -> None:
    domain_oig_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    oigi_projection_hash = "sha256:test:oigi"
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    domain_commit_id = uuid4()
    history_commit_id = stable_commit_id(lane_id=lane_id, key=str(domain_commit_id))
    oigi_lane_commit_id = uuid4()
    oigi_graph_hash_post = "sha256:test:oigi-head"
    projection = OigiHistoryDomainCommitProjection(
        domain_commit_id=domain_commit_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_lane_id=lane_id,
        history_commit_id=history_commit_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=domain_oig_id,
        oigi_projection_hash=oigi_projection_hash,
        oigi_lane_commit_id=oigi_lane_commit_id,
        oigi_graph_hash_post=oigi_graph_hash_post,
    )

    class _Store:
        async def get_oigi_history_domain_commit_projection(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            domain_commit_id: UUID,
        ) -> OigiHistoryDomainCommitProjection | None:
            assert branch_id == domain_oig_id
            assert projection_hash == oigi_projection_hash
            assert domain_commit_id == projection.domain_commit_id
            return projection

    perf_ms: dict[str, int] = {}
    hit = await _oigi_history_projection_head_index_hit(
        store=_Store(),  # type: ignore[arg-type]
        oigi_head={
            "commit_id": str(oigi_lane_commit_id),
            "graph_hash_post": oigi_graph_hash_post,
        },
        domain_oig_id=domain_oig_id,
        oigi_projection_hash=oigi_projection_hash,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        domain_commit_id=domain_commit_id,
        history_commit_id=history_commit_id,
        perf_ms=perf_ms,
    )

    assert hit
    assert perf_ms["run_commit_reaction_oigi_projection_index_head_hit_count"] == 1
    assert perf_ms["run_commit_reaction_oigi_projection_index_head_miss_count"] == 0

    miss_perf_ms: dict[str, int] = {}
    missing_hash_hit = await _oigi_history_projection_head_index_hit(
        store=_Store(),  # type: ignore[arg-type]
        oigi_head={"commit_id": str(oigi_lane_commit_id)},
        domain_oig_id=domain_oig_id,
        oigi_projection_hash=oigi_projection_hash,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        domain_commit_id=domain_commit_id,
        history_commit_id=history_commit_id,
        perf_ms=miss_perf_ms,
    )

    assert not missing_hash_hit
    assert miss_perf_ms["run_commit_reaction_oigi_projection_index_head_hit_count"] == 0
    assert (
        miss_perf_ms["run_commit_reaction_oigi_projection_index_head_miss_count"] == 1
    )


@pytest.mark.asyncio
async def test_oigi_history_wrapper_does_not_copy_domain_change_body() -> None:
    oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    domain_commit = _make_domain_commit(
        oigi_id=oigi_id,
        domain_oig_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        object_instance_graph_changes=[
            ObjectInstanceGraphChange.model_construct(
                id=uuid4(),
                class_instance_changes=[],
                class_instance_relationship_changes=[],
            )
        ],
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )
    session = Session(branch_id=domain_branch_id, skip_db=True)
    session.imap_add(object_instance_graph_identity)

    class _Store:
        async def get_commit(self, **_: object) -> ObjectInstanceGraphCommit | None:
            raise AssertionError("head commit was provided directly")

        async def get_commit_envelope(
            self,
            **_: object,
        ) -> ObjectInstanceGraphCommitEnvelope | None:
            raise AssertionError("head commit envelope was provided directly")

        async def put_commit_file(self, **_: object) -> bool:
            return True

        async def get_commit_identity_sidecar(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            assert commit_id == domain_commit.commit.id
            return _make_identity_sidecar(
                oigi_id=oigi_id,
                domain_oig_id=domain_oig_id,
                domain_commit_id=domain_commit.commit.id,
            )

    await _project_oigi_history_direct(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        head_commit_id=domain_commit.commit.id,
        store=_Store(),  # type: ignore[arg-type]
        domain_commit=domain_commit,
    )

    wrapper = _wrapper_for_domain_commit(
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit_id=domain_commit.commit.id,
    )
    assert wrapper is not None
    assert wrapper.object_instance_graph_changes == []


@pytest.mark.asyncio
async def test_oigi_history_canonicalizes_legacy_envelope_without_full_commit_read() -> (
    None
):
    legacy_oigi_id = uuid4()
    canonical_oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    domain_commit_id = uuid4()
    envelope = _make_envelope(
        oigi_id=legacy_oigi_id,
        domain_oig_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=domain_commit_id,
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=canonical_oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )

    class _Store:
        async def get_commit(self, **_: object) -> ObjectInstanceGraphCommit | None:
            raise AssertionError("legacy envelope repair must stay shallow")

        async def put_commit_file(self, **_: object) -> bool:
            raise AssertionError(
                "legacy envelope repair must not rewrite commit bodies"
            )

    canonical = await _canonicalize_domain_commit_envelope_identity_for_history(
        store=_Store(),  # type: ignore[arg-type]
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit_envelope=envelope,
    )

    assert canonical.commit_id == domain_commit_id
    assert canonical.object_instance_graph_id == domain_oig_id
    assert canonical.object_instance_graph_identity_id == canonical_oigi_id
    assert canonical.object_instance_graph_commit_id == (
        stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=canonical_oigi_id,
            commit_id=domain_commit_id,
        )
    )


@pytest.mark.asyncio
async def test_oigi_history_prefers_sidecar_when_domain_commit_body_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    class_instance_ids = (uuid4(), uuid4())
    domain_commit = _make_domain_commit(
        oigi_id=oigi_id,
        domain_oig_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        object_instance_graph_changes=[
            ObjectInstanceGraphChange.model_construct(
                id=uuid4(),
                class_instance_changes=[
                    ClassInstanceChange.model_construct(
                        id=uuid4(),
                        class_instance_id=uuid4(),
                    )
                ],
                class_instance_relationship_changes=[],
            )
        ],
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )
    session = Session(branch_id=domain_branch_id, skip_db=True)
    session.imap_add(object_instance_graph_identity)

    def _fail_full_body_identity_scan(*_: object, **__: object) -> None:
        raise AssertionError("sidecar-covered history projection must not scan body")

    monkeypatch.setattr(
        identity_history_module,
        "_ensure_class_instance_identities",
        _fail_full_body_identity_scan,
    )

    class _Store:
        async def get_commit_envelope(self, **_: object) -> None:
            raise AssertionError("head envelope was derived from the provided commit")

        async def get_commit(self, **_: object) -> ObjectInstanceGraphCommit | None:
            raise AssertionError("sidecar-covered identity refs need no full body")

        async def get_commit_identity_sidecar(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            assert commit_id == domain_commit.commit.id
            return _make_identity_sidecar(
                oigi_id=oigi_id,
                domain_oig_id=domain_oig_id,
                domain_commit_id=domain_commit.commit.id,
                class_instance_ids=class_instance_ids,
            )

    await _project_oigi_history_direct(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        head_commit_id=domain_commit.commit.id,
        store=_Store(),  # type: ignore[arg-type]
        domain_commit=domain_commit,
    )

    projected_class_instance_ids = {
        identity.class_instance_id
        for identity in object_instance_graph_identity.class_instance_identities
    }
    assert projected_class_instance_ids == set(class_instance_ids)
    wrapper = _wrapper_for_domain_commit(
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit_id=domain_commit.commit.id,
    )
    assert wrapper is not None
    assert wrapper.object_instance_graph_changes == []


@pytest.mark.asyncio
async def test_oigi_history_uses_envelope_for_missing_parent_without_full_commit_read() -> (
    None
):
    oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    parent_commit_id = uuid4()
    head_commit_id = uuid4()
    parent_envelope = _make_envelope(
        oigi_id=oigi_id,
        domain_oig_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=parent_commit_id,
    )
    head_envelope = _make_envelope(
        oigi_id=oigi_id,
        domain_oig_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=head_commit_id,
        parent_commit_ids=(parent_commit_id,),
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )
    session = Session(branch_id=domain_branch_id, skip_db=True)
    session.imap_add(object_instance_graph_identity)

    class _Store:
        envelope_calls: list[UUID] = []
        sidecar_calls: list[UUID] = []

        async def get_commit_envelope(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitEnvelope | None:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            self.envelope_calls.append(commit_id)
            if commit_id == parent_commit_id:
                return parent_envelope
            return None

        async def get_commit(self, **_: object) -> ObjectInstanceGraphCommit | None:
            raise AssertionError("parent projection must not validate the full body")

        async def get_commit_identity_sidecar(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            self.sidecar_calls.append(commit_id)
            if commit_id in {parent_commit_id, head_commit_id}:
                return _make_identity_sidecar(
                    oigi_id=oigi_id,
                    domain_oig_id=domain_oig_id,
                    domain_commit_id=commit_id,
                )
            return None

    store = _Store()

    await _project_oigi_history_direct(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        head_commit_id=head_commit_id,
        store=store,  # type: ignore[arg-type]
        domain_commit_envelope=head_envelope,
    )

    projected_domain_commit_ids = {
        wrapper.commit.key
        for wrapper in object_instance_graph_identity.object_instance_graph_commits
    }
    assert projected_domain_commit_ids == {str(parent_commit_id), str(head_commit_id)}
    assert store.envelope_calls == [parent_commit_id]
    assert store.sidecar_calls == [head_commit_id, parent_commit_id]
    lane = session.imap_get(Lane, lane_id)
    assert lane is not None
    assert lane.head_commit_id == stable_commit_id(
        lane_id=lane_id,
        key=str(head_commit_id),
    )


@pytest.mark.asyncio
async def test_oigi_history_uses_identity_sidecar_for_class_instance_identities() -> (
    None
):
    oigi_id = uuid4()
    domain_oig_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    head_commit_id = uuid4()
    class_instance_ids = (uuid4(), uuid4())
    head_envelope = _make_envelope(
        oigi_id=oigi_id,
        domain_oig_id=domain_oig_id,
        domain_projection_hash=domain_projection_hash,
        domain_commit_id=head_commit_id,
    )
    object_instance_graph_identity = ObjectInstanceGraphIdentity(
        id=oigi_id,
        object_projection_graph_identity_id=uuid4(),
        object_instance_graph_id=domain_oig_id,
    )
    session = Session(branch_id=domain_branch_id, skip_db=True)
    session.imap_add(object_instance_graph_identity)

    class _Store:
        async def get_commit_envelope(self, **_: object) -> None:
            raise AssertionError("head envelope was provided directly")

        async def get_commit(self, **_: object) -> ObjectInstanceGraphCommit | None:
            raise AssertionError("sidecar-covered identity refs need no full body")

        async def get_commit_identity_sidecar(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            assert commit_id == head_commit_id
            return _make_identity_sidecar(
                oigi_id=oigi_id,
                domain_oig_id=domain_oig_id,
                domain_commit_id=head_commit_id,
                class_instance_ids=class_instance_ids,
            )

    await _project_oigi_history_direct(
        session=session,
        object_instance_graph_identity=object_instance_graph_identity,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        lane_id=lane_id,
        head_commit_id=head_commit_id,
        store=_Store(),  # type: ignore[arg-type]
        domain_commit_envelope=head_envelope,
    )

    projected_class_instance_ids = {
        identity.class_instance_id
        for identity in object_instance_graph_identity.class_instance_identities
    }
    assert projected_class_instance_ids == set(class_instance_ids)
    wrapper = _wrapper_for_domain_commit(
        object_instance_graph_identity=object_instance_graph_identity,
        domain_commit_id=head_commit_id,
    )
    assert wrapper is not None
    assert wrapper.object_instance_graph_changes == []


def _make_domain_commit(
    *,
    oigi_id: UUID,
    domain_oig_id: UUID,
    domain_projection_hash: str,
    domain_commit_id: UUID | None = None,
    parent_commit_ids: tuple[UUID, ...] = (),
    object_instance_graph_changes: list[ObjectInstanceGraphChange] | None = None,
) -> ObjectInstanceGraphCommit:
    domain_commit_id = domain_commit_id or uuid4()
    commit = Commit(
        id=domain_commit_id,
        lane_id=uuid4(),
        key=str(domain_commit_id),
        author_id=uuid4(),
        created_at=datetime.now(UTC),
        status=CommitStatus.local,
        commit_parents=[
            CommitParent(
                id=stable_commit_parent_id(
                    commit_id=domain_commit_id,
                    parent_commit_id=parent_commit_id,
                ),
                commit_id=domain_commit_id,
                parent_commit_id=parent_commit_id,
            )
            for parent_commit_id in parent_commit_ids
        ],
    )
    return ObjectInstanceGraphCommit(
        id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=oigi_id,
            commit_id=domain_commit_id,
        ),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        commit=commit,
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
        object_instance_graph_changes=object_instance_graph_changes or [],
    )


def _make_envelope(
    *,
    oigi_id: UUID,
    domain_oig_id: UUID,
    domain_projection_hash: str,
    domain_commit_id: UUID,
    parent_commit_ids: tuple[UUID, ...] = (),
) -> ObjectInstanceGraphCommitEnvelope:
    return object_instance_graph_commit_envelope_from_commit(
        branch_id=uuid4(),
        projection_hash=domain_projection_hash,
        commit=_make_domain_commit(
            oigi_id=oigi_id,
            domain_oig_id=domain_oig_id,
            domain_projection_hash=domain_projection_hash,
            domain_commit_id=domain_commit_id,
            parent_commit_ids=parent_commit_ids,
        ),
    )


def _make_identity_sidecar(
    *,
    oigi_id: UUID,
    domain_oig_id: UUID,
    domain_commit_id: UUID,
    parent_commit_ids: tuple[UUID, ...] = (),
    class_instance_ids: tuple[UUID, ...] = (),
) -> ObjectInstanceGraphCommitIdentitySidecar:
    return ObjectInstanceGraphCommitIdentitySidecar(
        commit_id=domain_commit_id,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        parent_commit_ids=parent_commit_ids,
        class_instance_ids=class_instance_ids,
    )


def _wrapper_for_domain_commit(
    *,
    object_instance_graph_identity: ObjectInstanceGraphIdentity,
    domain_commit_id: UUID,
) -> ObjectInstanceGraphCommit | None:
    for wrapper in object_instance_graph_identity.object_instance_graph_commits:
        if wrapper.commit.key == str(domain_commit_id):
            return wrapper
    return None
