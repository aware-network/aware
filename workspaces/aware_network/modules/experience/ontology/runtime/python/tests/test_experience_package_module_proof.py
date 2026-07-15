from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.stable_ids import stable_code_package_id
from aware_experience.materialization.snapshot_commit import (
    commit_environment_experience_snapshot,
    commit_experience_package_manifest_snapshot,
)
from aware_experience_ontology.environment.experience_package import (
    ExperiencePackage,
)
from aware_experience_ontology.stable_ids import (
    stable_environment_experience_id,
    stable_experience_package_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    MetaOIGAssertions,
)
from ._experience_runtime_test_paths import REPO_ROOT


def _experience_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    )


def _experience_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/runtime/python",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/runtime/python",
    )


def _prepend_experience_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _experience_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_experience_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (  # noqa: WPS433
        meta_handlers as experience_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (  # noqa: WPS433
        meta_handlers as reactivity_meta_handlers,
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
        bootstrap_modules=(
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
    )
    assert runtime.context is not None
    return runtime


def _class_name_for_projection_node(*, runtime_index: Any, node: Any) -> str:
    class_config = getattr(node, "class_config", None)
    if class_config is None:
        class_config_id = getattr(node, "class_config_id", None)
        class_config = runtime_index.class_configs_by_id[class_config_id]
    return str(class_config.name)


def _projection_class_names(*, runtime_index: Any, projection_name: str) -> set[str]:
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=runtime_index,
        projection_name=projection_name,
    )
    opg = runtime_index.opg_by_hash[projection_hash]
    return {
        _class_name_for_projection_node(runtime_index=runtime_index, node=node)
        for node in opg.object_projection_graph_nodes
    }


def _projection_root_class_names(
    *, runtime_index: Any, projection_name: str
) -> set[str]:
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=runtime_index,
        projection_name=projection_name,
    )
    opg = runtime_index.opg_by_hash[projection_hash]
    return {
        _class_name_for_projection_node(runtime_index=runtime_index, node=node)
        for node in opg.object_projection_graph_nodes
        if bool(getattr(node, "is_root", False))
    }


async def _assertions_for_committed_head(
    *,
    runtime_index,
    branch_id: UUID,
    projection_hash: str,
) -> MetaOIGAssertions:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id")
    assert head.get("object_instance_graph_id")
    opg = runtime_index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=runtime_index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=runtime_index.attribute_configs_by_id,
        class_configs_by_id=runtime_index.class_configs_by_id,
    )
    return MetaOIGAssertions(oig=oig, index=runtime_index)


@pytest.mark.asyncio
async def test_experience_package_module_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_code_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401

    source_package_name = "aware_experience_test_source_package"
    source_package_fqn_prefix = "aware.experience.test.source"
    experience_fqn_prefix = "home_story"
    experience_package_name = "home-story"

    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface="structure",
        )
    )
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=source_package_name,
        language=CodeLanguage.aware.value,
    )
    environment_experience_id = stable_environment_experience_id(
        fqn_prefix=experience_fqn_prefix
    )
    experience_package_id = stable_experience_package_id(name=experience_package_name)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        runtime_index = runtime_context.index

        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="CodePackage",
        )
        environment_experience_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=runtime_index,
                projection_name="EnvironmentExperience",
            )
        )
        environment_experience_profile_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=runtime_index,
                projection_name="EnvironmentExperienceProfile",
            )
        )
        environment_experience_profile_config_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=runtime_index,
                projection_name="EnvironmentExperienceProfileConfig",
            )
        )
        environment_topology_seed_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=runtime_index,
                projection_name="EnvironmentTopologySeed",
            )
        )
        experience_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ExperiencePackage",
        )
        branch_id = uuid4()

        environment_experience_opg = runtime_index.opg_by_hash[
            environment_experience_projection_hash
        ]
        environment_profile_opg = runtime_index.opg_by_hash[
            environment_experience_profile_projection_hash
        ]
        environment_profile_config_opg = runtime_index.opg_by_hash[
            environment_experience_profile_config_projection_hash
        ]
        topology_seed_opg = runtime_index.opg_by_hash[
            environment_topology_seed_projection_hash
        ]
        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperience",
        ) == {"EnvironmentExperience"}
        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfileConfig",
        ) == {"EnvironmentExperienceProfileConfig"}
        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfile",
        ) == {"EnvironmentExperienceProfile"}
        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentTopologySeed",
        ) == {"EnvironmentTopologySeed"}
        assert _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperience",
        ) == {"EnvironmentExperience"}
        assert {
            relationship.target_object_projection_graph_id
            for relationship in (
                environment_experience_opg.object_projection_graph_relationships
            )
        } == {
            environment_profile_config_opg.id,
            environment_profile_opg.id,
            topology_seed_opg.id,
        }
        assert {
            "EnvironmentExperienceProfileConfig",
            "EnvironmentExperienceActorConfig",
            "EnvironmentExperienceProjection",
            "EnvironmentExperienceEvent",
            "EnvironmentExperienceEventAction",
            "EnvironmentExperienceViewEventTransition",
            "EnvironmentExperienceProcessConfig",
            "EnvironmentExperienceThreadConfig",
            "EnvironmentExperienceProgram",
            "EnvironmentExperienceProgramApply",
        }.issubset(
            _projection_class_names(
                runtime_index=runtime_index,
                projection_name="EnvironmentExperienceProfileConfig",
            )
        )
        assert _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfile",
        ) == {"EnvironmentExperienceProfile"}
        assert {
            "EnvironmentTopologySeed",
            "EnvironmentTopologyProcessSeed",
            "EnvironmentTopologyThreadSeed",
            "EnvironmentTopologyThreadLayoutSeed",
        } == _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentTopologySeed",
        )

        code_package_result = await commit_code_package_text_snapshot(
            index=runtime_index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=source_code_package_config_id,
            package_name=source_package_name,
            language=CodeLanguage.aware,
            surface="structure",
            manifest_kind="aware_toml",
            manifest_relative_path="aware.experience.toml",
            package_root=".",
            sources_root=".",
            fqn_prefix=source_package_fqn_prefix,
            source_texts_by_relative_path={
                "aware.experience.toml": (
                    "[experience]\n"
                    'package_name = "home-story"\n'
                    'fqn_prefix = "home_story"\n'
                ),
            },
        )
        assert code_package_result.code_package.id == source_code_package_id
        assert code_package_result.commit_id == code_package_result.head_commit_id
        assert code_package_result.object_count > 0

        environment_result = await commit_environment_experience_snapshot(
            index=runtime_index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=environment_experience_projection_hash,
            fqn_prefix=experience_fqn_prefix,
            title="Home Story",
            description="Experience package proof root",
        )
        assert environment_result.environment_experience.id == environment_experience_id
        assert environment_result.commit_id == environment_result.head_commit_id

        package_result = await commit_experience_package_manifest_snapshot(
            index=runtime_index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=experience_package_projection_hash,
            name=experience_package_name,
            environment_experience_id=environment_experience_id,
            source_code_package_id=source_code_package_id,
        )
        assert package_result.experience_package.id == experience_package_id
        assert package_result.commit_id == package_result.head_commit_id

        code_assertions = await _assertions_for_committed_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
        )
        code_assertions.expect_root(source_code_package_id)
        code_assertions.expect_instance(source_code_package_id)
        code_assertions.expect_primitive(
            instance_id=source_code_package_id,
            field_name="package_name",
            expected=source_package_name,
        )
        code_assertions.expect_primitive(
            instance_id=source_code_package_id,
            field_name="manifest_relative_path",
            expected="aware.experience.toml",
        )
        code_assertions.expect_primitive(
            instance_id=source_code_package_id,
            field_name="package_root",
            expected=".",
        )
        code_assertions.expect_primitive(
            instance_id=source_code_package_id,
            field_name="sources_root",
            expected=".",
        )
        code_assertions.expect_primitive(
            instance_id=source_code_package_id,
            field_name="fqn_prefix",
            expected=source_package_fqn_prefix,
        )

        environment_assertions = await _assertions_for_committed_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=environment_experience_projection_hash,
        )
        environment_assertions.expect_root(environment_experience_id)
        environment_assertions.expect_instance(environment_experience_id)
        environment_assertions.expect_primitive(
            instance_id=environment_experience_id,
            field_name="fqn_prefix",
            expected=experience_fqn_prefix,
        )
        environment_assertions.expect_primitive(
            instance_id=environment_experience_id,
            field_name="title",
            expected="Home Story",
        )
        environment_assertions.expect_primitive(
            instance_id=environment_experience_id,
            field_name="description",
            expected="Experience package proof root",
        )

        package_assertions = await _assertions_for_committed_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=experience_package_projection_hash,
        )
        package_assertions.expect_root(experience_package_id)
        package_assertions.expect_instance(experience_package_id)
        package_assertions.expect_primitive(
            instance_id=experience_package_id,
            field_name="name",
            expected=experience_package_name,
        )

        environment_experience_fk_value = package_assertions.primitive(
            instance_id=experience_package_id,
            field_name="environment_experience_id",
        )
        assert environment_experience_fk_value in {
            environment_experience_id,
            str(environment_experience_id),
        }

        source_code_package_fk_value = package_assertions.primitive(
            instance_id=experience_package_id,
            field_name="source_code_package_id",
        )
        assert source_code_package_fk_value in {
            source_code_package_id,
            str(source_code_package_id),
        }

        created = package_result.experience_package
        assert isinstance(created, ExperiencePackage)
        assert created.id == experience_package_id
        assert created.name == experience_package_name
        assert created.environment_experience_id == environment_experience_id
        assert created.source_code_package_id == source_code_package_id
