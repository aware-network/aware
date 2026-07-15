from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_attention.materialization import service as attention_materialization_service
from aware_attention.materialization import (
    workspace_provider as attention_workspace_provider,
)
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.stable_ids import stable_layout_config_id
from aware_code.semantic_materialization import SemanticPackageMaterializationRequest
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceLayoutGraphBindingSnapshot,
    commit_environment_experience_snapshot,
    commit_experience_package_manifest_snapshot,
    commit_projection_experience_snapshot,
)
from aware_interface.materialization.app_package import AppScreenResolutionError
from aware_interface.materialization.app_screen_entry import (
    AppScreenEntryResolutionError,
    CommittedAppScreenEntryRequest,
    resolve_committed_app_screen_entry,
)
from aware_interface.materialization.workspace_provider import materialize
from aware_interface_ontology.interface.app_config import AppConfig
from aware_interface_ontology.interface.app_package import AppPackage
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.oig_model_reifier import reify_oig_session

from _interface_runtime_test_paths import REPO_ROOT
from _meta_runtime_support import build_interface_meta_runtime, isolated_meta_aware_root


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_app_package(
    *,
    workspace_root: Path,
    package_name: str,
    dependencies: tuple[str, ...],
    projection_experience: str,
    layout_binding_key: str,
) -> Path:
    module_root = workspace_root / "modules" / "home"
    _write(module_root / "aware.module.toml", "aware = 1\n")
    package_root = module_root / "apps" / package_name
    dependency_text = "\n".join(
        "\n".join(
            (
                "[[dependencies]]",
                f'package_name = "{dependency}"',
                'kind = "experience_package"',
                'role = "experience"',
            )
        )
        for dependency in dependencies
    )
    _write(
        package_root / "aware.app.toml",
        "\n".join(
            (
                "aware_app = 1",
                "",
                "[app]",
                f'package_name = "{package_name}"',
                f'app_name = "{package_name}"',
                'fqn_prefix = "aware_test_app"',
                'kind = "app"',
                "",
                "[dart]",
                f'package_path = "apps/{package_name}/dart/{package_name}"',
                f'package_name = "{package_name}"',
                'entrypoint = "lib/main.dart"',
                "",
                "[factory]",
                'package_name = "aware_app_factory"',
                "",
                "[control]",
                'default_screen = "primary"',
                "",
                "[build]",
                'sources_dir = "."',
                'include_paths = ["app.aware"]',
                "exclude_paths = []",
                "",
                dependency_text,
                "",
                "[[platforms]]",
                'target = "test"',
                'runner_path = "unused"',
                "enabled = false",
                "",
                "[[interfaces]]",
                'package_name = "test-interface"',
                'role = "primary"',
                'runtime_import = "package:test_interface/test_interface.dart"',
                'runtime_import_alias = "test_interface"',
                'runtime_factory = "buildInterfacePackageRuntime"',
                "",
            )
        ),
    )
    _write(
        package_root / "app.aware",
        "\n".join(
            (
                f"app {package_name} {{",
                "    screen primary {",
                f"        projection {projection_experience} layout {layout_binding_key}",
                "    }",
                "}",
                "",
            )
        ),
    )
    return package_root / "aware.app.toml"


async def _commit_experience_package(
    *,
    runtime: Any,
    index: object,
    aware_root: Path,
    package_name: str,
    projection_experience_name: str,
    layout_binding_key: str,
) -> tuple[dict[str, object], UUID, UUID]:
    base_branch_id = uuid4()
    environment_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="EnvironmentExperience",
    )
    environment = await commit_environment_experience_snapshot(
        index=index,
        actor_id=None,
        branch_id=base_branch_id,
        projection_hash=environment_projection_hash,
        fqn_prefix=projection_experience_name,
        title=projection_experience_name,
        description=None,
    )
    package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ExperiencePackage",
    )
    package = await commit_experience_package_manifest_snapshot(
        index=index,
        actor_id=None,
        branch_id=base_branch_id,
        projection_hash=package_projection_hash,
        name=package_name,
        environment_experience_id=environment.environment_experience.id,
        source_code_package_id=None,
    )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=package_projection_hash,
    )
    assert opgi is not None
    projection_branch_id = derive_experience_reference_branch_id(
        base_branch_id=base_branch_id,
        experience_name=projection_experience_name,
    )
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    layout_config_id = stable_layout_config_id(key=layout_binding_key)
    attention_targets = attention_materialization_service._resolve_attention_runtime_targets(
        index=index,
    )
    attention_runtime = attention_workspace_provider._RuntimeManifestAdapter(
        manifest_path=REPO_ROOT / "aware.workspace.toml",
        invoker=attention_workspace_provider._MetaGraphFunctionRuntimeInvoker(
            meta_runtime=runtime,
        ),
    )
    await attention_materialization_service._ensure_attention_root(
        runtime=attention_runtime,
        index=index,
        actor_id=None,
        aware_root=aware_root,
        lane_state={},
        target=attention_targets.layout_config,
        branch_id=layout_config_id,
        root_type=LayoutConfig,
        label=f"LayoutConfig.build({layout_binding_key})",
        kwargs={
            "key": layout_binding_key,
            "title": layout_binding_key,
            "description": None,
        },
        expected_fields={
            "id": layout_config_id,
            "key": layout_binding_key,
            "title": layout_binding_key,
            "description": None,
        },
    )
    projection = await commit_projection_experience_snapshot(
        index=index,
        actor_id=None,
        branch_id=projection_branch_id,
        projection_hash=projection_hash,
        projection_graph_hash=find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceGraph",
        ),
        section_graph_binding_hash=find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceSectionGraphBinding",
        ),
        layout_graph_binding_hash=find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperienceLayoutGraphBinding",
        ),
        attention_layout_config_hash=find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="LayoutConfig",
        ),
        object_projection_graph_identity_id=opgi.id,
        name=projection_experience_name,
        layout_graph_bindings=(
            ExperienceLayoutGraphBindingSnapshot(
                layout_config_id=layout_config_id,
                binding_key=layout_binding_key,
            ),
        ),
    )
    layout_binding = projection.projection_experience.projection_experience_layout_graph_bindings[0]
    return (
        {
            "package_name": package_name,
            "experience_package_id": str(package.experience_package.id),
            "semantic_branch_id": str(base_branch_id),
            "semantic_head_commit_id": str(package.head_commit_id),
            "experience_package_object_instance_graph_commit_id": str(package.object_instance_graph_commit_id),
            "aware_root": aware_root.as_posix(),
        },
        projection.projection_experience.id,
        layout_binding.id,
    )


async def _replay_root(
    *,
    index: object,
    aware_root: Path,
    branch_id: UUID,
    projection_name: str,
    commit_id: UUID,
    root_type: type,
):
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name=projection_name,
    )
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer(commits=FSCommitStore(root_dir=aware_root)).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    roots = tuple(obj for obj in session.imap_all_objects() if isinstance(obj, root_type))
    assert len(roots) == 1
    return roots[0]


@pytest.mark.asyncio
async def test_app_package_commits_and_replays_exact_experience_screens(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    aware_root_path = tmp_path / "aware-root"
    with isolated_meta_aware_root(aware_root_path) as aware_root:
        runtime = build_interface_meta_runtime(REPO_ROOT, workspace_root=aware_root)
        assert runtime.context is not None
        index = runtime.context.index
        home_reference, home_experience_id, home_layout_binding_id = await _commit_experience_package(
            runtime=runtime,
            index=index,
            aware_root=aware_root,
            package_name="home-story",
            projection_experience_name="home_story",
            layout_binding_key="configuration_map",
        )
        alternate_reference, _, _ = await _commit_experience_package(
            runtime=runtime,
            index=index,
            aware_root=aware_root,
            package_name="alternate-home",
            projection_experience_name="home_story",
            layout_binding_key="configuration_map",
        )
        manifest_path = _write_app_package(
            workspace_root=workspace_root,
            package_name="aware_home_app",
            dependencies=("home-story",),
            projection_experience="home_story",
            layout_binding_key="configuration_map",
        )
        app_branch_id = uuid4()
        result = await materialize(
            SemanticPackageMaterializationRequest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=app_branch_id,
                workspace_root=workspace_root,
                manifest_path=manifest_path,
                context={
                    "workspace_manifest_kind": "app",
                    "semantic_package_name": "aware_home_app",
                    "workspace_experience_package_references": (home_reference,),
                },
            )
        )

        assert result.commit_id is not None
        assert result.head_commit_id == result.commit_id
        bundle = result.bundle_packages[0]
        assert bundle.semantic_branch_id == app_branch_id
        assert bundle.semantic_head_commit_id == result.head_commit_id
        assert bundle.semantic_object_instance_graph_commit_id is not None
        app_config_commit_id = UUID(str(result.details["app_config_head_commit_id"]))
        app_config = await _replay_root(
            index=index,
            aware_root=aware_root,
            branch_id=app_branch_id,
            projection_name="AppConfig",
            commit_id=app_config_commit_id,
            root_type=AppConfig,
        )
        assert len(app_config.screen_configs) == 1
        screen = app_config.screen_configs[0]
        assert screen.screen_key == "primary"
        assert screen.projection_experience_id == home_experience_id
        assert screen.projection_experience_layout_graph_binding_id == home_layout_binding_id
        app_package = await _replay_root(
            index=index,
            aware_root=aware_root,
            branch_id=app_branch_id,
            projection_name="AppPackage",
            commit_id=result.head_commit_id,
            root_type=AppPackage,
        )
        assert app_package.app_config_id == app_config.id
        assert app_package.app_config_object_instance_graph_commit_id == UUID(
            str(result.details["app_config_object_instance_graph_commit_id"])
        )
        assert len(app_package.experience_packages) == 1
        assert len(app_package.interface_packages) == 1
        assert bundle.semantic_object_instance_graph_commit_id is not None
        entry = await resolve_committed_app_screen_entry(
            index=index,
            request=CommittedAppScreenEntryRequest(
                app_package_id=app_package.id,
                app_package_branch_id=app_branch_id,
                app_package_object_instance_graph_commit_id=(bundle.semantic_object_instance_graph_commit_id),
                app_config_screen_config_id=screen.id,
            ),
        )
        assert entry.app_config_id == app_config.id
        assert entry.app_config_screen_config_id == screen.id
        assert entry.screen_key == "primary"
        assert entry.projection_experience_id == home_experience_id
        assert entry.projection_experience_layout_graph_binding_id == home_layout_binding_id
        assert entry.experience_name == "home_story"
        assert entry.layout_binding_key == "configuration_map"

        with pytest.raises(
            AppScreenEntryResolutionError,
            match="must be contained by the pinned AppConfig",
        ):
            await resolve_committed_app_screen_entry(
                index=index,
                request=CommittedAppScreenEntryRequest(
                    app_package_id=app_package.id,
                    app_package_branch_id=app_branch_id,
                    app_package_object_instance_graph_commit_id=(bundle.semantic_object_instance_graph_commit_id),
                    app_config_screen_config_id=uuid4(),
                ),
            )

        ambiguous_manifest_path = _write_app_package(
            workspace_root=workspace_root,
            package_name="ambiguous_home_app",
            dependencies=("home-story", "alternate-home"),
            projection_experience="home_story",
            layout_binding_key="configuration_map",
        )
        with pytest.raises(AppScreenResolutionError, match="matches=2"):
            await materialize(
                SemanticPackageMaterializationRequest(
                    runtime=runtime,
                    index=index,
                    actor_id=None,
                    branch_id=uuid4(),
                    workspace_root=workspace_root,
                    manifest_path=ambiguous_manifest_path,
                    context={
                        "workspace_manifest_kind": "app",
                        "semantic_package_name": "ambiguous_home_app",
                        "workspace_experience_package_references": (
                            home_reference,
                            alternate_reference,
                        ),
                    },
                )
            )

        with pytest.raises(
            AppScreenResolutionError,
            match="missing committed ExperiencePackage dependencies",
        ):
            await materialize(
                SemanticPackageMaterializationRequest(
                    runtime=runtime,
                    index=index,
                    actor_id=None,
                    branch_id=uuid4(),
                    workspace_root=workspace_root,
                    manifest_path=manifest_path,
                    context={
                        "workspace_manifest_kind": "app",
                        "semantic_package_name": "aware_home_app",
                        "workspace_experience_package_references": (alternate_reference,),
                    },
                )
            )
