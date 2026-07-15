from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_experience.handlers.impl.environment import (
    experience_package as package_handler,
)
from aware_experience.handlers.impl.environment import (
    experience_package_dependency as dependency_handler,
)
from aware_experience.stable_ids import stable_experience_package_dependency_id
from aware_experience_ontology.environment.experience_package import ExperiencePackage
from aware_experience_ontology.environment.experience_package_dependency import (
    ExperiencePackageDependency,
)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


def _ids() -> tuple[UUID, UUID, UUID]:
    ns = uuid5(NAMESPACE_URL, "aware://tests/experience/package-dependency/v1")
    return (
        uuid5(ns, "source-experience-package"),
        uuid5(ns, "target-experience-package"),
        uuid5(ns, "target-commit"),
    )


@pytest.mark.asyncio
async def test_experience_package_dependency_build_is_session_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_package_id, target_package_id, target_commit_id = _ids()
    expected_id = stable_experience_package_dependency_id(
        experience_package_id=source_package_id,
        target_experience_package_id=target_package_id,
    )
    session = _Session()
    target_package = ExperiencePackage.model_construct(
        id=target_package_id,
        name="aware-control",
    )
    session.put(target_package)
    monkeypatch.setattr(dependency_handler, "current_handler_session", lambda: session)

    created = await dependency_handler.build_via_experience_package(
        experience_package_id=source_package_id,
        target_experience_package_id=target_package_id,
        target_package_name=" aware-control ",
        target_version_number=1,
        expected_hash_sha256="A" * 64,
        description=" Control surface ",
    )

    assert created.id == expected_id
    assert created.target_experience_package is target_package
    assert created.target_package_name == "aware-control"
    assert created.expected_hash_sha256 == "a" * 64
    assert created.description == "Control surface"

    session.put(created)
    created_again = await dependency_handler.build_via_experience_package(
        experience_package_id=source_package_id,
        target_experience_package_id=target_package_id,
        target_package_name="aware-control",
        target_experience_package_object_instance_graph_commit_id=target_commit_id,
        target_version_number=1,
        expected_hash_sha256="a" * 64,
        description="Control surface",
    )

    assert created_again is created
    assert (
        created.target_experience_package_object_instance_graph_commit_id
        == target_commit_id
    )


@pytest.mark.asyncio
async def test_experience_package_attach_dependency_attaches_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_package_id, target_package_id, _target_commit_id = _ids()
    created = ExperiencePackageDependency.model_construct(
        id=stable_experience_package_dependency_id(
            experience_package_id=source_package_id,
            target_experience_package_id=target_package_id,
        ),
        experience_package_id=source_package_id,
        target_experience_package_id=target_package_id,
        target_package_name="aware-control",
    )

    async def _build_dependency(**_kwargs: object) -> ExperiencePackageDependency:
        return created

    monkeypatch.setattr(
        package_handler.ExperiencePackageDependency,
        "build_via_experience_package",
        staticmethod(_build_dependency),
    )
    package = ExperiencePackage.model_construct(
        id=source_package_id,
        name="aware-actor",
        experience_package_dependencies=[],
    )

    first = await package_handler.attach_experience_package_dependency(
        experience_package=package,
        target_experience_package_id=target_package_id,
        target_package_name="aware-control",
    )
    second = await package_handler.attach_experience_package_dependency(
        experience_package=package,
        target_experience_package_id=target_package_id,
        target_package_name="aware-control",
    )

    assert first is created
    assert second is created
    assert package.experience_package_dependencies == [created]
