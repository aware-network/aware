from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.semantic_materialization import SemanticPackageMaterializationRequest
from aware_experience.compiler.builder import build_experience_compile_plan
from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.materialization.workspace_provider import (
    _emit_view_api_package_output,
    _materialize_language_contract_packages,
)
from aware_experience.semantic_contract import (
    EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS,
    EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS,
    EXPERIENCE_PROVIDER_OWNER,
    EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY,
    EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY,
    EXPERIENCE_VIEW_API_PRODUCER_KEY,
    EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION,
    EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
    EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
    EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER,
)
from aware_experience.view_api import (
    build_experience_view_api_compile_plan,
    emit_experience_view_api_compile_plan_artifact,
)

_EXPERIENCE_MODULE_ROOT = Path(__file__).resolve().parents[4]


def _bootstrap_experience_module_plugin() -> None:
    AwareModulePluginRegistry.clear()
    AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
        module_roots=(_EXPERIENCE_MODULE_ROOT,),
    )


def test_experience_compile_plan_mounts_api_views_without_generated_view_api(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_experience_toml(root=root)
    _write_actor_experience_sources(root=root)
    composition_path = _write_identity_composition_truth(root=root)

    plan = build_experience_compile_plan(
        snapshot=ExperienceWorkspace.from_toml(
            toml_path=root / "aware.experience.toml",
            repo_root=root,
        ).build_snapshot(),
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert plan.view_api_ownership is None
    assert plan.view_state_model_contracts == ()
    mounted_views = {
        experience.name: experience.observables[0].views[0]
        for experience in plan.projection_experience_ownership
    }
    assert {name: view.api_view_ref for name, view in mounted_views.items()} == {
        "aware_actor_roles": "identity.roles",
        "aware_actor_commits": "identity.commits",
        "aware_actor_subscriptions": "identity.subscriptions",
    }
    assert all(view.state_model_ref is None for view in mounted_views.values())


def test_experience_api_view_mounts_do_not_feed_generated_api_compile_plan(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_experience_toml(root=root)
    _write_actor_experience_sources(root=root)
    composition_path = _write_identity_composition_truth(root=root)

    experience_plan = build_experience_compile_plan(
        snapshot=ExperienceWorkspace.from_toml(
            toml_path=root / "aware.experience.toml",
            repo_root=root,
        ).build_snapshot(),
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert (
        build_experience_view_api_compile_plan(
            experience_plan=experience_plan,
        )
        is None
    )
    artifact = emit_experience_view_api_compile_plan_artifact(
        experience_plan=experience_plan,
        repo_root=root,
    )
    assert artifact is None


def test_experience_view_actions_fail_closed_to_api_owned_capabilities(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_experience_toml(root=root)
    _write_actor_experience_source_with_view_action(root=root)
    composition_path = _write_identity_composition_truth(root=root)

    with pytest.raises(
        ValueError,
        match="API-owned ApiViewCapabilityEndpoint owns view actions",
    ):
        build_experience_compile_plan(
            snapshot=ExperienceWorkspace.from_toml(
                toml_path=root / "aware.experience.toml",
                repo_root=root,
            ).build_snapshot(),
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


def test_experience_api_view_mount_does_not_generate_view_api(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_experience_toml(root=root)
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience aware_actor_roles on aware_identity.identity.Identity {",
                "  observable actor {",
                "    view roles.v1 default api_view identity.roles {}",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    composition_path = _write_identity_composition_truth(root=root)

    plan = build_experience_compile_plan(
        snapshot=ExperienceWorkspace.from_toml(
            toml_path=root / "aware.experience.toml",
            repo_root=root,
        ).build_snapshot(),
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert plan.view_api_ownership is None
    assert plan.view_state_model_contracts == ()
    view = plan.projection_experience_ownership[0].observables[0].views[0]
    assert view.api_view_ref == "identity.roles"
    assert view.state_model_ref is None
    assert build_experience_view_api_compile_plan(experience_plan=plan) is None


def test_experience_declares_generated_view_api_semantic_outputs() -> None:
    assert len(EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS) == 1
    artifact_output = EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS[0]
    assert artifact_output.semantic_owner == EXPERIENCE_PROVIDER_OWNER
    assert artifact_output.producer_key == EXPERIENCE_VIEW_API_PRODUCER_KEY
    assert artifact_output.output_key == EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY
    assert artifact_output.artifact_family == "api_compile_plan"
    assert artifact_output.required is False
    assert (
        artifact_output.runtime_contract_version
        == EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION
    )
    assert artifact_output.provider_payload == {
        "target_provider_key": EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
        "target_semantic_owner": EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER,
        "target_input_key": EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
        "schema_version": 10,
    }

    assert len(EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS) == 1
    package_output = EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS[0]
    assert package_output.semantic_owner == EXPERIENCE_PROVIDER_OWNER
    assert package_output.producer_key == EXPERIENCE_VIEW_API_PRODUCER_KEY
    assert package_output.output_key == EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY
    assert package_output.target_provider_key == EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY
    assert package_output.target_semantic_owner == (
        EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER
    )
    assert package_output.target_input_key == EXPERIENCE_VIEW_API_TARGET_INPUT_KEY
    assert package_output.input_artifact_output_key == (
        EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY
    )
    assert package_output.input_artifact_family == "api_compile_plan"
    assert package_output.required is False
    assert (
        package_output.runtime_contract_version
        == EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION
    )


def test_experience_generated_view_api_outputs_resolve_through_registry() -> None:
    _bootstrap_experience_module_plugin()

    artifact_outputs = AwareModulePluginRegistry.semantic_materialization_artifact_outputs_for_provider_key(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        output_key=EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY,
        artifact_family="api_compile_plan",
        required_for="workspace.semantic_materialization",
    )
    package_outputs = AwareModulePluginRegistry.semantic_materialization_package_outputs_for_provider_key(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        output_key=EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY,
        target_provider_key=EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
        target_input_key=EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
        required_for="workspace.semantic_materialization",
    )

    assert artifact_outputs == EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS
    assert package_outputs == EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS


def test_experience_workspace_provider_does_not_emit_view_api_package_for_api_views(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_experience_toml(root=root)
    _write_actor_experience_sources(root=root)
    (root / "aware.environment.toml").write_text(
        "aware_environment = 1\n",
        encoding="utf-8",
    )
    request = SemanticPackageMaterializationRequest(
        runtime=None,
        index=None,
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=root,
        manifest_path=root / "aware.experience.toml",
    )

    output = _emit_view_api_package_output(
        request=request,
        source_package_key="aware-actor",
    )

    assert output is None


def test_experience_workspace_provider_skips_api_view_language_contract_packages(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text("aware = 1\n", encoding="utf-8")
    (root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "aware-goals"',
                'fqn_prefix = "aware_goals"',
                'description = "Goal view contracts."',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                "",
                "[targets.dart]",
                'root_dir = "languages/dart"',
                'package_dir = "aware_goals"',
                "",
                "[targets.python]",
                'root_dir = "languages/python"',
                'package_dir = "aware_goals"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience aware_goals on aware_workflow.goal.Goal {",
                "  observable workflow {",
                "    view goal.v1 default api_view workflow.goal {}",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    view_path = root / "views" / "goal" / "home" / "v1.aware"
    view_path.parent.mkdir(parents=True, exist_ok=True)
    view_path.write_text(
        "\n".join(
            [
                "class GoalLaneViewStateV1 : inline_value {",
                "  lane_key String",
                '  status String = "planned"',
                "}",
                "",
                "class GoalHomeViewStateV1 : inline_value {",
                '  title String = "Goal"',
                "  lanes GoalLaneViewStateV1[] = []",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    request = SemanticPackageMaterializationRequest(
        runtime=None,
        index=None,
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=root,
        manifest_path=root / "aware.experience.toml",
    )

    packages = _materialize_language_contract_packages(request=request)

    assert packages == ()
    assert not (root / "languages").exists()


def _write_experience_toml(*, root: Path) -> None:
    (root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "aware-actor"',
                'fqn_prefix = "aware_actor"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_actor_experience_sources(*, root: Path) -> None:
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience aware_actor_roles on aware_identity.identity.Identity {",
                "  observable actor {",
                "    view roles.v1 default api_view identity.roles {}",
                "  }",
                "}",
                "",
                "experience aware_actor_commits on aware_identity.identity.Identity {",
                "  observable actor {",
                "    view commits.v1 default api_view identity.commits {}",
                "  }",
                "}",
                "",
                "experience aware_actor_subscriptions on aware_identity.identity.Identity {",
                "  observable actor {",
                "    view subscriptions.v1 default api_view identity.subscriptions {}",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_actor_experience_source_with_view_action(*, root: Path) -> None:
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience aware_actor_roles on aware_identity.identity.Identity {",
                "  observable actor {",
                "    view roles.v1 default api_view identity.roles {",
                "      action admit_identity view {",
                '        label "Admit identity";',
                "        receipt show_receipt;",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_identity_composition_truth(*, root: Path) -> Path:
    runtime_dir = (
        root
        / "modules"
        / "identity"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
    )
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "environment.manifest.json").write_text(
        json.dumps(
            {
                "opg_index": {"file": "opg.index.json"},
                "bindings": {"file": "bindings.manifest.json"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_dir / "opg.index.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "model": "Identity",
                        "projection_hash": "identity",
                        "file": "opgs/identity.json",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    opg_dir = runtime_dir / "opgs"
    opg_dir.mkdir(parents=True, exist_ok=True)
    (opg_dir / "identity.json").write_text(
        json.dumps(
            {
                "object_projection_graph_nodes": [
                    {"class_config_id": "identity-class", "is_root": True}
                ],
                "object_projection_graph_identity": {
                    "object_projection_graph_observables": [
                        {
                            "observable_key": "actor",
                            "key": "Identity:actor",
                        }
                    ]
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_dir / "bindings.manifest.json").write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "class_fqn": "aware_identity_ontology.identity.identity.Identity",
                        "canonical_class_config_id": "identity-class",
                        "sql_mapping": [{"attribute_name": "id"}],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    composition_path = root / ".aware" / "tmp" / "environment.composition.manifest.json"
    composition_path.parent.mkdir(parents=True, exist_ok=True)
    composition_path.write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "module_id": "identity",
                        "manifest_path": (
                            "modules/identity/structure/ontology/.aware/"
                            "environment/runtime/environment.manifest.json"
                        ),
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return composition_path
