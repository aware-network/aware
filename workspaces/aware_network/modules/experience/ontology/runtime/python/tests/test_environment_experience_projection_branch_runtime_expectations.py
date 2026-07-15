from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

import pytest

from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
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
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
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
        repo_root / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_runtime",
        repo_root / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/runtime/python",
        repo_root / "workspaces/aware_network/modules/experience/ontology/runtime/python",
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


def _projection(*, runtime_index: Any, projection_name: str) -> Any:
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=runtime_index,
        projection_name=projection_name,
    )
    return runtime_index.opg_by_hash[projection_hash]


def _class_name_for_projection_node(*, runtime_index: Any, node: Any) -> str:
    class_config = getattr(node, "class_config", None)
    if class_config is None:
        class_config_id = getattr(node, "class_config_id", None)
        class_config = runtime_index.class_configs_by_id[class_config_id]
    return str(class_config.name)


def _projection_class_names(*, runtime_index: Any, projection_name: str) -> set[str]:
    opg = _projection(runtime_index=runtime_index, projection_name=projection_name)
    return {
        _class_name_for_projection_node(runtime_index=runtime_index, node=node)
        for node in opg.object_projection_graph_nodes
    }


def _projection_root_class_names(
    *,
    runtime_index: Any,
    projection_name: str,
) -> set[str]:
    opg = _projection(runtime_index=runtime_index, projection_name=projection_name)
    return {
        _class_name_for_projection_node(runtime_index=runtime_index, node=node)
        for node in opg.object_projection_graph_nodes
        if bool(getattr(node, "is_root", False))
    }


def _portal_target_projection_names(
    *,
    runtime_index: Any,
    projection_name: str,
) -> set[str]:
    opg = _projection(runtime_index=runtime_index, projection_name=projection_name)
    opg_names_by_id = {
        candidate.id: candidate.name
        for candidate in runtime_index.ocg.object_projection_graphs
    }
    return {
        str(opg_names_by_id[relationship.target_object_projection_graph_id])
        for relationship in opg.object_projection_graph_relationships
    }


def test_environment_experience_projection_branches_are_runtime_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_experience_ontology  # noqa: F401

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        runtime_index = runtime_context.index

        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperience",
        ) == {"EnvironmentExperience"}
        assert _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperience",
        ) == {"EnvironmentExperience"}
        assert _portal_target_projection_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperience",
        ) == {
            "EnvironmentExperienceProfileConfig",
            "EnvironmentExperienceProfile",
            "EnvironmentTopologySeed",
            "ExperienceSession",
        }

        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfileConfig",
        ) == {"EnvironmentExperienceProfileConfig"}
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
        assert "EnvironmentExperience" not in _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfileConfig",
        )

        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfile",
        ) == {"EnvironmentExperienceProfile"}
        assert _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfile",
        ) == {"EnvironmentExperienceProfile"}
        assert "EnvironmentExperience" not in _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentExperienceProfile",
        )

        assert _projection_root_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentTopologySeed",
        ) == {"EnvironmentTopologySeed"}
        assert {
            "EnvironmentTopologySeed",
            "EnvironmentTopologyProcessSeed",
            "EnvironmentTopologyThreadSeed",
            "EnvironmentTopologyThreadLayoutSeed",
        } == _projection_class_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentTopologySeed",
        )
        assert "EnvironmentExperienceProfileConfig" in _portal_target_projection_names(
            runtime_index=runtime_index,
            projection_name="EnvironmentTopologySeed",
        )
