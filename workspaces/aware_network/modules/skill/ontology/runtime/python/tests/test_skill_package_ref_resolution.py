from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from _skill_runtime_test_paths import REPO_ROOT

for _relpath in (
    "workspaces/aware_network/modules/skill/ontology/runtime/python",
    "workspaces/aware_network/modules/skill/ontology/structure/python/orm_runtime",
    "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_runtime",
):
    _path_str = str((REPO_ROOT / _relpath).resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_meta.graph.instance.commit.contract import ObjectInstanceGraphCommitRef
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (  # noqa: E402
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex  # noqa: E402
from aware_skill.package_ref_resolution import (  # noqa: E402
    SkillRuntimePackageRef,
    resolve_committed_skill_runtime_package_ref,
)
from aware_skill_ontology.skill.skill_config import SkillConfig  # noqa: E402
from aware_skill_ontology.skill.skill_package import SkillPackage  # noqa: E402
from aware_skill_ontology.skill.skill_package_api_package import (  # noqa: E402
    SkillPackageApiPackage,
)


def _fake_projection_hash_token(projection_name: str) -> str:
    return {
        "SkillPackage": "skill_package",
        "SkillConfig": "skill_config",
    }.get(projection_name, projection_name)


@pytest.mark.asyncio
async def test_committed_skill_runtime_package_ref_hydrates_package_skill_config_and_api_edges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    skill_toml = revision_root / "skills" / "door_control" / "aware.skill.toml"
    skill_toml.parent.mkdir(parents=True, exist_ok=True)
    skill_toml.write_text("this is intentionally not valid toml\n", encoding="utf-8")

    branch_id = uuid4()
    package_id = uuid4()
    skill_config_id = uuid4()
    package_oig_commit_id = uuid4()
    legacy_head_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    skill_config_oig_commit_id = uuid4()
    skill_config_domain_commit_id = uuid4()
    stale_portal_skill_config_domain_commit_id = uuid4()
    source_code_package_id = uuid4()
    api_package_id = uuid4()

    skill_config_commit = ObjectInstanceGraphCommit.model_construct(
        id=skill_config_oig_commit_id,
        commit_id=stale_portal_skill_config_domain_commit_id,
    )
    skill_config = SkillConfig.model_construct(
        id=skill_config_id,
        name="door_control",
    )
    api_package_edge = SkillPackageApiPackage.model_construct(
        id=uuid4(),
        skill_package_id=package_id,
        api_package_id=api_package_id,
    )
    skill_package = SkillPackage.model_construct(
        id=package_id,
        name="door_control",
        skill_config_id=skill_config_id,
        skill_config=skill_config,
        skill_config_object_instance_graph_commit_id=skill_config_oig_commit_id,
        skill_config_object_instance_graph_commit=skill_config_commit,
        source_code_package_id=source_code_package_id,
        api_packages=[api_package_edge],
    )
    package_ref = SkillRuntimePackageRef(
        family_key="skill",
        package_kind="skill",
        package_name="door_control",
        manifest_path="skills/door_control/aware.skill.toml",
        semantic_package_id=str(package_id),
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_head_commit_id=str(legacy_head_commit_id),
        semantic_branch_id=str(branch_id),
        semantic_root_kind="skill_config",
        semantic_root_id=str(skill_config_id),
        semantic_root_object_instance_graph_commit_id=str(skill_config_oig_commit_id),
    )
    index = cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{_fake_projection_hash_token(projection_name)}"

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self
        assert kwargs["branch_id"] == branch_id
        if kwargs["projection_hash"] == "sha256:skill_package":
            assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
            return package_domain_commit_id
        assert kwargs["projection_hash"] == "sha256:skill_config"
        assert kwargs["object_instance_graph_commit_id"] == skill_config_oig_commit_id
        return skill_config_domain_commit_id

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        if kwargs["root_type"] is SkillPackage:
            assert kwargs["projection_hash"] == "sha256:skill_package"
            assert kwargs["commit_id"] == package_domain_commit_id
            assert kwargs["root_id"] == package_id
            return skill_package
        assert kwargs["root_type"] is SkillConfig
        assert kwargs["projection_hash"] == "sha256:skill_config"
        assert kwargs["commit_id"] == skill_config_domain_commit_id
        assert kwargs["root_id"] == skill_config_id
        return skill_config

    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._find_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution.FSCommitStore."
        "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_skill_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
    )

    assert resolved.skill_package_id == package_id
    assert resolved.skill_config_id == skill_config_id
    assert (
        resolved.skill_config_object_instance_graph_commit_id
        == skill_config_oig_commit_id
    )
    assert resolved.manifest_path == skill_toml.resolve()
    assert resolved.manifest_relative_path == "skills/door_control/aware.skill.toml"
    assert resolved.toml_paths == (skill_toml.resolve(),)
    assert resolved.package_name == "door_control"
    assert resolved.semantic_package_id == str(package_id)
    assert resolved.semantic_object_instance_graph_commit_id == str(
        package_oig_commit_id
    )
    assert resolved.semantic_head_commit_id == str(legacy_head_commit_id)
    assert resolved.semantic_branch_id == str(branch_id)
    assert resolved.semantic_root_object_instance_graph_commit_id == str(
        skill_config_oig_commit_id
    )
    assert resolved.source_code_package_id == str(source_code_package_id)
    assert resolved.skill_package is skill_package
    assert resolved.skill_config is skill_config
    assert resolved.skill_package_api_packages == (api_package_edge,)
    assert resolved.api_package_ids == (api_package_id,)


@pytest.mark.asyncio
async def test_committed_skill_runtime_package_ref_resolves_branch_from_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"

    branch_id = uuid4()
    package_id = uuid4()
    skill_config_id = uuid4()
    package_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    skill_config_oig_commit_id = uuid4()
    skill_config_domain_commit_id = uuid4()
    stale_portal_skill_config_domain_commit_id = uuid4()

    skill_config_commit = ObjectInstanceGraphCommit.model_construct(
        id=skill_config_oig_commit_id,
        commit_id=stale_portal_skill_config_domain_commit_id,
    )
    skill_config = SkillConfig.model_construct(
        id=skill_config_id,
        name="door_control",
    )
    skill_package = SkillPackage.model_construct(
        id=package_id,
        name="door_control",
        skill_config_id=skill_config_id,
        skill_config=skill_config,
        skill_config_object_instance_graph_commit_id=skill_config_oig_commit_id,
        skill_config_object_instance_graph_commit=skill_config_commit,
        api_packages=[],
    )
    package_ref = SkillRuntimePackageRef(
        family_key="skill",
        package_kind="skill",
        package_name="door_control",
        semantic_package_id=str(package_id),
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_root_kind="skill_config",
        semantic_root_id=str(skill_config_id),
        semantic_root_object_instance_graph_commit_id=str(skill_config_oig_commit_id),
    )
    index = cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{_fake_projection_hash_token(projection_name)}"

    async def _fake_domain_commit_refs_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["projection_hash"] == "sha256:skill_package"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=branch_id,
                projection_hash="sha256:skill_package",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=package_domain_commit_id,
            ),
        )

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self
        assert kwargs["branch_id"] == branch_id
        assert kwargs["projection_hash"] == "sha256:skill_config"
        assert kwargs["object_instance_graph_commit_id"] == skill_config_oig_commit_id
        return skill_config_domain_commit_id

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["branch_id"] == branch_id
        if kwargs["root_type"] is SkillPackage:
            assert kwargs["projection_hash"] == "sha256:skill_package"
            assert kwargs["commit_id"] == package_domain_commit_id
            assert kwargs["root_id"] == package_id
            return skill_package
        assert kwargs["root_type"] is SkillConfig
        assert kwargs["projection_hash"] == "sha256:skill_config"
        assert kwargs["commit_id"] == skill_config_domain_commit_id
        assert kwargs["root_id"] == skill_config_id
        return skill_config

    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._find_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_domain_commit_refs_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution.FSCommitStore."
        "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_skill_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
    )

    assert resolved.semantic_branch_id == str(branch_id)
    assert resolved.semantic_object_instance_graph_commit_id == str(
        package_oig_commit_id
    )
    assert resolved.skill_package_id == package_id
    assert resolved.skill_config_id == skill_config_id
    assert resolved.manifest_path is None
    assert resolved.toml_paths == ()


@pytest.mark.asyncio
async def test_committed_skill_runtime_package_ref_rejects_ambiguous_branchless_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    package_oig_commit_id = uuid4()
    index = cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    async def _fake_domain_commit_refs_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=uuid4(),
                projection_hash="sha256:skill_package",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=uuid4(),
            ),
            ObjectInstanceGraphCommitRef(
                branch_id=uuid4(),
                projection_hash="sha256:skill_package",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=uuid4(),
            ),
        )

    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._find_projection_hash_by_name",
        lambda *, index, projection_name: (
            f"sha256:{_fake_projection_hash_token(projection_name)}"
        ),
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_domain_commit_refs_for_oig_commit_id,
    )

    with pytest.raises(RuntimeError, match="multiple SkillPackage branches"):
        await resolve_committed_skill_runtime_package_ref(
            index=index,
            package_ref=SkillRuntimePackageRef(
                family_key="skill",
                package_kind="skill",
                package_name="door_control",
                semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
            ),
            materialized_workspace_root=revision_root,
        )


@pytest.mark.asyncio
async def test_committed_skill_runtime_package_ref_rejects_root_pin_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    branch_id = uuid4()
    package_id = uuid4()
    skill_config_id = uuid4()
    package_oig_commit_id = uuid4()
    skill_config_oig_commit_id = uuid4()
    skill_package = SkillPackage.model_construct(
        id=package_id,
        name="door_control",
        skill_config_id=skill_config_id,
        skill_config_object_instance_graph_commit_id=skill_config_oig_commit_id,
    )
    package_ref = SkillRuntimePackageRef(
        family_key="skill",
        package_kind="skill",
        package_name="door_control",
        semantic_package_id=str(package_id),
        semantic_head_commit_id=str(package_oig_commit_id),
        semantic_branch_id=str(branch_id),
        semantic_root_kind="skill_config",
        semantic_root_id=str(skill_config_id),
        semantic_root_object_instance_graph_commit_id=str(uuid4()),
    )
    index = cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    def _fake_projection_hash(
        *, index: MetaGraphRuntimeIndex, projection_name: str
    ) -> str:
        del index
        return f"sha256:{_fake_projection_hash_token(projection_name)}"

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self, kwargs
        return uuid4()

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["root_type"] is SkillPackage
        return skill_package

    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._find_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution.FSCommitStore."
        "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_skill.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    with pytest.raises(
        RuntimeError,
        match="semantic_root_object_instance_graph_commit_id",
    ):
        await resolve_committed_skill_runtime_package_ref(
            index=index,
            package_ref=package_ref,
            materialized_workspace_root=revision_root,
        )


@pytest.mark.asyncio
async def test_committed_skill_runtime_package_ref_rejects_non_skill_package_kind() -> (
    None
):
    index = cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    with pytest.raises(RuntimeError, match="package_kind='skill'"):
        await resolve_committed_skill_runtime_package_ref(
            index=index,
            package_ref=SkillRuntimePackageRef(
                family_key="skill",
                package_kind="api",
                package_name="door_control",
            ),
        )
