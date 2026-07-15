from __future__ import annotations

import sys
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from ._environment_runtime_test_paths import (
    ENVIRONMENT_ONTOLOGY_ROOT,
    ENVIRONMENT_RUNTIME_ROOT,
    REPO_ROOT,
)

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "meta" / "runtime",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    ENVIRONMENT_RUNTIME_ROOT,
    ENVIRONMENT_ONTOLOGY_ROOT / "structure/python/orm_runtime",
    _REPO_ROOT / "modules" / "storage" / "structure" / "ontology" / "python",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_meta_ontology.stable_ids import (  # noqa: E402
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_identity_id,
)
from aware_environment.handlers.impl.thread import thread as thread_impl  # noqa: E402
from aware_environment.handlers.impl.thread import (  # noqa: E402
    thread_object_instance_graph_branch as oigb_impl,
)
from aware_environment.stable_ids import stable_thread_oigb_assoc_id  # noqa: E402
from aware_environment_ontology.thread.thread import Thread  # noqa: E402
from aware_environment_ontology.thread.thread_object_instance_graph_branch import (  # noqa: E402
    ThreadObjectInstanceGraphBranch,
)


class _FakeCommitStore:
    def __init__(
        self,
        *,
        domain_commit_id: UUID,
        object_instance_graph_id: UUID,
        has_head_payload: bool = True,
    ) -> None:
        self.domain_commit_id = domain_commit_id
        self.object_instance_graph_id = object_instance_graph_id
        self.has_head_payload = has_head_payload
        self.head_requests: list[tuple[UUID, str]] = []
        self.commit_requests: list[tuple[UUID, str, UUID]] = []

    async def head(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> dict[str, object] | None:
        self.head_requests.append((branch_id, projection_hash))
        if not self.has_head_payload:
            return None
        return {
            "commit_id": str(self.domain_commit_id),
            "object_instance_graph_id": str(self.object_instance_graph_id),
        }

    async def get_commit(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        commit_id: UUID,
    ) -> SimpleNamespace:
        self.commit_requests.append((branch_id, projection_hash, commit_id))
        return SimpleNamespace(commit=SimpleNamespace(id=commit_id))


class _FakeSession:
    def __init__(self, existing: object | None = None) -> None:
        self.existing = existing
        self.lookups: list[tuple[type[object], UUID]] = []

    def imap_get(self, model_type: type[object], object_id: UUID) -> object | None:
        self.lookups.append((model_type, object_id))
        return self.existing


@pytest.mark.asyncio
async def test_create_for_lane_derives_thread_oigb_association_from_meta_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread_id = uuid4()
    domain_branch_id = uuid4()
    projection_hash = "identity-projection"
    domain_commit_id = uuid4()
    object_instance_graph_id = uuid4()
    opgi_id = uuid4()
    store = _FakeCommitStore(
        domain_commit_id=domain_commit_id,
        object_instance_graph_id=object_instance_graph_id,
    )
    session = _FakeSession()
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=(SimpleNamespace(projection_hash=projection_hash),)
        )
    )
    monkeypatch.setattr(oigb_impl, "FSCommitStore", lambda: store)
    monkeypatch.setattr(oigb_impl, "current_handler_index", lambda: index)
    monkeypatch.setattr(oigb_impl, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        oigb_impl,
        "resolve_ocgi_opgi",
        lambda *, index, projection_hash: (None, SimpleNamespace(id=opgi_id)),
    )

    assoc = await oigb_impl.create_for_lane(
        thread_id=thread_id,
        domain_branch_id=domain_branch_id,
        projection_hash=projection_hash,
        title="Identity",
        is_active=True,
    )

    expected_oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi_id,
        object_instance_graph_id=object_instance_graph_id,
    )
    expected_oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=expected_oigi_id,
        branch_id=domain_branch_id,
    )
    assert assoc == ThreadObjectInstanceGraphBranch(
        id=stable_thread_oigb_assoc_id(
            thread_id=thread_id,
            oigb_id=expected_oigb_id,
        ),
        thread_id=thread_id,
        object_instance_graph_branch_id=expected_oigb_id,
        object_instance_graph_identity_id=expected_oigi_id,
        title="Identity",
        is_active=True,
    )
    assert store.head_requests == [(domain_branch_id, projection_hash)]
    assert store.commit_requests == [
        (domain_branch_id, projection_hash, domain_commit_id),
    ]
    assert session.lookups == [(ThreadObjectInstanceGraphBranch, assoc.id)]


@pytest.mark.asyncio
async def test_create_for_lane_fails_closed_when_domain_lane_has_no_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _FakeCommitStore(
        domain_commit_id=uuid4(),
        object_instance_graph_id=uuid4(),
        has_head_payload=False,
    )
    monkeypatch.setattr(oigb_impl, "FSCommitStore", lambda: store)

    with pytest.raises(RuntimeError, match="Cannot attach lane with no HEAD commit"):
        await oigb_impl.create_for_lane(
            thread_id=uuid4(),
            domain_branch_id=uuid4(),
            projection_hash="identity-projection",
        )


@pytest.mark.asyncio
async def test_thread_attach_lane_appends_once_per_oigb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread = Thread(
        id=uuid4(),
        thread_config_id=uuid4(),
        process_id=uuid4(),
        key="bootstrap",
    )
    domain_branch_id = uuid4()
    identity_oigb_id = uuid4()
    credential_oigb_id = uuid4()
    identity_oigi_id = uuid4()
    credential_oigi_id = uuid4()
    oigb_by_projection = {
        "identity-projection": (identity_oigb_id, identity_oigi_id),
        "credential-projection": (credential_oigb_id, credential_oigi_id),
    }
    create_calls: list[tuple[UUID, str]] = []

    async def _create_for_lane(
        *,
        thread_id: UUID,
        domain_branch_id: UUID,
        projection_hash: str,
        title: str | None = None,
        is_active: bool = True,
    ) -> ThreadObjectInstanceGraphBranch:
        create_calls.append((domain_branch_id, projection_hash))
        oigb_id, oigi_id = oigb_by_projection[projection_hash]
        return ThreadObjectInstanceGraphBranch(
            id=stable_thread_oigb_assoc_id(thread_id=thread_id, oigb_id=oigb_id),
            thread_id=thread_id,
            object_instance_graph_branch_id=oigb_id,
            object_instance_graph_identity_id=oigi_id,
            title=title,
            is_active=is_active,
        )

    monkeypatch.setattr(
        ThreadObjectInstanceGraphBranch,
        "create_for_lane",
        _create_for_lane,
    )

    identity_assoc = await thread_impl.attach_lane(
        thread=thread,
        domain_branch_id=domain_branch_id,
        projection_hash="identity-projection",
        title="Identity",
        is_active=True,
    )
    duplicate_identity_assoc = await thread_impl.attach_lane(
        thread=thread,
        domain_branch_id=domain_branch_id,
        projection_hash="identity-projection",
        title="Identity duplicate",
        is_active=False,
    )
    credential_assoc = await thread_impl.attach_lane(
        thread=thread,
        domain_branch_id=domain_branch_id,
        projection_hash="credential-projection",
        title="Credential",
        is_active=False,
    )

    assert duplicate_identity_assoc is identity_assoc
    assert credential_assoc is not identity_assoc
    assert thread.thread_object_instance_graph_branches == [
        identity_assoc,
        credential_assoc,
    ]
    assert [
        assoc.object_instance_graph_branch_id
        for assoc in thread.thread_object_instance_graph_branches
    ] == [
        identity_oigb_id,
        credential_oigb_id,
    ]
    assert create_calls == [
        (domain_branch_id, "identity-projection"),
        (domain_branch_id, "identity-projection"),
        (domain_branch_id, "credential-projection"),
    ]


def test_attach_lane_existing_domain_proof_uses_meta_handler_boundary() -> None:
    with open(__file__, encoding="utf-8") as source:
        text = source.read()

    disallowed_markers = (
        "aware_" "runtime",
        "aware_" "environment_artifacts",
        "resolve_environment_lane_" "context",
        "ensure_object_instance_graph_identity_lane_" "head",
        "hydrate_orm_graph_" "from_oig",
        "resolve_environment_runtime_" "manifest",
        "Runtime" "Harness",
    )

    assert [marker for marker in disallowed_markers if marker in text] == []
