from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_ontology.handlers.impl.ontology import (
    ontology_package_runtime_code_package as handler,
)
from aware_ontology_ontology.ontology.ontology_package_runtime_code_package import (
    OntologyPackageRuntimeCodePackage,
)
from aware_ontology_ontology.stable_ids import (
    stable_ontology_package_runtime_code_package_id,
)


class _FakeSession:
    def __init__(self, objects: dict[tuple[type[object], UUID], object]) -> None:
        self._objects = objects

    def imap_get(self, model_type: type[object], object_id: UUID | None) -> Any:
        if object_id is None:
            return None
        return self._objects.get((model_type, object_id))


def _code_package(code_package_id: UUID) -> CodePackage:
    return CodePackage.model_construct(id=code_package_id)


def _commit(commit_id: UUID, *, code_package_id: UUID) -> ObjectInstanceGraphCommit:
    return ObjectInstanceGraphCommit.model_construct(
        id=commit_id,
        root_source_object_id=code_package_id,
    )


def _runtime_package(
    *,
    ontology_package_id: UUID,
    code_package_id: UUID,
    commit_id: UUID | None,
    commit: ObjectInstanceGraphCommit | None = None,
) -> OntologyPackageRuntimeCodePackage:
    return OntologyPackageRuntimeCodePackage.model_construct(
        id=stable_ontology_package_runtime_code_package_id(
            ontology_package_id=ontology_package_id,
            code_package_id=code_package_id,
        ),
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        code_package=_code_package(code_package_id),
        object_instance_graph_commit_id=commit_id,
        object_instance_graph_commit=commit,
        package_name="aware-demo",
        language=CodeLanguage.python,
        import_root="aware_demo",
        manifest_relative_path="runtime/python/pyproject.toml",
        package_root="runtime/python",
        role="ontology_runtime_handler_package",
        include_paths=[],
        exclude_paths=[],
    )


async def _build(
    *,
    ontology_package_id: UUID,
    code_package_id: UUID,
    commit_id: UUID,
) -> OntologyPackageRuntimeCodePackage:
    return await handler.build_via_ontology_package(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        object_instance_graph_commit_id=commit_id,
        package_name="aware-demo",
        language=CodeLanguage.python,
        import_root="aware_demo",
        manifest_relative_path="runtime/python/pyproject.toml",
        package_root="runtime/python",
        role="ontology_runtime_handler_package",
    )


@pytest.mark.asyncio
async def test_build_creates_runtime_package_with_resolved_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ontology_package_id = uuid4()
    code_package_id = uuid4()
    commit_id = uuid4()
    code_package = _code_package(code_package_id)
    commit = _commit(commit_id, code_package_id=code_package_id)
    monkeypatch.setattr(
        handler,
        "current_handler_session",
        lambda: _FakeSession(
            {
                (CodePackage, code_package_id): code_package,
                (ObjectInstanceGraphCommit, commit_id): commit,
            }
        ),
    )

    result = await _build(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        commit_id=commit_id,
    )

    assert result.code_package is code_package
    assert result.object_instance_graph_commit is commit
    assert result.object_instance_graph_commit_id == commit_id


@pytest.mark.asyncio
async def test_build_reuses_same_commit_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ontology_package_id = uuid4()
    code_package_id = uuid4()
    commit_id = uuid4()
    commit = _commit(commit_id, code_package_id=code_package_id)
    existing = _runtime_package(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        commit_id=commit_id,
        commit=commit,
    )
    monkeypatch.setattr(
        handler,
        "current_handler_session",
        lambda: _FakeSession(
            {
                (OntologyPackageRuntimeCodePackage, existing.id): existing,
                (ObjectInstanceGraphCommit, commit_id): commit,
            }
        ),
    )

    result = await _build(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        commit_id=commit_id,
    )

    assert result is existing
    assert result.object_instance_graph_commit is commit
    assert result.object_instance_graph_commit_id == commit_id


@pytest.mark.asyncio
async def test_build_advances_valid_commit_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ontology_package_id = UUID("11111111-1111-4111-8111-111111111111")
    code_package_id = UUID("22222222-2222-4222-8222-222222222222")
    old_commit_id = UUID("33333333-3333-4333-8333-333333333333")
    new_commit_id = UUID("44444444-4444-4444-8444-444444444444")
    old_commit = _commit(old_commit_id, code_package_id=code_package_id)
    new_commit = _commit(new_commit_id, code_package_id=code_package_id)
    existing = _runtime_package(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        commit_id=old_commit_id,
        commit=old_commit,
    )
    monkeypatch.setattr(
        handler,
        "current_handler_session",
        lambda: _FakeSession(
            {
                (OntologyPackageRuntimeCodePackage, existing.id): existing,
                (ObjectInstanceGraphCommit, new_commit_id): new_commit,
            }
        ),
    )

    result = await _build(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
        commit_id=new_commit_id,
    )

    assert result is existing
    assert result.object_instance_graph_commit is new_commit
    assert result.object_instance_graph_commit_id == new_commit_id


@pytest.mark.asyncio
async def test_build_rejects_commit_owned_by_another_code_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ontology_package_id = uuid4()
    code_package_id = uuid4()
    foreign_commit_id = uuid4()
    foreign_commit = _commit(foreign_commit_id, code_package_id=uuid4())
    monkeypatch.setattr(
        handler,
        "current_handler_session",
        lambda: _FakeSession(
            {(ObjectInstanceGraphCommit, foreign_commit_id): foreign_commit}
        ),
    )

    with pytest.raises(RuntimeError, match="commit owner mismatch"):
        await _build(
            ontology_package_id=ontology_package_id,
            code_package_id=code_package_id,
            commit_id=foreign_commit_id,
        )


@pytest.mark.asyncio
async def test_build_rejects_existing_edge_payload_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ontology_package_id = uuid4()
    code_package_id = uuid4()
    commit_id = uuid4()
    runtime_package_id = stable_ontology_package_runtime_code_package_id(
        ontology_package_id=ontology_package_id,
        code_package_id=code_package_id,
    )
    existing = _runtime_package(
        ontology_package_id=ontology_package_id,
        code_package_id=uuid4(),
        commit_id=None,
    )
    existing.id = runtime_package_id
    monkeypatch.setattr(
        handler,
        "current_handler_session",
        lambda: _FakeSession(
            {(OntologyPackageRuntimeCodePackage, runtime_package_id): existing}
        ),
    )

    with pytest.raises(RuntimeError, match="payload mismatch"):
        await _build(
            ontology_package_id=ontology_package_id,
            code_package_id=code_package_id,
            commit_id=commit_id,
        )
