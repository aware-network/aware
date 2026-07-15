from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.semantic_source_meaning import resolve_code_semantic_source_meaning
from aware_code.source_index import CodeGrammarSource, CodeGrammarSourceIndex
from aware_code_service_dto.code.features.semantic_source_meaning import (
    CodeSemanticSourceMeaningContract as DtoCodeSemanticSourceMeaningContract,
)
from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_code.semantic_currentness import (
    SemanticMaterializationCurrentnessReplayRequest,
    resolve_semantic_materialization_currentness_replay_adapter,
)
from aware_experience.semantic_contract import (
    EXPERIENCE_CONNECTOR_OWNER,
    EXPERIENCE_MANIFEST_RESOLUTION,
    EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS,
    EXPERIENCE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    EXPERIENCE_MATERIALIZATION_RUNTIME,
    EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT,
    EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    EXPERIENCE_PROVIDER_OWNER,
    EXPERIENCE_GRAMMAR_RULE_DECLARATIONS,
    EXPERIENCE_PROFILE_OWNER,
    EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_PARTICIPATION,
    EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT,
    EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_EXECUTION_POLICY,
    EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_PARTICIPATION,
    EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
    EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
    EXPERIENCE_SYNTAX_LANES,
)
from aware_experience.materialization.currentness_replay import (
    resolve_currentness_replay,
)
from aware_code.semantic_materialization import SemanticPackageMaterializationBundle
from uuid import uuid4


_EXPERIENCE_MODULE_ROOT = Path(__file__).resolve().parents[4]


def test_experience_semantic_contract_registers_currentness_replay_adapter() -> None:
    [participation] = EXPERIENCE_MATERIALIZATION_CAPABILITY_PARTICIPATION
    adapter = resolve_semantic_materialization_currentness_replay_adapter(
        capability_metadata=participation.metadata or {},
    )
    assert adapter is resolve_currentness_replay


@pytest.mark.asyncio
async def test_experience_currentness_replay_requires_live_package_and_outputs(
    tmp_path: Path,
) -> None:
    branch_id = uuid4()
    package_id = uuid4()
    package_commit_id = uuid4()
    projection_hash = "sha256:experience-package"
    package_root = tmp_path / "generated" / "experience"
    output_path = package_root / "models.py"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("VALUE = 1\n", encoding="utf-8")
    output_hash = __import__("hashlib").sha256(output_path.read_bytes()).hexdigest()

    async def _read_head(*, branch_id: object, projection_hash: str):
        return {"object_instance_graph_commit_id": package_commit_id}

    bundle = SemanticPackageMaterializationBundle(
        package_key="example-experience",
        manifest_toml_path=Path("example/aware.experience.toml"),
        semantic_package_id=package_id,
        semantic_root_id=package_id,
        semantic_branch_id=branch_id,
        semantic_projection_hash=projection_hash,
        semantic_object_instance_graph_commit_id=package_commit_id,
        runtime_code_package_refs=({"package_name": "example-runtime"},),
    )
    request = SemanticMaterializationCurrentnessReplayRequest(
        provider_key="aware_experience",
        semantic_owner="aware_experience.provider",
        workspace_root=tmp_path,
        workspace_manifest_kind="experience",
        semantic_package_family="experience",
        semantic_package_kind="experience_package",
        input_proof={"kind": "declared_source_tree", "complete": True},
        bundles=(bundle,),
        read_head=_read_head,
        replay_output_details={
            "generated_code_package_deltas": (
                {
                    "package_name": "example-runtime",
                    "package_root": "generated/experience",
                    "paths": (
                        {
                            "relative_path": "models.py",
                            "after_hash": output_hash,
                        },
                    ),
                },
            ),
        },
    )

    current = await resolve_currentness_replay(request)
    assert current.status == "reused"
    assert current.replay_kind == "previous_experience_output_bundles"

    output_path.write_text("VALUE = 2\n", encoding="utf-8")
    stale = await resolve_currentness_replay(request)
    assert stale.status == "must_execute"
    assert stale.reason == "experience_generated_output_mismatch"


def _experience_profile_source_index(*, title: str) -> CodeGrammarSourceIndex:
    source_text = "\n".join(
        (
            "experience home_story {",
            "    profile os.default {",
            f'        title "{title}"',
            "    }",
            "}",
            "",
        )
    )
    return CodeGrammarSourceIndex.from_sources(
        (
            CodeGrammarSource(
                source_key="profiles.aware",
                relative_path="profiles.aware",
                source_text=source_text,
            ),
        )
    )


def _bootstrap_experience_module_plugin() -> None:
    AwareModulePluginRegistry.clear()
    AwareModulePluginRegistry.ensure_module_plugins_registered_from_module_roots(
        module_roots=(_EXPERIENCE_MODULE_ROOT,),
    )


def test_experience_manifest_resolution_exports_package_dependencies() -> None:
    assert len(EXPERIENCE_MANIFEST_RESOLUTION) == 1
    descriptor = EXPERIENCE_MANIFEST_RESOLUTION[0]

    assert descriptor.semantic_package_metadata is not None
    assert (
        descriptor.semantic_package_metadata["dependency_attribute_name"]
        == "dependencies"
    )


def test_experience_materialization_runtime_uses_ontology_package_names() -> None:
    assert len(EXPERIENCE_MATERIALIZATION_RUNTIME) == 1
    descriptor = EXPERIENCE_MATERIALIZATION_RUNTIME[0]

    assert descriptor.semantic_owner == EXPERIENCE_PROVIDER_OWNER
    assert (
        descriptor.runtime_ontology_package_names
        == EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert descriptor.lane_projection_name == "ExperiencePackage"
    assert descriptor.required_projection_names == (
        EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS
    )
    projection_packages = {
        package.package_name: package.projection_names
        for package in descriptor.runtime_projection_packages
    }
    assert projection_packages["identity-ontology"] == (
        "ActorConfig",
        "RoleConfig",
    )
    assert projection_packages["api-ontology"] == ("Api", "ApiPackage")
    assert projection_packages["code-ontology"] == ("CodePackage",)
    assert projection_packages["environment-ontology"] == ("ThreadConfig",)
    assert projection_packages["meta-ontology"] == ("ObjectInstanceGraphIdentity",)
    assert set(EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS).issubset(
        {
            projection_name
            for projection_names in projection_packages.values()
            for projection_name in projection_names
        }
    )
    assert "ExperiencePackage" in {
        projection_name
        for projection_names in projection_packages.values()
        for projection_name in projection_names
    }
    assert descriptor.include_package_dependency_closure is True


def test_experience_declares_connector_syntax_lane_and_required_projections() -> None:
    connector_lane = next(
        lane
        for lane in EXPERIENCE_SYNTAX_LANES
        if lane.semantic_owner == EXPERIENCE_CONNECTOR_OWNER
    )

    assert connector_lane.lane_key == "aware_experience.connector"
    assert connector_lane.grammar_rules == (
        "connector_def",
        "connector_provider_def",
        "connector_sensor_def",
        "connector_actuator_def",
        "connector_invocation_def",
    )
    assert {
        "ActuatorConfig",
        "ActuatorInvocationActionConfig",
        "ConnectorConfig",
        "ConnectorProvider",
        "EnvironmentExperience",
        "EnvironmentExperienceProfileConfig",
        "EnvironmentExperienceProfile",
        "EnvironmentTopologySeed",
        "ExperienceInvocationActionConfig",
        "ObjectInstanceGraphIdentity",
        "SensorConfig",
        "SensorInvocationActionConfig",
    }.issubset(set(EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS))


def test_experience_declares_profile_grammar_source_meaning_contract() -> None:
    profile_lane = next(
        lane
        for lane in EXPERIENCE_SYNTAX_LANES
        if lane.semantic_owner == EXPERIENCE_PROFILE_OWNER
    )
    assert profile_lane.lane_key == "aware_experience.profile"
    assert {
        "experience_profile_scope_def",
        "experience_profile_def",
        "experience_profile_title_stmt",
    }.issubset(set(profile_lane.grammar_rules))

    declarations = {
        declaration.rule_name: declaration
        for declaration in EXPERIENCE_GRAMMAR_RULE_DECLARATIONS
    }
    assert declarations["experience_profile_scope_def"].source_anchor_fields == (
        "name",
    )
    assert declarations["experience_profile_def"].source_anchor_fields == ("key",)
    assert declarations["experience_profile_title_stmt"].source_anchor_fields == (
        "title",
    )

    [participation] = EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_PARTICIPATION
    assert participation.capability == "semantic_source_meaning"
    assert participation.semantic_owner == EXPERIENCE_PROFILE_OWNER
    assert participation.metadata is not None
    dto_contract = DtoCodeSemanticSourceMeaningContract.model_validate(
        participation.metadata["source_meaning_contract"]
    )
    assert dto_contract.provider_key == "aware_experience"
    assert dto_contract.semantic_owner == EXPERIENCE_PROFILE_OWNER
    assert len(dto_contract.bindings[0].template_value_bindings) == 2
    assert len(dto_contract.bindings[0].typed_operation_bindings) == 1
    [binding] = EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT.bindings
    assert binding.grammar_rule_name == "experience_profile_title_stmt"
    assert binding.anchor_field_path == "title"
    assert tuple(
        (
            value.value_key,
            value.grammar_rule_name,
            value.field_path,
        )
        for value in binding.template_value_bindings
    ) == (
        (
            "experience_name",
            "experience_profile_scope_def",
            "name",
        ),
        ("profile_key", "experience_profile_def", "key"),
    )
    [operation_binding] = binding.typed_operation_bindings
    assert operation_binding.semantic_operation_type == (
        "aware_experience.profile.title.update"
    )
    assert operation_binding.event_verbs == ("update", "delete")
    [resolver_participation] = (
        EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION
    )
    assert resolver_participation.semantic_owner == EXPERIENCE_PROFILE_OWNER
    assert resolver_participation.metadata == (
        EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA
    )
    [projection_participation] = (
        EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_PARTICIPATION
    )
    assert projection_participation.capability == (
        "semantic_operation_source_projection_resolution"
    )
    assert projection_participation.semantic_owner == EXPERIENCE_PROFILE_OWNER
    [projection_policy] = (
        EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_EXECUTION_POLICY
    )
    assert projection_policy.callable_module == (
        "aware_experience.profile.source_projection"
    )
    assert projection_policy.callable_name == (
        "resolve_experience_profile_source_projection"
    )


def test_experience_profile_title_source_pair_resolves_through_code_contract() -> None:
    baseline = _experience_profile_source_index(title="Home Story OS")
    current = _experience_profile_source_index(title="Aware Home OS")

    resolution = resolve_code_semantic_source_meaning(
        contract=EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.status == "resolved"
    assert resolution.diagnostics == ()
    assert resolution.action_bindings == ()
    [delta] = resolution.semantic_deltas
    assert delta.semantic_key == "experience.profile:home_story:os.default"
    assert delta.subject_type == ("aware_experience.EnvironmentExperienceProfileConfig")
    assert delta.verb == "update"
    assert delta.before_payload is not None
    assert delta.before_payload["title"] == "Home Story OS"
    assert delta.after_payload is not None
    assert delta.after_payload["title"] == "Aware Home OS"
    [operation] = resolution.typed_operations
    assert operation.operation_key == (
        "aware_experience.profile.title:home_story:os.default:update"
    )
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_experience.profile.title.update"
    )
    assert operation.semantic_key == "experience.profile:home_story:os.default"
    assert operation.after_payload is not None
    assert operation.after_payload["title"] == "Aware Home OS"
    assert operation.requires_baseline_object_identity is True


def test_experience_declares_provider_owned_runtime_context() -> None:
    assert len(EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT) == 1
    descriptor = EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT[0]

    assert descriptor.semantic_owner == EXPERIENCE_PROVIDER_OWNER
    assert descriptor.callable_module == (
        "aware_experience.materialization.runtime_context"
    )
    assert descriptor.callable_name == (
        "build_experience_workspace_materialization_runtime_context"
    )
    assert descriptor.required is True
    assert descriptor.provider_payload is not None
    assert descriptor.provider_payload["runtime_ontology_package_names"] == (
        EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )


def test_experience_runtime_context_resolves_through_registry() -> None:
    _bootstrap_experience_module_plugin()
    descriptors = AwareModulePluginRegistry.semantic_materialization_runtime_context_for_provider_key(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
    )

    assert descriptors == EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT


def test_experience_runtime_context_callable_resolves_through_registry() -> None:
    _bootstrap_experience_module_plugin()
    resolvers = AwareModulePluginRegistry.resolve_semantic_materialization_runtime_context_resolvers(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
    )

    assert len(resolvers) == 1
    resolver = resolvers[0]
    assert resolver.provider_key == "aware_experience"
    assert resolver.semantic_owner == EXPERIENCE_PROVIDER_OWNER
    assert resolver.callable_module == (
        "aware_experience.materialization.runtime_context"
    )
    assert resolver.callable_name == (
        "build_experience_workspace_materialization_runtime_context"
    )
    assert resolver.required is True


def test_experience_runtime_context_uses_catalog_with_external_storage_dependency(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_experience.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    experience_manifest_path = (
        workspace_root / "experiences" / "demo" / "aware.experience.toml"
    )
    experience_manifest_path.parent.mkdir(parents=True)
    experience_manifest_path.write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "demo-experience"',
                'fqn_prefix = "demo_experience"',
                "",
                "[build]",
                'environment_handle = "kernel"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (experience_manifest_path.parent / "aware.programs.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "demo:BootInterface"',
                'path = "programs/boot_interface.aware"',
                'name = "BootInterface"',
                'dependencies = ["interface-ontology"]',
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifests = {
        "meta-ontology": repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        "code-ontology": repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        "api-ontology": repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        "interface-ontology": repo_root
        / "modules/interface/structure/ontology/aware.toml",
        "storage-ontology": repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        "identity-ontology": repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        "attention-ontology": repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        "reactivity-ontology": repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        "experience-ontology": repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    }
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_context,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )

    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=experience_manifest_path,
        context={
            "runtime_ontology_package_names": (
                "experience-ontology",
                "api-ontology",
            ),
            "required_projection_names": (
                "Api",
                "ApiPackage",
                "ExperiencePackage",
                "CodePackage",
            ),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    _catalog_entry(
                        package_name="meta-ontology",
                        manifest_path=manifests["meta-ontology"],
                        projection_names=("ObjectConfigGraphPackage",),
                    ),
                    _catalog_entry(
                        package_name="code-ontology",
                        manifest_path=manifests["code-ontology"],
                        dependency_package_names=("meta-ontology",),
                        projection_names=("CodePackage",),
                    ),
                    _catalog_entry(
                        package_name="api-ontology",
                        manifest_path=manifests["api-ontology"],
                        dependency_package_names=("meta-ontology", "code-ontology"),
                        projection_names=("Api", "ApiPackage"),
                    ),
                    _catalog_entry(
                        package_name="interface-ontology",
                        manifest_path=manifests["interface-ontology"],
                        dependency_package_names=(
                            "meta-ontology",
                            "code-ontology",
                            "experience-ontology",
                        ),
                        projection_names=("Interface", "InterfacePackage"),
                    ),
                    _catalog_entry(
                        package_name="storage-ontology",
                        manifest_path=manifests["storage-ontology"],
                        dependency_package_names=("meta-ontology",),
                    ),
                    _catalog_entry(
                        package_name="identity-ontology",
                        manifest_path=manifests["identity-ontology"],
                        dependency_package_names=("meta-ontology",),
                        projection_names=("RoleConfig",),
                    ),
                    _catalog_entry(
                        package_name="attention-ontology",
                        manifest_path=manifests["attention-ontology"],
                        dependency_package_names=("meta-ontology",),
                    ),
                    _catalog_entry(
                        package_name="reactivity-ontology",
                        manifest_path=manifests["reactivity-ontology"],
                        dependency_package_names=("meta-ontology",),
                    ),
                    _catalog_entry(
                        package_name="experience-ontology",
                        manifest_path=manifests["experience-ontology"],
                        dependency_package_names=(
                            "attention-ontology",
                            "meta-ontology",
                            "reactivity-ontology",
                            "storage-ontology",
                            "identity-ontology",
                            "code-ontology",
                        ),
                        projection_names=("ExperiencePackage",),
                    ),
                ],
            },
        },
        provider_payload={
            "runtime_ontology_package_names": (
                "experience-ontology",
                "api-ontology",
            ),
        },
    )

    resolved = (
        runtime_context.build_experience_workspace_materialization_runtime_context(
            request
        )
    )

    assert resolved is not None
    assert resolved.runtime is not None
    assert resolved.meta_context is not None
    assert captured["workspace_root"] == workspace_root
    package_manifest_paths = cast(tuple[Path, ...], captured["package_manifest_paths"])
    assert package_manifest_paths == (
        manifests["meta-ontology"],
        manifests["attention-ontology"],
        manifests["reactivity-ontology"],
        manifests["storage-ontology"],
        manifests["identity-ontology"],
        manifests["code-ontology"],
        manifests["experience-ontology"],
        manifests["api-ontology"],
        manifests["interface-ontology"],
    )
    assert manifests["storage-ontology"] in package_manifest_paths
    assert manifests["interface-ontology"] in package_manifest_paths
    assert experience_manifest_path not in package_manifest_paths
    assert captured["strict_package_graph_cache"] is True
    entries_by_manifest = captured["package_entries_by_manifest_path"]
    assert isinstance(entries_by_manifest, dict)
    assert (
        entries_by_manifest[manifests["interface-ontology"].resolve()].package_name
        == "interface-ontology"
    )
    owner_roots_by_manifest = captured["package_cache_owner_roots_by_manifest_path"]
    assert isinstance(owner_roots_by_manifest, dict)
    assert (
        owner_roots_by_manifest[manifests["interface-ontology"].resolve()]
        == repo_root.resolve()
    )


def test_experience_runtime_context_includes_declared_ontology_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_experience.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    conversation_ontology = (
        workspace_root / "ontologies" / "conversation" / "structure" / "aware.toml"
    )
    content_ontology = (
        repo_root / "modules" / "content" / "structure" / "ontology" / "aware.toml"
    )
    conversation_ontology.parent.mkdir(parents=True)
    content_ontology.parent.mkdir(parents=True)
    conversation_ontology.write_text("aware = 1\n", encoding="utf-8")
    content_ontology.write_text("aware = 1\n", encoding="utf-8")
    experience_manifest_path = (
        workspace_root / "experiences" / "demo" / "aware.experience.toml"
    )
    experience_manifest_path.parent.mkdir(parents=True)
    experience_manifest_path.write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "demo-experience"',
                'fqn_prefix = "demo_experience"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                "",
                "[[dependencies]]",
                'package_name = "conversation-ontology"',
                'kind = "ontology_package"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    experience_ontology = (
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml"
    )
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_context,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )

    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=experience_manifest_path,
        context={
            "runtime_ontology_package_names": ("experience-ontology",),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    _catalog_entry(
                        package_name="content-ontology",
                        manifest_path=content_ontology,
                    ),
                    _catalog_entry(
                        package_name="conversation-ontology",
                        manifest_path=conversation_ontology,
                        dependency_package_names=("content-ontology",),
                    ),
                    _catalog_entry(
                        package_name="experience-ontology",
                        manifest_path=experience_ontology,
                    ),
                ],
            },
        },
    )

    resolved = (
        runtime_context.build_experience_workspace_materialization_runtime_context(
            request
        )
    )

    assert resolved is not None
    assert captured["package_manifest_paths"] == (
        experience_ontology,
        content_ontology,
        conversation_ontology,
    )


def test_experience_runtime_context_includes_source_module_ontology(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_experience.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    module_root = workspace_root / "modules" / "home"
    experience_manifest_path = (
        module_root / "experiences" / "home_story" / "aware.experience.toml"
    )
    ontology_package_manifest = module_root / "ontology" / "aware.ontology.toml"
    home_ontology = module_root / "ontology" / "structure" / "aware.toml"
    experience_ontology = (
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml"
    )
    experience_manifest_path.parent.mkdir(parents=True)
    ontology_package_manifest.parent.mkdir(parents=True)
    home_ontology.parent.mkdir(parents=True)
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "ontology/aware.ontology.toml"',
                "",
                "[[packages]]",
                'id = "home_story_experience"',
                'kind = "experience"',
                'manifest = "experiences/home_story/aware.experience.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ontology_package_manifest.write_text(
        "\n".join(
            [
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'source_manifest = "structure/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    home_ontology.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    experience_manifest_path.write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "home-story"',
                'fqn_prefix = "home_story"',
                "",
                "[build]",
                'environment_handle = "home-story"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_context,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )

    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=experience_manifest_path,
        context={
            "runtime_ontology_package_names": ("experience-ontology",),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    _catalog_entry(
                        package_name="experience-ontology",
                        manifest_path=experience_ontology,
                    ),
                ],
            },
        },
    )

    resolved = (
        runtime_context.build_experience_workspace_materialization_runtime_context(
            request
        )
    )

    assert resolved is not None
    assert captured["package_manifest_paths"] == (
        experience_ontology,
        home_ontology,
    )
    entries_by_manifest = captured["package_entries_by_manifest_path"]
    assert isinstance(entries_by_manifest, dict)
    assert entries_by_manifest[home_ontology].package_name == "home-ontology"
    assert entries_by_manifest[home_ontology].module_id == "home"
    owner_roots_by_manifest = captured["package_cache_owner_roots_by_manifest_path"]
    assert isinstance(owner_roots_by_manifest, dict)
    assert owner_roots_by_manifest[home_ontology] == module_root.resolve()


def test_experience_runtime_context_local_package_entries_are_same_module_only(
    tmp_path: Path,
) -> None:
    import aware_experience.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    module_root = workspace_root / "modules" / "home"
    same_module_manifest = module_root / "ontology" / "structure" / "aware.toml"
    unrelated_manifest = (
        workspace_root / "other" / "ontology" / "structure" / "aware.toml"
    )
    same_module_manifest.parent.mkdir(parents=True)
    unrelated_manifest.parent.mkdir(parents=True)
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "ontology/structure/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    same_module_manifest.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    unrelated_manifest.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "other-ontology"',
                'fqn_prefix = "aware_other"',
                'kind = "ontology"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=None,
        context={
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [],
            },
        },
    )

    entries = runtime_context._package_entries_by_manifest_path_for_request(
        request=request,
        manifest_paths=(same_module_manifest, unrelated_manifest),
        source_module_ontology_manifest_paths=(same_module_manifest,),
    )
    owner_roots = (
        runtime_context._package_cache_owner_roots_by_manifest_path_for_request(
            request=request,
            manifest_paths=(same_module_manifest, unrelated_manifest),
            source_module_ontology_manifest_paths=(same_module_manifest,),
        )
    )

    assert entries is not None
    assert entries[same_module_manifest].package_name == "home-ontology"
    assert unrelated_manifest not in entries
    assert owner_roots[same_module_manifest] == module_root.resolve()
    assert unrelated_manifest not in owner_roots


def test_experience_runtime_context_ignores_non_ontology_package_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_experience.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    experience_manifest_path = (
        workspace_root / "experiences" / "actor" / "aware.experience.toml"
    )
    experience_manifest_path.parent.mkdir(parents=True)
    experience_manifest_path.write_text(
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
                "",
                "[[dependencies]]",
                'package_name = "aware-control"',
                'kind = "experience_package"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    experience_ontology = (
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml"
    )
    captured: dict[str, object] = {}

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_context,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )

    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=experience_manifest_path,
        context={
            "runtime_ontology_package_names": ("experience-ontology",),
            SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
                "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
                "entries": [
                    _catalog_entry(
                        package_name="experience-ontology",
                        manifest_path=experience_ontology,
                    ),
                ],
            },
        },
    )

    resolved = (
        runtime_context.build_experience_workspace_materialization_runtime_context(
            request
        )
    )

    assert resolved is not None
    assert captured["package_manifest_paths"] == (experience_ontology,)


def _catalog_entry(
    *,
    package_name: str,
    manifest_path: Path,
    dependency_package_names: tuple[str, ...] = (),
    projection_names: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "module_id": package_name.removesuffix("-ontology"),
        "package_name": package_name,
        "fqn_prefix": package_name.replace("-", "_"),
        "manifest_path": manifest_path.as_posix(),
        "dependency_package_names": list(dependency_package_names),
        "projection_names": list(projection_names),
    }
