from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.stable_ids import stable_code_package_id
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.build import service as build_service


def _experience_source_code_package_config_id() -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_experience_toml",
            surface="experience",
        )
    )


def _experience_source_code_package_id(*, package_name: str) -> UUID:
    return stable_code_package_id(
        code_package_config_id=_experience_source_code_package_config_id(),
        package_name=package_name,
        language=CodeLanguage.aware.value,
    )


@pytest.mark.asyncio
async def test_execute_experience_package_build_consumer_uses_meta_projection_lookup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_name = "demo-experience"
    fqn_prefix = "aware_demo"
    environment_experience_id = experience_stable_ids.stable_environment_experience_id(
        fqn_prefix=fqn_prefix,
    )
    experience_package_id = experience_stable_ids.stable_experience_package_id(
        name=package_name,
    )
    source_code_package_id = _experience_source_code_package_id(
        package_name=package_name,
    )
    index = object()
    branch_id = uuid4()
    observed_projection_names: list[str] = []
    observed_hydrates: list[dict[str, object]] = []

    monkeypatch.setattr(
        build_service,
        "resolve_experience_package_materialization_spec",
        lambda **_: SimpleNamespace(
            package_name=package_name,
            package_fqn_prefix=fqn_prefix,
            experience_name="Demo",
        ),
    )

    def _fake_find_meta_graph_projection_hash_by_name(
        *,
        index: object,
        projection_name: str,
    ) -> str:
        assert index is test_index
        observed_projection_names.append(projection_name)
        return f"hash:{projection_name}"

    async def _fake_hydrate_lane_root_from_head(**kwargs: object) -> object:
        observed_hydrates.append(dict(kwargs))
        root_type = kwargs["root_type"]
        if root_type is build_service.EnvironmentExperience:
            return SimpleNamespace(
                id=environment_experience_id,
                fqn_prefix=fqn_prefix,
            )
        if root_type is build_service.ExperiencePackage:
            return SimpleNamespace(
                id=experience_package_id,
                name=package_name,
                environment_experience_id=environment_experience_id,
                source_code_package_id=source_code_package_id,
            )
        raise AssertionError(f"Unexpected root type: {root_type!r}")

    test_index = index
    monkeypatch.setattr(
        build_service,
        "find_meta_graph_projection_hash_by_name",
        _fake_find_meta_graph_projection_hash_by_name,
    )
    monkeypatch.setattr(
        build_service,
        "_hydrate_lane_root_from_head",
        _fake_hydrate_lane_root_from_head,
    )

    result = await build_service.execute_experience_package_build_consumer(
        index=index,
        branch_id=branch_id,
        workspace_root=tmp_path,
        experience_toml_path=tmp_path / "aware.experience.toml",
        experience_package_id=experience_package_id,
        environment_experience_id=environment_experience_id,
        source_code_package_id=source_code_package_id,
    )

    assert observed_projection_names == [
        "EnvironmentExperience",
        "ExperiencePackage",
    ]
    projection_hashes = {
        item["root_type"]: item["projection_hash"] for item in observed_hydrates
    }
    assert projection_hashes[build_service.EnvironmentExperience] == (
        "hash:EnvironmentExperience"
    )
    assert projection_hashes[build_service.ExperiencePackage] == (
        "hash:ExperiencePackage"
    )
    assert result.package_name == package_name
    assert result.experience_name == "Demo"
    assert isinstance(result.experience_package_id, UUID)
    assert result.experience_package_id == experience_package_id
