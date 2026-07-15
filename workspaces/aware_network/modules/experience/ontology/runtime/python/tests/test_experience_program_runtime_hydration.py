from __future__ import annotations

import sys
from types import SimpleNamespace
from uuid import UUID, uuid4

from ._experience_runtime_test_paths import EXPERIENCE_ONTOLOGY_RUNTIME_ROOT, REPO_ROOT

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "environment" / "python" / "aware_environment_service_dto",
    _REPO_ROOT / "libs" / "comms" / "python",
    _REPO_ROOT / "modules" / "experience" / "runtime",
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "meta" / "runtime",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "environment" / "runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_experience.program import snapshot_reader  # noqa: E402
from aware_orm.session.session import Session  # noqa: E402


class _HydratedNode:
    def __init__(self, node_id: UUID) -> None:
        self.id = node_id
        self.children: list[_HydratedNode] = []
        self._branch_id: UUID | None = None

    def get_branch_id(self) -> UUID | None:
        return self._branch_id


def test_program_snapshot_reader_source_is_clean_for_deprecated_runtime() -> None:
    source = (
        EXPERIENCE_ONTOLOGY_RUNTIME_ROOT
        / "aware_experience"
        / "program"
        / "snapshot_reader.py"
    ).read_text()

    assert "aware_runtime" not in source


def test_hydrate_oig_into_session_uses_meta_reifier_session(
    monkeypatch,
) -> None:
    branch_id = uuid4()
    parent_id = uuid4()
    child_id = uuid4()
    index = object()
    opg = SimpleNamespace(name="ProgramConfig")
    oig = object()
    captured: dict[str, object] = {}

    def _fake_reify_oig_session(
        *,
        index: object,
        opg: object,
        oig: object,
        branch_id: UUID,
    ) -> Session:
        captured["index"] = index
        captured["opg"] = opg
        captured["oig"] = oig
        captured["branch_id"] = branch_id

        parent = _HydratedNode(parent_id)
        child = _HydratedNode(child_id)
        parent.children = [child]

        scratch = Session(branch_id=branch_id, skip_db=True)
        scratch.imap_add(parent)
        scratch.imap_add(child)
        return scratch

    monkeypatch.setattr(
        snapshot_reader,
        "reify_oig_session",
        _fake_reify_oig_session,
    )

    target = Session(branch_id=branch_id, skip_db=True)
    count = snapshot_reader._hydrate_oig_into_session(
        index=index,
        opg=opg,  # type: ignore[arg-type]
        session=target,
        oig=oig,
        branch_id=branch_id,
    )

    assert count == 2
    assert captured == {
        "index": index,
        "opg": opg,
        "oig": oig,
        "branch_id": branch_id,
    }
    parent = target.imap_get(_HydratedNode, parent_id)
    child = target.imap_get(_HydratedNode, child_id)
    assert parent is not None
    assert child is not None
    assert parent.children == [child]
    assert getattr(parent, "_bound_session") is target
    assert getattr(child, "_bound_session") is target
