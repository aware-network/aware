from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code.semantic_materialization import SemanticPackageMaterializationRequest
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackagePathRole,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentProfileInstallSpec,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)
from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
)
from aware_api_ontology.api.api_view_capability_endpoint import (
    ApiViewCapabilityEndpoint,
)

from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_branch import (
    ProjectionExperienceBranch,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience_view_state_provider import (
    ProjectionExperienceViewStateProvider,
)
from aware_experience.materialization.projection_snapshot_preservation import (
    merge_projection_node_snapshots,
    preserve_projection_branch_snapshots_from_session,
    preserve_projection_node_snapshots_from_session,
    preserve_projection_view_snapshots_from_session,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceLayoutGraphBindingSnapshot,
    ExperienceProjectionNodeSnapshot,
    ExperienceSectionGraphBindingSnapshot,
)
import aware_experience.materialization.snapshot_commit as snapshot_commit
from aware_experience.graph.materialization.service import (
    ProjectionExperienceGraphIdentityEdgeMaterializationSpec,
    ProjectionExperienceGraphIdentityMaterializationSpec,
    ProjectionExperienceGraphMaterializationSpec,
    ProjectionExperienceNodeIdentityEdgeMaterializationSpec,
    ProjectionExperienceNodeMaterializationSpec,
    build_graph_materialization_plan,
    decode_graph_materialization_step_payload,
    encode_graph_materialization_step_payload,
    _relationship_token_matches_target_leaf,
    resolve_graph_materialization_specs,
)
import aware_experience.graph.materialization.service as graph_materialization_service
from aware_experience.materialization.service import (
    ActorMaterializationSpec,
    ActionMaterializationSpec,
    ActuatorConfigMaterializationSpec,
    ConnectorConfigMaterializationSpec,
    ConnectorInvocationActionConfigMaterializationSpec,
    ConnectorProviderMaterializationSpec,
    EnvironmentProfileMaterializationSpec,
    EnvironmentProfileProcessMaterializationSpec,
    EnvironmentProfileThreadMaterializationSpec,
    EnvironmentProfileThreadLayoutMaterializationSpec,
    EnvironmentProfileThreadLayoutSectionMaterializationSpec,
    EnvironmentProfileThreadProjectionMaterializationSpec,
    EnvironmentProfileViewEventTransitionMaterializationSpec,
    ProjectionExperienceMaterializationSpec,
    ProjectionExperienceLayoutGraphBindingSpec,
    ProjectionExperienceSectionSurfaceBindingSpec,
    ProjectionExperienceSectionSurfaceMaterializationSpec,
    ProjectionExperienceViewMaterializationSpec,
    build_actor_materialization_plan,
    build_action_materialization_plan,
    build_connector_config_materialization_plan,
    build_environment_profile_materialization_plan,
    build_projection_materialization_plan,
    build_section_surface_materialization_plan,
    decode_actor_materialization_step_payload,
    decode_connector_config_materialization_step_payload,
    decode_environment_profile_materialization_step_payload,
    decode_projection_materialization_step_payload,
    decode_section_surface_materialization_step_payload,
    encode_actor_materialization_step_payload,
    encode_connector_config_materialization_step_payload,
    encode_environment_profile_materialization_step_payload,
    encode_projection_materialization_step_payload,
    encode_section_surface_materialization_step_payload,
    load_experience_compile_plan_payloads,
    materialize_experience_compile_plan_actors,
    materialize_experience_compile_plan_actions,
    materialize_experience_connector_config_ontology,
    materialize_experience_compile_plan_environment_profiles,
    materialize_experience_compile_plan_projections,
    materialize_experience_compile_plan_graphs,
    materialize_experience_compile_plan_section_surfaces,
    resolve_activation_target_materialization_specs,
    resolve_actor_materialization_specs,
    resolve_environment_profile_materialization_specs,
    resolve_action_materialization_specs,
    resolve_connector_config_materialization_specs,
    resolve_projection_materialization_specs,
    resolve_section_surface_materialization_specs,
    SensorConfigMaterializationSpec,
)


from aware_experience_ontology.stable_ids import (
    stable_projection_experience_id,
    stable_projection_experience_layout_graph_binding_id,
    stable_projection_experience_layout_section_graph_binding_id,
    stable_projection_experience_section_graph_binding_id,
)
from aware_meta.materialization import (
    MaterializationLaneContext,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
import aware_experience.materialization.service as materialization_service
import aware_experience.materialization.projection_contract_materialization as projection_contract_materialization
import aware_experience.materialization.workspace_provider as experience_workspace_provider


@pytest.mark.asyncio
async def test_snapshot_no_change_uses_committed_head_oig_identity() -> None:
    branch_id = uuid4()
    head_commit_id = uuid4()
    committed_oigi_id = uuid4()
    runtime_oigi_id = uuid4()
    expected_oig_commit_id = snapshot_commit.stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=committed_oigi_id,
        commit_id=head_commit_id,
    )
    assert expected_oig_commit_id != (
        snapshot_commit.stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=runtime_oigi_id,
            commit_id=head_commit_id,
        )
    )

    class _CommitStore:
        async def get_commit_identity_metadata(self, **_kwargs: object):
            return SimpleNamespace(
                object_instance_graph_identity_id=committed_oigi_id,
            )

        async def get_commit(self, **_kwargs: object):
            raise AssertionError("identity metadata is the committed authority")

    result = await snapshot_commit._committed_oig_commit_id_for_head(  # noqa: SLF001
        commit_store=cast(Any, _CommitStore()),
        branch_id=branch_id,
        projection_hash="experience-package-projection",
        head_commit_id=head_commit_id,
        head={"object_instance_graph_commit_id": str(expected_oig_commit_id)},
        operation_label="ExperiencePackage.materialize_manifest_snapshot",
    )

    assert result == expected_oig_commit_id


class _NoOpRuntimeInvoker:
    async def invoke_function_with_index(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        request: InvokeFunctionRequest,
    ) -> InvokeFunctionResponse:
        _ = index, request
        raise AssertionError(
            "invoke_function_with_index should not run in skip-path tests"
        )


class _NoOpRuntime:
    manifest_path: Path = Path(".")
    invoker: object = _NoOpRuntimeInvoker()


def test_experience_workspace_provider_forwards_dependency_reference_branch_context() -> (
    None
):
    conversation_branch_id = uuid4()

    branch_ids = (
        experience_workspace_provider._experience_reference_branch_ids_from_context(
            context={
                "experience_reference_branch_ids_by_experience_name": {
                    "Aware_Conversation_Spaces": str(conversation_branch_id),
                }
            }
        )
    )

    assert branch_ids == {
        "Aware_Conversation_Spaces": conversation_branch_id,
        "aware_conversation_spaces": conversation_branch_id,
    }


def _write_test_experience_toml(
    *,
    package_root: Path,
    package_name: str,
    fqn_prefix: str,
    dependencies: tuple[str, ...] = (),
) -> None:
    package_root.mkdir(parents=True, exist_ok=True)
    lines = [
        "aware_experience = 1",
        "",
        "[experience]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        "version_number = 1",
        f'title = "{package_name}"',
        "",
        "[build]",
        'environment_handle = "kernel"',
        'sources_dir = "."',
        'include_paths = ["**/*.aware"]',
        "exclude_paths = []",
        "force_fresh_scan = true",
    ]
    for dependency in dependencies:
        lines.extend(
            [
                "",
                "[[dependencies]]",
                f'package_name = "{dependency}"',
                'kind = "experience_package"',
            ]
        )
    (package_root / "aware.experience.toml").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


class _ObjectListSession:
    def __init__(self, *objects: object) -> None:
        self._objects = objects

    def imap_all_objects(self) -> tuple[object, ...]:
        return self._objects


@pytest.mark.asyncio
async def test_environment_profile_materialization_initializes_profile_lane_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit_id = uuid4()
    head_commit_id = uuid4()
    function_id = uuid4()
    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="EnvironmentExperience",
    )
    captured: dict[str, object] = {}

    async def _fake_invoke_constructor(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(
            status="succeeded",
            error=None,
            commit_id=commit_id,
            object_instance_graph_commit_id=head_commit_id,
        )

    async def _fake_lane_head_commit_id(**kwargs: object) -> None:
        _ = kwargs
        return None

    monkeypatch.setattr(
        materialization_service,
        "_invoke_constructor_environment_function",
        _fake_invoke_constructor,
    )
    monkeypatch.setattr(
        materialization_service,
        "_lane_head_commit_id",
        _fake_lane_head_commit_id,
    )

    result = (
        await materialization_service._ensure_environment_experience_profile_lane_root(
            runtime=_NoOpRuntime(),
            index=cast(MetaGraphRuntimeIndex, object()),
            actor_id=None,
            lane=lane,
            function_id=function_id,
            spec=EnvironmentProfileMaterializationSpec(
                fqn_prefix="aware_actor",
                experience_name="aware_actor_roles",
                key="actor.home",
                source_path="profiles.aware",
                title="Actor Home",
                description="Default actor workspace.",
            ),
        )
    )

    assert result.commit_id == commit_id
    assert result.head_commit_id == head_commit_id
    assert captured["lane"] == lane
    assert captured["function_id"] == function_id
    assert captured["args"] == [
        "aware_actor",
        "Actor Home",
        "Default actor workspace.",
    ]


@pytest.mark.asyncio
async def test_environment_profile_materialization_requires_environment_api_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="ProjectionExperience",
    )
    spec = EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware_actor",
        experience_name="aware_actor_roles",
        key="actor.home",
        source_path="profiles.aware",
        title="Actor Home",
        description="Default actor workspace.",
    )

    monkeypatch.setattr(
        materialization_service,
        "resolve_environment_profile_materialization_specs",
        lambda **_: (spec,),
    )

    with pytest.raises(RuntimeError, match="requires an Environment API client"):
        await materialization_service.materialize_experience_environment_profile_ontology(
            runtime=_NoOpRuntime(),
            index=cast(MetaGraphRuntimeIndex, object()),
            actor_id=None,
            lane=lane,
            environment_id=uuid4(),
            compile_plan_payloads=({"environment_profile_ownership": []},),
            prefer_snapshot_materialization=True,
        )


@pytest.mark.asyncio
async def test_environment_profile_materialization_maps_topology_to_environment_api() -> (
    None
):
    actor_id = uuid4()
    environment_id = uuid4()
    environment_profile_config_id = uuid4()
    layout_config_id = stable_layout_config_id(key="actor.home")
    captured: dict[str, UpsertEnvironmentProfileRequest] = {}

    class _ProfileApi:
        async def upsert_environment_profile(
            self,
            request: UpsertEnvironmentProfileRequest,
        ) -> UpsertEnvironmentProfileResponse:
            captured["request"] = request
            return UpsertEnvironmentProfileResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="succeeded",
                environment_profile_config_id=environment_profile_config_id,
                environment_profile_id=uuid4(),
            )

    environment_api_client = SimpleNamespace(
        environment=SimpleNamespace(profile=_ProfileApi())
    )
    spec = EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware_actor",
        experience_name="aware_actor_roles",
        key="actor.home",
        source_path="profiles.aware",
        title="Actor Home",
        description="Default actor workspace.",
        process_configs=(
            EnvironmentProfileProcessMaterializationSpec(
                type="continuous",
                key="control",
                process_key="control",
                source_path="profiles.aware",
                thread_configs=(
                    EnvironmentProfileThreadMaterializationSpec(
                        key="main",
                        thread_key="main",
                        source_path="profiles.aware",
                        workspace_view_key="actor.home",
                        projection_experiences=(
                            EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name="aware_actor_roles",
                                projection_key="actor.role",
                                source_path="profiles.aware",
                                view_key="role.default",
                                is_default=True,
                            ),
                        ),
                        layout_configs=(
                            EnvironmentProfileThreadLayoutMaterializationSpec(
                                layout_key="actor.home",
                                layout_config_id=layout_config_id,
                                source_path="profiles.aware",
                                key="home.layout",
                                sections=(
                                    EnvironmentProfileThreadLayoutSectionMaterializationSpec(
                                        section_key="primary",
                                        projection_experience_name=(
                                            "aware_actor_roles"
                                        ),
                                        projection_key="actor.role",
                                        view_key="role.default",
                                        source_path="profiles.aware",
                                        key="primary",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    response = await materialization_service._upsert_environment_profile_via_api(
        environment_api_client=environment_api_client,
        actor_id=actor_id,
        environment_id=environment_id,
        spec=spec,
    )

    assert response.status == "succeeded"
    request = captured["request"]
    assert request.actor_id == actor_id
    assert request.environment_id == environment_id
    assert isinstance(request.profile, EnvironmentProfileInstallSpec)
    assert request.profile.key == "actor.home"
    process = request.profile.process_configs[0]
    assert process.key == "control"
    assert process.type == "continuous"
    thread = process.thread_configs[0]
    assert thread.key == "main"
    assert thread.workspace_view_key == "actor.home"
    assert thread.projection_refs[0].object_projection_graph_ref == "actor.role"
    assert thread.projection_refs[0].view_key == "role.default"
    layout = thread.layout_configs[0]
    assert layout.layout_key == "actor.home"
    assert layout.layout_config_id == layout_config_id
    assert layout.key == "home.layout"
    section = layout.sections[0]
    assert section.section_key == "primary"
    assert section.object_projection_graph_ref == "actor.role"
    assert section.view_key == "role.default"
    assert section.layout_config_section_config_id == (
        stable_layout_config_section_config_id(
            layout_config_id=layout_config_id,
            section_key="primary",
        )
    )


def test_environment_profile_materialization_requires_config_and_applied_identity() -> (
    None
):
    spec = EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware_actor",
        experience_name="aware_actor_roles",
        key="actor.home",
        source_path="profiles.aware",
    )
    response = UpsertEnvironmentProfileResponse(
        status="succeeded",
        environment_id=uuid4(),
        environment_profile_id=uuid4(),
    )

    with pytest.raises(RuntimeError, match="omitted EnvironmentProfileConfig identity"):
        materialization_service._require_environment_profile_identity(
            response=response,
            spec=spec,
        )


@pytest.mark.asyncio
async def test_experience_workspace_provider_reports_full_rebuild_fallback_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_code_package_id = uuid4()
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    package_oig_commit_id = uuid4()
    profile_branch_id = uuid4()
    profile_oig_id = uuid4()
    profile_oig_commit_id = uuid4()
    profile_head_commit_id = uuid4()
    captured_materialize_kwargs: dict[str, object] = {}

    async def _fake_materialize_experience_package_from_manifest(**kwargs: object):
        captured_materialize_kwargs.update(kwargs)
        return SimpleNamespace(
            experience_toml_path=tmp_path / "aware.experience.toml",
            workspace_root=tmp_path,
            manifest_spec=SimpleNamespace(
                experience=SimpleNamespace(
                    package_name="home-story-experience",
                    description=None,
                ),
                targets={},
                build=SimpleNamespace(environment_handle="home"),
            ),
            experience_name="home",
            experience_names=("home",),
            environment_experience=SimpleNamespace(id=uuid4()),
            experience_package=SimpleNamespace(
                name="home-story-experience",
                id=uuid4(),
            ),
            language_contract_packages=(),
            source_code_package_id=source_code_package_id,
            experience_source_path="experience/home.aware",
            source_files=("experience/home.aware",),
            phase_timings_s={},
            environment_experience_commit_id=uuid4(),
            projection_experience_commit_id=uuid4(),
            projection_experience_head_commit_id=uuid4(),
            projection_experience_graph_commit_id=uuid4(),
            projection_experience_graph_head_commit_id=uuid4(),
            projection_experience_section_surface_commit_id=uuid4(),
            projection_experience_section_surface_head_commit_id=uuid4(),
            activation_profile_config_branch_id=profile_branch_id,
            activation_profile_config_projection_hash="profile-projection-hash",
            activation_profile_config_domain_object_instance_graph_id=profile_oig_id,
            activation_profile_config_object_instance_graph_commit_id=(
                profile_oig_commit_id
            ),
            activation_profile_config_head_commit_id=profile_head_commit_id,
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
            package_projection_hash="experience-package-projection-hash",
            package_object_instance_graph_commit_id=package_oig_commit_id,
        )

    monkeypatch.setattr(
        experience_workspace_provider,
        "materialize_experience_package_from_manifest",
        _fake_materialize_experience_package_from_manifest,
    )
    monkeypatch.setattr(
        experience_workspace_provider,
        "resolve_experience_profile_publication_summary",
        lambda **_: SimpleNamespace(
            experience_handle="home",
            profiles=(SimpleNamespace(experience_name="home", key="os.default"),),
        ),
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.experience.toml",
        code_package_delta=CodePackageDelta(
            package_name="home-story-experience",
            paths=[
                CodePackageDeltaPath(
                    relative_path="experience/home.aware",
                    kind=CodePackageDeltaKind.update,
                    language=CodeLanguage.aware,
                    is_structural=True,
                )
            ],
        ),
        change_preview={"affected_semantic_keys": ("home",)},
    )

    result = await experience_workspace_provider.materialize(request)

    assert result.mode == "full_rebuild"
    assert captured_materialize_kwargs["prefer_snapshot_environment_profiles"] is True
    assert result.affected_semantic_keys == ("home",)
    assert result.applied_semantic_keys == ("home",)
    assert result.fallback_reason is not None
    assert "not implemented delta materialization" in result.fallback_reason
    assert result.commit_id == package_commit_id
    assert result.head_commit_id == package_head_commit_id
    assert (
        result.bundle_packages[0].semantic_object_instance_graph_commit_id
        == package_oig_commit_id
    )
    assert (
        result.bundle_packages[0].semantic_projection_hash
        == "experience-package-projection-hash"
    )
    [identity] = result.current_semantic_object_identities
    assert identity.domain_branch_id == str(profile_branch_id)
    assert identity.projection_hash == "profile-projection-hash"
    assert identity.domain_object_instance_graph_id == str(profile_oig_id)
    assert identity.object_instance_graph_commit_id == str(profile_oig_commit_id)
    assert identity.semantic_head_commit_id == str(profile_head_commit_id)


@pytest.mark.asyncio
async def test_experience_workspace_provider_emits_declared_python_runtime_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = tmp_path / "languages" / "python" / "aware_code_experience"
    source_root = package_root / "aware_code_experience"
    source_root.mkdir(parents=True)
    (package_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "aware-code-experience"',
                'version = "0.1.0"',
                "",
                "[build-system]",
                'requires = ["hatchling>=1.27.0"]',
                'build-backend = "hatchling.build"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (source_root / "__init__.py").write_text(
        "from .view_model_registry import VIEW_MODEL_CONTRACTS\n",
        encoding="utf-8",
    )
    (source_root / "view_model_registry.py").write_text(
        "VIEW_MODEL_CONTRACTS = ()\n",
        encoding="utf-8",
    )
    (source_root / "py.typed").write_text("", encoding="utf-8")
    (source_root / "__pycache__").mkdir()
    (source_root / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
    source_code_package_id = uuid4()
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    package_oig_commit_id = uuid4()

    async def _fake_materialize_experience_package_from_manifest(**_: object):
        return SimpleNamespace(
            experience_toml_path=tmp_path / "aware.experience.toml",
            workspace_root=tmp_path,
            manifest_spec=SimpleNamespace(
                experience=SimpleNamespace(
                    package_name="aware-code-experience",
                    description="Code-owned view contracts.",
                ),
                targets={
                    "python": SimpleNamespace(
                        language="python",
                        root_dir="languages/python",
                        package_dir="aware_code_experience",
                    ),
                },
            ),
            experience_name="aware_code_package",
            experience_names=("aware_code_package",),
            environment_experience=SimpleNamespace(id=uuid4()),
            experience_package=SimpleNamespace(
                name="aware-code-experience",
                id=uuid4(),
            ),
            language_contract_packages=(),
            source_code_package_id=source_code_package_id,
            experience_source_path="experiences.aware",
            source_files=("experiences.aware",),
            phase_timings_s={},
            environment_experience_commit_id=uuid4(),
            projection_experience_commit_id=uuid4(),
            projection_experience_head_commit_id=uuid4(),
            projection_experience_graph_commit_id=uuid4(),
            projection_experience_graph_head_commit_id=uuid4(),
            projection_experience_section_surface_commit_id=uuid4(),
            projection_experience_section_surface_head_commit_id=uuid4(),
            activation_profile_config_branch_id=None,
            activation_profile_config_projection_hash=None,
            activation_profile_config_domain_object_instance_graph_id=None,
            activation_profile_config_object_instance_graph_commit_id=None,
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
            package_projection_hash="experience-package-projection-hash",
            package_object_instance_graph_commit_id=package_oig_commit_id,
        )

    monkeypatch.setattr(
        experience_workspace_provider,
        "materialize_experience_package_from_manifest",
        _fake_materialize_experience_package_from_manifest,
    )
    monkeypatch.setattr(
        experience_workspace_provider,
        "resolve_experience_profile_publication_summary",
        lambda **_: SimpleNamespace(experience_handle="aware_code", profiles=()),
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.experience.toml",
    )

    result = await experience_workspace_provider.materialize(request)

    raw_deltas = result.details["generated_code_package_deltas"]
    assert len(raw_deltas) == 1
    delta = CodePackageDelta.model_validate(raw_deltas[0])
    assert delta.package_name == "aware-code-experience"
    assert delta.package_root == "languages/python/aware_code_experience"
    assert delta.sources_root == (
        "languages/python/aware_code_experience/aware_code_experience"
    )
    assert delta.manifest_relative_path == (
        "languages/python/aware_code_experience/pyproject.toml"
    )
    assert {path.relative_path for path in delta.paths} == {
        "pyproject.toml",
        "aware_code_experience/__init__.py",
        "aware_code_experience/py.typed",
        "aware_code_experience/view_model_registry.py",
    }
    paths_by_relpath = {path.relative_path: path for path in delta.paths}
    assert paths_by_relpath["pyproject.toml"].path_role == (
        CodePackagePathRole.generated_manifest
    )
    assert paths_by_relpath["pyproject.toml"].content_text is not None
    assert 'name = "aware-code-experience"' in (
        paths_by_relpath["pyproject.toml"].content_text or ""
    )
    assert delta.production is not None
    provider_payload = delta.production.producer.provider_payload
    assert delta.production.producer.provider_key == "aware_experience"
    assert provider_payload["package_name"] == "aware-code-experience"
    assert provider_payload["manifest_kind"] == "pyproject_toml"
    assert provider_payload["manifest_relative_path"] == (
        "languages/python/aware_code_experience/pyproject.toml"
    )

    bundle = result.bundle_packages[0]
    assert bundle.semantic_object_instance_graph_commit_id == package_oig_commit_id
    assert len(bundle.runtime_code_package_refs) == 1
    runtime_ref = bundle.runtime_code_package_refs[0]
    assert runtime_ref["role"] == "experience_language_package"
    assert runtime_ref["package_name"] == "aware-code-experience"
    assert runtime_ref["manifest_relative_path"] == (
        "languages/python/aware_code_experience/pyproject.toml"
    )
    assert runtime_ref["source_code_package_id"] == provider_payload["code_package_id"]


def test_experience_profile_semantic_ids_match_materialized_stable_ids() -> None:
    result = SimpleNamespace(
        manifest_spec=SimpleNamespace(
            build=SimpleNamespace(environment_handle="home-story")
        )
    )
    publication = SimpleNamespace(
        experience_handle="home_story",
        profiles=(SimpleNamespace(experience_name="home_story", key="os.default"),),
    )

    assert experience_workspace_provider._profile_semantic_object_ids(
        result=result,
        profile_publication=publication,
    ) == {
        "experience.profile:home_story:os.default": (
            "4c64b46a-2099-5205-88b6-27bafd5970bc"
        )
    }


def _index_stub() -> MetaGraphRuntimeIndex:
    return cast(MetaGraphRuntimeIndex, object())


def _lane() -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="Environment",
    )


def test_load_experience_compile_plan_payloads_reads_runtime_artifacts(
    tmp_path: Path,
) -> None:
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "experience"
        / "runtime"
        / "home_story_workspace"
        / "experience.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    _ = compile_plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "action_ownership": [],
                "environment_ownership": [],
            }
        ),
        encoding="utf-8",
    )

    payloads = load_experience_compile_plan_payloads(repo_root=tmp_path)

    assert len(payloads) == 1
    assert payloads[0]["schema_version"] == 1


def test_resolve_actor_materialization_specs_derives_role_bindings() -> None:
    payloads: list[dict[str, object]] = [
        {
            "role_ownership": [
                {"name": "requester", "source_path": "roles.aware", "capabilities": []},
                {"name": "assistant", "source_path": "roles.aware", "capabilities": []},
            ],
            "actor_ownership": [
                {
                    "name": "human_requester",
                    "kind": "Human",
                    "roles": [],
                    "source_path": "actors.aware",
                },
                {
                    "name": "home_assistant",
                    "kind": "Agent",
                    "roles": [],
                    "source_path": "actors.aware",
                },
            ],
            "environment_actor_bindings": [
                {
                    "environment": "assistance",
                    "actor": "human_requester",
                    "roles": ["requester"],
                    "source_path": "environments.aware",
                },
                {
                    "environment": "assistance",
                    "actor": "home_assistant",
                    "roles": ["assistant"],
                    "source_path": "environments.aware",
                },
            ],
        }
    ]

    specs = resolve_actor_materialization_specs(compile_plan_payloads=payloads)

    assert specs == (
        ActorMaterializationSpec(
            actor_name="home_assistant",
            actor_kind="Agent",
            role_keys=("assistant",),
        ),
        ActorMaterializationSpec(
            actor_name="human_requester",
            actor_kind="Human",
            role_keys=("requester",),
        ),
    )


def test_build_actor_materialization_plan_emits_deterministic_steps() -> None:
    specs = (
        ActorMaterializationSpec(
            actor_name="home_assistant",
            actor_kind="Agent",
            role_keys=("assistant",),
        ),
        ActorMaterializationSpec(
            actor_name="human_requester",
            actor_kind="Human",
            role_keys=("requester",),
        ),
    )

    plan = build_actor_materialization_plan(lane=_lane(), specs=specs)

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.actor"
    assert [step.step_id for step in plan.steps] == [
        "actor:home_assistant",
        "actor:human_requester",
    ]
    assert plan.steps[0].payload["actor_name"] == "home_assistant"


def test_actor_materialization_step_payload_roundtrip_is_typed() -> None:
    spec = ActorMaterializationSpec(
        actor_name="human_requester",
        actor_kind="Human",
        role_keys=("requester", "assistant"),
    )

    payload = encode_actor_materialization_step_payload(spec=spec)
    decoded = decode_actor_materialization_step_payload(payload)

    assert decoded == ActorMaterializationSpec(
        actor_name="human_requester",
        actor_kind="Human",
        role_keys=("requester", "assistant"),
    )


def test_resolve_actor_materialization_specs_rejects_unknown_roles() -> None:
    payloads: list[dict[str, object]] = [
        {
            "role_ownership": [
                {"name": "requester", "source_path": "roles.aware", "capabilities": []},
            ],
            "actor_ownership": [
                {
                    "name": "human_requester",
                    "kind": "Human",
                    "roles": [],
                    "source_path": "actors.aware",
                },
            ],
            "environment_actor_bindings": [
                {
                    "environment": "assistance",
                    "actor": "human_requester",
                    "roles": ["ghost"],
                    "source_path": "environments.aware",
                }
            ],
        }
    ]

    with pytest.raises(RuntimeError, match="unknown role declarations"):
        _ = resolve_actor_materialization_specs(compile_plan_payloads=payloads)


@pytest.mark.asyncio
async def test_materialize_experience_compile_plan_actors_skips_when_no_threads() -> (
    None
):
    receipt = await materialize_experience_compile_plan_actors(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
        environment_experience_profile_config_id=uuid4(),
        planned_processes=(
            {
                "process_key": "boot",
                "threads": [],
            },
        ),
    )

    assert receipt is None


def test_resolve_action_materialization_specs_derives_program_bindings() -> None:
    payloads = [
        {
            "action_ownership": [
                {
                    "symbol": "home_story.open_door",
                    "action_name": "open_door",
                    "program_bindings": [
                        {"program": "door_program"},
                        {"program": "door_program"},
                    ],
                },
                {
                    "symbol": "home_story.watch_tv",
                    "action_name": "watch_tv",
                    "program_bindings": [{"program": "tv_program"}],
                },
            ],
            "environment_ownership": [
                {
                    "name": "home",
                    "programs": [
                        {
                            "program_config": "door_program",
                            "program_impl": "door_program_impl",
                        },
                        {
                            "program_config": "tv_program",
                            "program_impl": "tv_program_impl",
                        },
                    ],
                    "events": [
                        {
                            "event": "doorbell",
                            "actions": [{"action": "open_door"}],
                        },
                        {
                            "event": "remote",
                            "actions": [{"action": "watch_tv"}],
                        },
                    ],
                }
            ],
        }
    ]

    specs = resolve_action_materialization_specs(compile_plan_payloads=payloads)

    assert specs == (
        ActionMaterializationSpec(
            action_name="open_door", program_keys=("door_program",)
        ),
        ActionMaterializationSpec(action_name="watch_tv", program_keys=("tv_program",)),
    )


def test_resolve_action_materialization_specs_derives_dependency_action_ref() -> None:
    payloads = [
        {
            "action_ownership": [
                {
                    "symbol": "MemoryRememberEvent",
                    "action_name": "memory.remember_event",
                    "package_name": "aware-memory",
                    "fqn_prefix": "aware_memory",
                    "is_dependency": True,
                    "program_bindings": [],
                }
            ],
            "environment_ownership": [
                {
                    "name": "conversation",
                    "programs": [],
                    "events": [
                        {
                            "event": "ConversationMessageCreated",
                            "actions": [
                                {"action": "aware_memory.memory.remember_event"}
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    specs = resolve_action_materialization_specs(compile_plan_payloads=payloads)

    assert specs == (
        ActionMaterializationSpec(
            action_name="memory.remember_event",
            program_keys=(),
            is_dependency=True,
        ),
    )


def test_resolve_action_materialization_specs_rejects_unqualified_dependency_ref() -> (
    None
):
    payloads = [
        {
            "action_ownership": [
                {
                    "symbol": "MemoryRememberEvent",
                    "action_name": "memory.remember_event",
                    "package_name": "aware-memory",
                    "fqn_prefix": "aware_memory",
                    "is_dependency": True,
                    "program_bindings": [],
                }
            ],
            "environment_ownership": [
                {
                    "name": "conversation",
                    "programs": [],
                    "events": [
                        {
                            "event": "ConversationMessageCreated",
                            "actions": [{"action": "memory.remember_event"}],
                        }
                    ],
                }
            ],
        }
    ]

    with pytest.raises(RuntimeError, match="no matching action ownership"):
        resolve_action_materialization_specs(compile_plan_payloads=payloads)


def test_build_action_materialization_plan_emits_deterministic_steps() -> None:
    specs = (
        ActionMaterializationSpec(
            action_name="open_door", program_keys=("door_program",)
        ),
        ActionMaterializationSpec(action_name="watch_tv", program_keys=("tv_program",)),
    )

    plan = build_action_materialization_plan(
        lane=_lane(),
        specs=specs,
    )

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.action"
    assert [step.step_id for step in plan.steps] == [
        "action:open_door",
        "action:watch_tv",
    ]
    assert plan.steps[0].payload["action_name"] == "open_door"


def test_home_source_compile_payload_carries_activation_topology_inputs() -> None:
    repo_root = Path(__file__).resolve().parents[8]
    experience_toml = (
        repo_root
        / "workspaces"
        / "aware_home"
        / "modules"
        / "home"
        / "experiences"
        / "home_story"
        / "aware.experience.toml"
    )
    if not experience_toml.exists():
        pytest.skip("aware_home workspace is not available in this checkout")

    snapshot = materialization_service.compile_experience_workspace(
        toml_path=experience_toml,
        repo_root=repo_root / "workspaces" / "aware_home",
    ).snapshot
    payload = materialization_service._build_source_experience_compile_plan_payload(
        snapshot=snapshot,
    )

    assert payload["environment_handle"] == "home-story"
    actions = {
        item["action_name"]: item
        for item in cast(list[dict[str, object]], payload["action_ownership"])
    }
    assert actions["assist_home"]["program_bindings"] == [
        {"program": "home_story_scene", "args": []}
    ]

    environments = cast(list[dict[str, object]], payload["environment_ownership"])
    home_environment = next(
        item for item in environments if item["name"] == "home_story"
    )
    home_event = cast(list[dict[str, object]], home_environment["events"])[0]
    assert home_event["event"] == "home_door_state_changed"
    assert home_event["node_scopes"] == [{"node_ref": "front_door"}]
    assert home_event["actions"] == [{"action": "assist_home"}]

    connectors = cast(list[dict[str, object]], payload["connector_ownership"])
    home_devices = next(
        item for item in connectors if item["connector_key"] == "home_devices"
    )
    open_door = next(
        item
        for item in cast(list[dict[str, object]], home_devices["actuator_configs"])
        if item["actuator_key"] == "open_door"
    )
    dispatch = next(
        item
        for item in cast(
            list[dict[str, object]], open_door["invocation_action_configs"]
        )
        if item["action_key"] == "dispatch"
    )
    assert dispatch["target_ref"] == "home_devices.open_door.dispatch_open_door_action"
    request_fields = cast(list[dict[str, object]], dispatch["request_fields"])
    assert request_fields[-2:] == [
        {
            "attribute": "door_class_instance_identity_id",
            "source_ref": "binding.node.front_door.class_instance_identity_id",
            "required": True,
        },
        {
            "attribute": "door_class_config_id",
            "source_ref": "binding.node.front_door.class_config_id",
            "required": True,
        },
    ]


def test_source_compile_payload_carries_dependency_action_targets(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    memory_root = root / "experiences" / "aware-memory"
    _write_test_experience_toml(
        package_root=memory_root,
        package_name="aware-memory",
        fqn_prefix="aware_memory",
    )
    (memory_root / "actions").mkdir(parents=True, exist_ok=True)
    (memory_root / "actions" / "memory_actions.aware").write_text(
        "\n".join(
            [
                "action MemoryRememberEvent {",
                '  name "memory.remember_event";',
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (memory_root / "connectors").mkdir(parents=True, exist_ok=True)
    (memory_root / "connectors" / "memory.aware").write_text(
        "\n".join(
            [
                "connector memory {",
                "  kind memory_service_provider",
                "  actuator remember_event {",
                "    kind memory_remember_event",
                "    invocation remember_event api memory.remember_event.remember_event {",
                "      request_field event_id from event.id;",
                "      request_field actor_id from actor.id;",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    conversation_root = root / "experiences" / "aware-conversations"
    _write_test_experience_toml(
        package_root=conversation_root,
        package_name="aware-conversations",
        fqn_prefix="aware_conversations",
        dependencies=("aware-memory",),
    )
    (conversation_root / "events").mkdir(parents=True, exist_ok=True)
    (conversation_root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                'event ConversationMessageCreated name "conversation.message.created" renderer "conversation.message.created" {',
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (conversation_root / "environments").mkdir(parents=True, exist_ok=True)
    (conversation_root / "environments" / "conversation_environment.aware").write_text(
        "\n".join(
            [
                "environment aware_conversations {",
                "  event ConversationMessageCreated {",
                "    action aware_memory.memory.remember_event",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = materialization_service.compile_experience_workspace(
        toml_path=conversation_root / "aware.experience.toml",
        repo_root=root,
    ).snapshot
    payload = materialization_service._build_source_experience_compile_plan_payload(
        snapshot=snapshot,
    )

    action_specs = resolve_action_materialization_specs(
        compile_plan_payloads=(payload,)
    )
    target_specs = resolve_activation_target_materialization_specs(
        compile_plan_payloads=(payload,)
    )

    assert action_specs == (
        ActionMaterializationSpec(
            action_name="memory.remember_event",
            program_keys=(),
            is_dependency=True,
        ),
    )
    assert len(target_specs) == 1
    assert target_specs[0].connector_key == "aware_memory.memory"
    invocation = target_specs[0].actuator_configs[0].invocation_action_configs[0]
    assert invocation.target_ref == "memory.remember_event.remember_event"
    assert invocation.materialized_action_key == (
        "aware_memory.memory.actuator.remember_event.remember_event"
    )
    assert [field.attribute for field in invocation.request_fields] == [
        "event_id",
        "actor_id",
    ]


def test_activation_action_request_binding_selects_single_request_target() -> None:
    projection_experience_id = uuid4()
    dispatch = materialization_service._ActivationInvocationTargetSpec(
        materialized_action_key="home_devices.actuator.open_door.dispatch",
        target_ref="home_devices.open_door.dispatch_open_door_action",
        target_kind=ExperienceInvocationActionTargetKind.api,
        api_capability_endpoint_id=uuid4(),
        sdk_operation_id=None,
        experience_invocation_action_config_id=uuid4(),
        request_fields=(
            materialization_service.ConnectorInvocationRequestFieldMaterializationSpec(
                attribute="event_id",
                source_ref="event.id",
            ),
        ),
    )
    direct = materialization_service._ActivationInvocationTargetSpec(
        materialized_action_key="home_devices.actuator.open_door.open",
        target_ref="home_devices.open_door.open_door",
        target_kind=ExperienceInvocationActionTargetKind.api,
        api_capability_endpoint_id=uuid4(),
        sdk_operation_id=None,
        experience_invocation_action_config_id=projection_experience_id,
        request_fields=(),
    )

    bindings = materialization_service._activation_action_request_bindings(
        action_specs=(
            ActionMaterializationSpec(
                action_name="assist_home",
                program_keys=("home_story_scene",),
            ),
        ),
        targets=(direct, dispatch),
    )

    assert bindings == (
        (
            ActionMaterializationSpec(
                action_name="assist_home",
                program_keys=("home_story_scene",),
            ),
            (dispatch,),
        ),
    )


def test_activation_action_request_binding_requires_dependency_target() -> None:
    with pytest.raises(RuntimeError, match="dependency actions require"):
        materialization_service._activation_action_request_bindings(
            action_specs=(
                ActionMaterializationSpec(
                    action_name="memory.remember_event",
                    program_keys=(),
                    is_dependency=True,
                ),
            ),
            targets=(),
        )


def test_endpoint_request_attribute_index_skips_incomplete_request_rows() -> None:
    class_config_id = uuid4()
    payload = {
        "api_ontology": [
            {
                "capability_endpoint_request_configs": [
                    {
                        "api_name": "home_story_views",
                        "capability_name": "home_story_security_door",
                        "endpoint_name": "resolve",
                        "class_config_id": None,
                        "class_ref": (
                            "home_story_view_api.view_resolution."
                            "HomeStorySecurityDoorViewResolveRequest"
                        ),
                    },
                    {
                        "api_name": "home_devices",
                        "capability_name": "open_door",
                        "endpoint_name": "dispatch_open_door_action",
                        "class_config_id": str(class_config_id),
                        "class_ref": (
                            "aware_home_devices_dto.home."
                            "OpenDoorActionDispatchRequestV1"
                        ),
                    },
                ]
            }
        ]
    }

    refs = materialization_service._endpoint_request_attributes_by_endpoint_ref(
        index=SimpleNamespace(class_configs_by_id={}),
        api_compile_plan_payloads=(payload,),
    )

    assert tuple(refs) == ("home_devices.open_door.dispatch_open_door_action",)
    ref = refs["home_devices.open_door.dispatch_open_door_action"]
    assert ref.class_config_id == class_config_id
    assert (
        ref.class_ref == "aware_home_devices_dto.home.OpenDoorActionDispatchRequestV1"
    )


def test_resolve_connector_config_materialization_specs_derives_scoped_invocations() -> (
    None
):
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "futurehill_clinic",
                    "projection": "ClinicAmbient",
                }
            ],
            "connector_ownership": [
                {
                    "connector_key": "music",
                    "connector_kind": "media",
                    "source_path": "connectors/music.aware",
                    "label": "Music",
                    "description": None,
                    "providers": [
                        {
                            "provider_key": "youtube_music",
                            "provider_kind": "music_streaming",
                            "source_path": "connectors/music.aware",
                            "provider_ref": "youtube.music",
                            "label": "YouTube Music",
                            "description": None,
                        }
                    ],
                    "sensor_configs": [
                        {
                            "sensor_key": "now_playing",
                            "sensor_kind": "media_state",
                            "source_path": "connectors/music.aware",
                            "source_ref": "youtube.now_playing",
                            "observed_state_node_refs": [
                                "clinic.Room::devices",
                                "clinic.Room::current_track",
                            ],
                            "label": None,
                            "description": None,
                            "invocation_action_configs": [
                                {
                                    "action_key": "poll",
                                    "action_kind": "api",
                                    "target_ref": "MusicApi.Playback.now_playing",
                                    "source_path": "connectors/music.aware",
                                    "label": "Poll",
                                    "receipt_policy": "event",
                                    "confirmation_policy": None,
                                    "optimistic_policy": None,
                                },
                                {
                                    "action_key": "subscribe",
                                    "action_kind": "sdk",
                                    "target_ref": (
                                        "MusicSdk.Player.subscribe_now_playing"
                                    ),
                                    "source_path": "connectors/music.aware",
                                    "label": None,
                                    "receipt_policy": None,
                                    "confirmation_policy": "none",
                                    "optimistic_policy": None,
                                },
                            ],
                        },
                        {
                            "sensor_key": "queue",
                            "sensor_kind": "media_queue",
                            "source_path": "connectors/music.aware",
                            "source_ref": "youtube.queue",
                            "observed_state_node_refs": [],
                            "label": None,
                            "description": None,
                            "invocation_action_configs": [
                                {
                                    "action_key": "poll",
                                    "action_kind": "api",
                                    "target_ref": "MusicApi.Queue.current",
                                    "source_path": "connectors/music.aware",
                                    "label": None,
                                    "receipt_policy": None,
                                    "confirmation_policy": None,
                                    "optimistic_policy": None,
                                }
                            ],
                        },
                    ],
                    "actuator_configs": [
                        {
                            "actuator_key": "play_track",
                            "actuator_kind": "media_control",
                            "source_path": "connectors/music.aware",
                            "target_ref": "youtube.play",
                            "affected_state_node_refs": ["clinic.Room::devices"],
                            "label": None,
                            "description": None,
                            "invocation_action_configs": [
                                {
                                    "action_key": "activate",
                                    "action_kind": "sdk",
                                    "target_ref": "MusicSdk.Player.play",
                                    "source_path": "connectors/music.aware",
                                    "label": None,
                                    "receipt_policy": None,
                                    "confirmation_policy": None,
                                    "optimistic_policy": "immediate",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    specs = resolve_connector_config_materialization_specs(
        compile_plan_payloads=payloads
    )

    assert specs == (
        ConnectorConfigMaterializationSpec(
            connector_key="music",
            connector_kind="media",
            source_path="connectors/music.aware",
            projection_experience_name="futurehill_clinic",
            projection_key="ClinicAmbient",
            label="Music",
            providers=(
                ConnectorProviderMaterializationSpec(
                    provider_key="youtube_music",
                    provider_kind="music_streaming",
                    source_path="connectors/music.aware",
                    provider_ref="youtube.music",
                    label="YouTube Music",
                ),
            ),
            sensor_configs=(
                SensorConfigMaterializationSpec(
                    sensor_key="now_playing",
                    sensor_kind="media_state",
                    source_path="connectors/music.aware",
                    source_ref="youtube.now_playing",
                    observed_state_node_refs=(
                        "clinic.Room::devices",
                        "clinic.Room::current_track",
                    ),
                    invocation_action_configs=(
                        ConnectorInvocationActionConfigMaterializationSpec(
                            action_key="poll",
                            action_kind="api",
                            target_ref="MusicApi.Playback.now_playing",
                            materialized_action_key=("music.sensor.now_playing.poll"),
                            source_path="connectors/music.aware",
                            label="Poll",
                            receipt_policy="event",
                        ),
                        ConnectorInvocationActionConfigMaterializationSpec(
                            action_key="subscribe",
                            action_kind="sdk",
                            target_ref=("MusicSdk.Player.subscribe_now_playing"),
                            materialized_action_key=(
                                "music.sensor.now_playing.subscribe"
                            ),
                            source_path="connectors/music.aware",
                            confirmation_policy="none",
                        ),
                    ),
                ),
                SensorConfigMaterializationSpec(
                    sensor_key="queue",
                    sensor_kind="media_queue",
                    source_path="connectors/music.aware",
                    source_ref="youtube.queue",
                    invocation_action_configs=(
                        ConnectorInvocationActionConfigMaterializationSpec(
                            action_key="poll",
                            action_kind="api",
                            target_ref="MusicApi.Queue.current",
                            materialized_action_key="music.sensor.queue.poll",
                            source_path="connectors/music.aware",
                        ),
                    ),
                ),
            ),
            actuator_configs=(
                ActuatorConfigMaterializationSpec(
                    actuator_key="play_track",
                    actuator_kind="media_control",
                    source_path="connectors/music.aware",
                    target_ref="youtube.play",
                    affected_state_node_refs=("clinic.Room::devices",),
                    invocation_action_configs=(
                        ConnectorInvocationActionConfigMaterializationSpec(
                            action_key="activate",
                            action_kind="sdk",
                            target_ref="MusicSdk.Player.play",
                            materialized_action_key=(
                                "music.actuator.play_track.activate"
                            ),
                            source_path="connectors/music.aware",
                            optimistic_policy="immediate",
                        ),
                    ),
                ),
            ),
        ),
    )


def test_resolve_activation_target_materialization_specs_derives_imported_targets() -> (
    None
):
    payloads = [
        {
            "action_target_ownership": [
                {
                    "connector_key": "memory",
                    "connector_kind": "memory_service_consumer",
                    "source_path": "connectors/memory.aware",
                    "package_name": "aware-memory",
                    "fqn_prefix": "aware_memory",
                    "is_dependency": True,
                    "providers": [],
                    "sensor_configs": [],
                    "actuator_configs": [
                        {
                            "actuator_key": "remember_event",
                            "actuator_kind": "memory_remember_event",
                            "source_path": "connectors/memory.aware",
                            "target_ref": "aware_memory.service",
                            "affected_state_node_refs": [],
                            "label": "Remember event",
                            "description": None,
                            "invocation_action_configs": [
                                {
                                    "action_key": "remember_event",
                                    "action_kind": "api",
                                    "target_ref": "memory.remember_event.remember_event",
                                    "source_path": "connectors/memory.aware",
                                    "label": "Remember event",
                                    "receipt_policy": "show_receipt",
                                    "confirmation_policy": None,
                                    "optimistic_policy": None,
                                    "request_fields": [
                                        {
                                            "attribute": "event_id",
                                            "source_ref": "event.id",
                                            "required": True,
                                        },
                                        {
                                            "attribute": "actor_id",
                                            "source_ref": "actor.id",
                                            "required": True,
                                        },
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    specs = resolve_activation_target_materialization_specs(
        compile_plan_payloads=payloads
    )

    assert specs == (
        ConnectorConfigMaterializationSpec(
            connector_key="aware_memory.memory",
            connector_kind="memory_service_consumer",
            source_path="connectors/memory.aware",
            projection_experience_name="",
            projection_key="",
            label=None,
            providers=(),
            sensor_configs=(),
            actuator_configs=(
                ActuatorConfigMaterializationSpec(
                    actuator_key="remember_event",
                    actuator_kind="memory_remember_event",
                    source_path="connectors/memory.aware",
                    target_ref="aware_memory.service",
                    label="Remember event",
                    invocation_action_configs=(
                        ConnectorInvocationActionConfigMaterializationSpec(
                            action_key="remember_event",
                            action_kind="api",
                            target_ref="memory.remember_event.remember_event",
                            materialized_action_key=(
                                "aware_memory.memory.actuator."
                                "remember_event.remember_event"
                            ),
                            source_path="connectors/memory.aware",
                            label="Remember event",
                            receipt_policy="show_receipt",
                            request_fields=(
                                materialization_service.ConnectorInvocationRequestFieldMaterializationSpec(
                                    attribute="event_id",
                                    source_ref="event.id",
                                ),
                                materialization_service.ConnectorInvocationRequestFieldMaterializationSpec(
                                    attribute="actor_id",
                                    source_ref="actor.id",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def test_resolve_connector_config_materialization_specs_ignores_action_targets() -> (
    None
):
    payloads = [
        {
            "action_target_ownership": [
                {
                    "connector_key": "memory",
                    "connector_kind": "memory_service_consumer",
                    "source_path": "connectors/memory.aware",
                }
            ]
        }
    ]

    assert (
        resolve_connector_config_materialization_specs(compile_plan_payloads=payloads)
        == ()
    )


def test_resolve_connector_config_materialization_specs_rejects_payload_schema_ref() -> (
    None
):
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "futurehill_clinic",
                    "projection": "ClinicAmbient",
                }
            ],
            "connector_ownership": [
                {
                    "connector_key": "music",
                    "connector_kind": "media",
                    "source_path": "connectors/music.aware",
                    "sensor_configs": [
                        {
                            "sensor_key": "now_playing",
                            "sensor_kind": "media_state",
                            "source_path": "connectors/music.aware",
                            "payload_schema_ref": "clinic.Room",
                        }
                    ],
                    "actuator_configs": [
                        {
                            "actuator_key": "play_track",
                            "actuator_kind": "media_control",
                            "source_path": "connectors/music.aware",
                        }
                    ],
                }
            ],
        }
    ]

    with pytest.raises(RuntimeError, match="payload_schema_ref is retired"):
        resolve_connector_config_materialization_specs(compile_plan_payloads=payloads)

    payloads[0]["connector_ownership"][0]["sensor_configs"][0].pop("payload_schema_ref")
    payloads[0]["connector_ownership"][0]["actuator_configs"][0][
        "payload_schema_ref"
    ] = "clinic.Room"

    with pytest.raises(RuntimeError, match="payload_schema_ref is retired"):
        resolve_connector_config_materialization_specs(compile_plan_payloads=payloads)


def test_build_connector_config_materialization_plan_emits_deterministic_steps() -> (
    None
):
    spec = ConnectorConfigMaterializationSpec(
        connector_key="music",
        connector_kind="media",
        source_path="connectors/music.aware",
        projection_experience_name="futurehill_clinic",
        projection_key="ClinicAmbient",
        sensor_configs=(
            SensorConfigMaterializationSpec(
                sensor_key="now_playing",
                sensor_kind="media_state",
                source_path="connectors/music.aware",
                invocation_action_configs=(
                    ConnectorInvocationActionConfigMaterializationSpec(
                        action_key="poll",
                        action_kind="api",
                        target_ref="MusicApi.Playback.now_playing",
                        materialized_action_key="music.sensor.now_playing.poll",
                        source_path="connectors/music.aware",
                    ),
                ),
            ),
        ),
    )

    plan = build_connector_config_materialization_plan(lane=_lane(), specs=(spec,))

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.connector_config"
    assert [step.step_id for step in plan.steps] == ["connector_config:music"]
    assert plan.steps[0].payload["connector_key"] == "music"
    assert (
        plan.steps[0].payload["sensor_configs"][0]["invocation_action_configs"][0][
            "materialized_action_key"
        ]
        == "music.sensor.now_playing.poll"
    )

    payload = encode_connector_config_materialization_step_payload(spec=spec)
    assert decode_connector_config_materialization_step_payload(payload) == spec


@pytest.mark.asyncio
async def test_materialize_connector_config_ontology_executes_config_and_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opgi_id = uuid4()
    calls: list[tuple[str, object]] = []

    class _FakeLane:
        def __init__(self, *, projection: str) -> None:
            self.projection = projection
            self.last_commit_id: UUID | None = None
            self.last_head_commit_id: UUID | None = None

        @contextmanager
        def activate(self, **kwargs: object):
            calls.append(("activate", self.projection))
            self.last_commit_id = uuid4()
            self.last_head_commit_id = uuid4()
            yield

    class _FakeConnectorConfig:
        def __init__(self, *, object_id: UUID) -> None:
            self.id = object_id

        async def add_provider(self, **kwargs: object) -> object:
            calls.append(("connector.add_provider", dict(kwargs)))
            return SimpleNamespace(id=uuid4())

        async def add_sensor_config(self, **kwargs: object) -> object:
            calls.append(("connector.add_sensor_config", dict(kwargs)))
            return SimpleNamespace(id=uuid4())

        async def add_actuator_config(self, **kwargs: object) -> object:
            calls.append(("connector.add_actuator_config", dict(kwargs)))
            return SimpleNamespace(id=uuid4())

    class _FakeProjectionExperience:
        def __init__(self, *, object_id: UUID) -> None:
            self.id = object_id

        async def create_invocation_action_config(self, **kwargs: object) -> object:
            calls.append(("projection.create_invocation_action_config", dict(kwargs)))
            return SimpleNamespace(id=uuid4())

    async def _connector_create(**kwargs: object) -> object:
        calls.append(("connector.create", dict(kwargs)))
        return _FakeConnectorConfig(object_id=uuid4())

    async def _sensor_binding(**kwargs: object) -> object:
        calls.append(("sensor.binding", dict(kwargs)))
        return SimpleNamespace(id=uuid4())

    async def _actuator_binding(**kwargs: object) -> object:
        calls.append(("actuator.binding", dict(kwargs)))
        return SimpleNamespace(id=uuid4())

    def _fake_bind_meta_graph_runtime_lane(**kwargs: object) -> _FakeLane:
        return _FakeLane(projection=str(kwargs["projection"]))

    monkeypatch.setattr(
        materialization_service.ocg_support,
        "find_projection_hash_by_name",
        lambda *, index, projection_name: f"hash:{projection_name}",
    )
    monkeypatch.setattr(
        materialization_service.ocg_support,
        "build_opgi_index",
        lambda *, index: {"ClinicAmbient": (opgi_id, set())},
    )
    monkeypatch.setattr(
        materialization_service,
        "_bind_meta_graph_runtime_lane",
        _fake_bind_meta_graph_runtime_lane,
    )
    monkeypatch.setattr(
        materialization_service.ConnectorConfig,
        "create",
        _connector_create,
    )
    monkeypatch.setattr(
        materialization_service.ProjectionExperience,
        "model_construct",
        lambda **kwargs: _FakeProjectionExperience(object_id=kwargs["id"]),
    )
    monkeypatch.setattr(
        materialization_service.SensorInvocationActionConfig,
        "build_via_sensor_config",
        _sensor_binding,
    )
    monkeypatch.setattr(
        materialization_service.ActuatorInvocationActionConfig,
        "build_via_actuator_config",
        _actuator_binding,
    )

    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "futurehill_clinic",
                    "projection": "ClinicAmbient",
                }
            ],
            "connector_ownership": [
                {
                    "connector_key": "music",
                    "connector_kind": "media",
                    "source_path": "connectors/music.aware",
                    "providers": [
                        {
                            "provider_key": "youtube_music",
                            "provider_kind": "music_streaming",
                            "source_path": "connectors/music.aware",
                        }
                    ],
                    "sensor_configs": [
                        {
                            "sensor_key": "now_playing",
                            "sensor_kind": "media_state",
                            "source_path": "connectors/music.aware",
                            "invocation_action_configs": [
                                {
                                    "action_key": "poll",
                                    "action_kind": "api",
                                    "target_ref": "MusicApi.Playback.now_playing",
                                    "source_path": "connectors/music.aware",
                                }
                            ],
                        }
                    ],
                    "actuator_configs": [
                        {
                            "actuator_key": "play_track",
                            "actuator_kind": "media_control",
                            "source_path": "connectors/music.aware",
                            "invocation_action_configs": [
                                {
                                    "action_key": "activate",
                                    "action_kind": "sdk",
                                    "target_ref": "MusicSdk.Player.play",
                                    "source_path": "connectors/music.aware",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    receipt = await materialize_experience_connector_config_ontology(
        runtime=_NoOpRuntime(),
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=None,
        lane=_lane(),
        compile_plan_payloads=payloads,
    )

    assert receipt is not None
    assert receipt.status == "succeeded"
    assert receipt.steps[0].details["provider_count"] == 1
    assert receipt.steps[0].details["sensor_invocation_action_config_count"] == 1
    assert receipt.steps[0].details["actuator_invocation_action_config_count"] == 1

    call_names = [name for name, _payload in calls]
    assert "connector.create" in call_names
    assert "connector.add_provider" in call_names
    assert "connector.add_sensor_config" in call_names
    assert "connector.add_actuator_config" in call_names
    assert call_names.count("projection.create_invocation_action_config") == 2
    assert "sensor.binding" in call_names
    assert "actuator.binding" in call_names

    action_payloads = [
        cast(dict[str, object], payload)
        for name, payload in calls
        if name == "projection.create_invocation_action_config"
        and "target_kind" in cast(dict[str, object], payload)
    ]
    api_action_payload = next(
        payload
        for payload in action_payloads
        if payload.get("api_capability_endpoint_id") is not None
    )
    sdk_action_payload = next(
        payload
        for payload in action_payloads
        if payload.get("sdk_operation_id") is not None
    )
    assert api_action_payload["api_capability_endpoint_id"] is not None
    assert api_action_payload["sdk_operation_id"] is None
    assert sdk_action_payload["sdk_operation_id"] is not None
    assert sdk_action_payload["api_capability_endpoint_id"] is None


@pytest.mark.asyncio
async def test_materialize_experience_compile_plan_actions_skips_when_no_threads() -> (
    None
):
    receipt = await materialize_experience_compile_plan_actions(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
        planned_processes=(
            {
                "process_key": "boot",
                "threads": [],
            },
        ),
    )

    assert receipt is None


def test_resolve_environment_profile_materialization_specs_derives_nested_specs() -> (
    None
):
    payloads = [
        {
            "fqn_prefix": "aware://experiences/home_story",
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                }
            ],
            "environment_profile_ownership": [
                {
                    "experience_name": "home_story",
                    "key": "os.default",
                    "source_path": "profiles.aware",
                    "title": "Default",
                    "description": "Default home story profile",
                    "narrative": "Story-first desktop",
                    "process_configs": [
                        {
                            "type": "continuous",
                            "key": "home",
                            "process_key": "home",
                            "source_path": "profiles.aware",
                            "title": "Home",
                            "is_bootstrap_default": True,
                            "thread_configs": [
                                {
                                    "key": "home.main",
                                    "thread_key": "home.main",
                                    "source_path": "profiles.aware",
                                    "title": "Main",
                                    "is_default": True,
                                    "projection_experiences": [
                                        {
                                            "experience_name": "home_story",
                                            "source_path": "profiles.aware",
                                            "view_key": "overview.home",
                                            "is_default": True,
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                    "view_event_transitions": [
                        {
                            "key": "home.open.main",
                            "source_projection_experience_name": "home_story",
                            "source_view_key": "overview.home",
                            "trigger_event_config_ref": "home.opened",
                            "target_projection_experience_name": "home_story",
                            "target_section_graph_binding_key": "home.main",
                            "source_path": "profiles.aware",
                            "name": "Open main home",
                            "rationale": "Home opened event focuses the main home surface.",
                            "idempotency_policy": "event_commit",
                        }
                    ],
                }
            ],
        }
    ]

    specs = resolve_environment_profile_materialization_specs(
        compile_plan_payloads=payloads
    )

    assert specs == (
        EnvironmentProfileMaterializationSpec(
            fqn_prefix="aware://experiences/home_story",
            experience_name="home_story",
            key="os.default",
            source_path="profiles.aware",
            title="Default",
            description="Default home story profile",
            narrative="Story-first desktop",
            process_configs=(
                EnvironmentProfileProcessMaterializationSpec(
                    type="continuous",
                    key="home",
                    process_key="home",
                    source_path="profiles.aware",
                    title="Home",
                    is_bootstrap_default=True,
                    thread_configs=(
                        EnvironmentProfileThreadMaterializationSpec(
                            key="home.main",
                            thread_key="home.main",
                            source_path="profiles.aware",
                            title="Main",
                            is_default=True,
                            projection_experiences=(
                                EnvironmentProfileThreadProjectionMaterializationSpec(
                                    projection_experience_name="home_story",
                                    projection_key="home",
                                    source_path="profiles.aware",
                                    view_key="overview.home",
                                    is_default=True,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            view_event_transitions=(
                EnvironmentProfileViewEventTransitionMaterializationSpec(
                    key="home.open.main",
                    source_projection_experience_name="home_story",
                    source_view_key="overview.home",
                    trigger_event_config_ref="home.opened",
                    target_projection_experience_name="home_story",
                    target_section_graph_binding_key="home.main",
                    source_path="profiles.aware",
                    name="Open main home",
                    rationale="Home opened event focuses the main home surface.",
                    idempotency_policy="event_commit",
                ),
            ),
        ),
    )


def test_build_environment_profile_materialization_plan_emits_deterministic_steps() -> (
    None
):
    specs = (
        EnvironmentProfileMaterializationSpec(
            fqn_prefix="aware://experiences/home_story",
            experience_name="home_story",
            key="os.default",
            source_path="profiles.aware",
            process_configs=(),
        ),
    )

    plan = build_environment_profile_materialization_plan(lane=_lane(), specs=specs)

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.environment_profile"
    assert [step.step_id for step in plan.steps] == [
        "environment_profile:home_story:os.default"
    ]
    assert plan.steps[0].payload["fqn_prefix"] == "aware://experiences/home_story"


def test_environment_profile_materialization_step_payload_roundtrip_is_typed() -> None:
    spec = EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware://experiences/home_story",
        experience_name="home_story",
        key="os.default",
        source_path="profiles.aware",
        title="Default",
        process_configs=(
            EnvironmentProfileProcessMaterializationSpec(
                type="continuous",
                key="home",
                process_key="home",
                source_path="profiles.aware",
                is_bootstrap_default=True,
                thread_configs=(
                    EnvironmentProfileThreadMaterializationSpec(
                        key="home.main",
                        thread_key="home.main",
                        source_path="profiles.aware",
                        is_default=True,
                        projection_experiences=(
                            EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name="home_story",
                                projection_key="home",
                                source_path="profiles.aware",
                                view_key="overview.home",
                                is_default=True,
                            ),
                        ),
                    ),
                ),
            ),
        ),
        view_event_transitions=(
            EnvironmentProfileViewEventTransitionMaterializationSpec(
                key="home.open.main",
                source_projection_experience_name="home_story",
                source_view_key="overview.home",
                trigger_event_config_ref="home.opened",
                target_projection_experience_name="home_story",
                target_section_graph_binding_key="home.main",
                source_path="profiles.aware",
                name="Open main home",
                rationale="Home opened event focuses the main home surface.",
                idempotency_policy="event_commit",
            ),
        ),
    )

    payload = encode_environment_profile_materialization_step_payload(spec=spec)
    decoded = decode_environment_profile_materialization_step_payload(payload)

    assert decoded == spec


def test_resolve_environment_profile_materialization_specs_rejects_unknown_projection_experience() -> (
    None
):
    payloads = [
        {
            "fqn_prefix": "aware://experiences/home_story",
            "projection_experience_ownership": [],
            "environment_profile_ownership": [
                {
                    "experience_name": "home_story",
                    "key": "os.default",
                    "source_path": "profiles.aware",
                    "process_configs": [
                        {
                            "type": "continuous",
                            "key": "home",
                            "process_key": "home",
                            "source_path": "profiles.aware",
                            "thread_configs": [
                                {
                                    "key": "home.main",
                                    "thread_key": "home.main",
                                    "source_path": "profiles.aware",
                                    "projection_experiences": [
                                        {
                                            "experience_name": "missing_projection",
                                            "source_path": "profiles.aware",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    with pytest.raises(RuntimeError, match="could not resolve projection ownership"):
        _ = resolve_environment_profile_materialization_specs(
            compile_plan_payloads=payloads
        )


def test_resolve_environment_profile_materialization_specs_accepts_committed_dependency_projection_ownership() -> (
    None
):
    payloads = [
        {
            "fqn_prefix": "aware_goals",
            "projection_experience_ownership": [
                {
                    "name": "aware_goals",
                    "projection": "goals",
                    "source_path": "experiences.aware",
                }
            ],
            "environment_profile_ownership": [
                {
                    "experience_name": "aware_goals",
                    "key": "goals.default",
                    "source_path": "profiles.aware",
                    "process_configs": [
                        {
                            "type": "continuous",
                            "key": "goals",
                            "process_key": "goals",
                            "source_path": "profiles.aware",
                            "thread_configs": [
                                {
                                    "key": "goals.main",
                                    "thread_key": "goals.main",
                                    "source_path": "profiles.aware",
                                    "projection_experiences": [
                                        {
                                            "experience_name": "aware_conversation_spaces",
                                            "source_path": "profiles.aware",
                                            "view_key": "selector",
                                        }
                                    ],
                                    "layout_configs": [
                                        {
                                            "layout_key": "coordination_center",
                                            "source_path": "profiles.aware",
                                            "sections": [
                                                {
                                                    "section_key": "orchestration",
                                                    "projection_experience_name": "aware_conversation_spaces",
                                                    "view_key": "selector",
                                                    "source_path": "profiles.aware",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    specs = resolve_environment_profile_materialization_specs(
        compile_plan_payloads=payloads,
        external_projection_keys_by_experience_name={
            "aware_conversation_spaces": "conversation_spaces"
        },
    )

    thread = specs[0].process_configs[0].thread_configs[0]
    assert thread.projection_experiences[0].projection_key == "conversation_spaces"
    assert thread.layout_configs[0].sections[0].projection_key == "conversation_spaces"


def test_resolve_environment_profile_materialization_specs_rejects_conflicting_dependency_projection_ownership() -> (
    None
):
    payloads = [
        {
            "fqn_prefix": "aware_goals",
            "projection_experience_ownership": [
                {
                    "name": "aware_conversation_spaces",
                    "projection": "local_conversation_spaces",
                    "source_path": "experiences.aware",
                }
            ],
            "environment_profile_ownership": [],
        }
    ]

    with pytest.raises(RuntimeError, match="conflicting projection keys"):
        _ = resolve_environment_profile_materialization_specs(
            compile_plan_payloads=payloads,
            external_projection_keys_by_experience_name={
                "aware_conversation_spaces": "conversation_spaces"
            },
        )


@pytest.mark.asyncio
async def test_materialize_experience_compile_plan_environment_profiles_skips_when_no_threads() -> (
    None
):
    receipt = await materialize_experience_compile_plan_environment_profiles(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
        planned_processes=(
            {
                "process_key": "boot",
                "threads": [],
            },
        ),
    )

    assert receipt is None


def test_resolve_projection_materialization_specs_derives_deterministic_specs() -> None:
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "branches": [
                        {
                            "name": "beta",
                            "is_default": False,
                            "source_path": "experiences.aware",
                        },
                        {
                            "name": "main",
                            "is_default": True,
                            "source_path": "experiences.aware",
                        },
                    ],
                    "observables": [
                        {
                            "key": "security",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "door",
                                    "is_default": True,
                                    "api_view_ref": "home_views.home_story_security_door",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                        {
                            "key": "entertainment",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "tv",
                                    "is_default": True,
                                    "api_view_ref": "home_views.home_story_entertainment_tv",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                    ],
                    "nodes": [],
                }
            ],
            "view_api_ownership": {
                "api_name": "home_views",
                "views": [
                    {
                        "api_name": "home_views",
                        "view_name": "home_story_entertainment_tv",
                        "experience_name": "home_story",
                        "observable_key": "entertainment",
                        "view_key": "tv",
                        "observable_ref": "home.entertainment",
                        "view_ref": "home_story.entertainment.tv",
                        "projection_view_key": "entertainment.tv",
                        "state_model_ref": "aware_home.home.Tv",
                        "is_default": True,
                        "source_path": "experiences.aware",
                    },
                    {
                        "api_name": "home_views",
                        "view_name": "home_story_security_door",
                        "experience_name": "home_story",
                        "observable_key": "security",
                        "view_key": "door",
                        "observable_ref": "home.security",
                        "view_ref": "home_story.security.door",
                        "projection_view_key": "security.door",
                        "state_model_ref": "aware_home.home.Door",
                        "is_default": True,
                        "source_path": "experiences.aware",
                    },
                ],
            },
        }
    ]

    specs = resolve_projection_materialization_specs(compile_plan_payloads=payloads)

    assert specs == (
        ProjectionExperienceMaterializationSpec(
            experience_name="home_story",
            projection_key="home",
            branches=("beta", "main"),
            views=(
                ProjectionExperienceViewMaterializationSpec(
                    observable_key="entertainment",
                    view_key="tv",
                    api_name="home_views",
                    api_view_name="home_story_entertainment_tv",
                    api_view_ref="home_views.home_story_entertainment_tv",
                ),
                ProjectionExperienceViewMaterializationSpec(
                    observable_key="security",
                    view_key="door",
                    api_name="home_views",
                    api_view_name="home_story_security_door",
                    api_view_ref="home_views.home_story_security_door",
                ),
            ),
        ),
    )


def test_resolve_projection_materialization_specs_keeps_source_projection_key_after_runtime_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_opgi_id = UUID("11111111-1111-4111-8111-111111111111")

    class _Resolver:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[str, ...]]] = []

        def resolve(
            self,
            *,
            projection_key: str,
            node_refs,
            experience_name: str,
            context: str,
        ) -> SimpleNamespace:
            _ = experience_name, context
            resolved_node_refs = tuple(node_refs)
            self.calls.append((projection_key, resolved_node_refs))
            return SimpleNamespace(projection_key="Home", opgi_id=runtime_opgi_id)

    resolver = _Resolver()
    monkeypatch.setattr(
        projection_contract_materialization,
        "build_projection_runtime_resolver",
        lambda *, index: resolver,
    )
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "branches": [],
                    "observables": [
                        {
                            "key": "overview",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "home",
                                    "is_default": True,
                                    "api_view_ref": "home_views.home_story_overview_home",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                    ],
                    "nodes": [
                        {
                            "name": "home",
                            "node_ref": "home.Home",
                            "source_path": "experiences.aware",
                            "identities": [
                                {"key": "home", "source_path": "experiences.aware"}
                            ],
                        }
                    ],
                }
            ],
            "view_api_ownership": {
                "api_name": "home_views",
                "views": [
                    {
                        "api_name": "home_views",
                        "view_name": "home_story_overview_home",
                        "experience_name": "home_story",
                        "observable_key": "overview",
                        "view_key": "home",
                        "observable_ref": "home.overview",
                        "view_ref": "home_story.overview.home",
                        "projection_view_key": "overview.home",
                        "state_model_ref": "aware_home.home.Home",
                        "is_default": True,
                        "source_path": "experiences.aware",
                    },
                ],
            },
        }
    ]

    specs = resolve_projection_materialization_specs(
        compile_plan_payloads=payloads,
        index=_index_stub(),
    )

    assert specs[0].projection_key == "home"
    assert specs[0].runtime_opgi_id == runtime_opgi_id
    assert resolver.calls == [("home", ("home.Home",))]


def test_runtime_opgi_id_resolves_projection_materialization_source_node_alias() -> (
    None
):
    runtime_opgi_id = UUID("22222222-2222-4222-8222-222222222222")

    resolved = materialization_service._resolve_projection_opgi_id_for_projection_key(
        opgi_by_key_casefolded={"layout": (runtime_opgi_id, frozenset())},
        projection_key="layoutsection",
        experience_name="layout_section",
        runtime_opgi_id=runtime_opgi_id,
    )

    assert resolved == runtime_opgi_id


def test_build_projection_materialization_plan_emits_deterministic_steps() -> None:
    specs = (
        ProjectionExperienceMaterializationSpec(
            experience_name="home_story",
            projection_key="home",
            branches=("main",),
            views=(
                ProjectionExperienceViewMaterializationSpec(
                    observable_key="security",
                    view_key="door",
                    api_name="home_views",
                    api_view_name="home_story_security_door",
                    api_view_ref="home_views.home_story_security_door",
                    state_model_ref="aware_home.home.Door",
                ),
            ),
        ),
        ProjectionExperienceMaterializationSpec(
            experience_name="home_story_secondary",
            projection_key="home",
            branches=(),
            views=(),
        ),
    )

    plan = build_projection_materialization_plan(lane=_lane(), specs=specs)

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.projection"
    assert [step.step_id for step in plan.steps] == [
        "projection:home_story",
        "projection:home_story_secondary",
    ]
    assert plan.steps[0].payload["projection_key"] == "home"


def test_projection_materialization_step_payload_roundtrip_is_typed() -> None:
    runtime_opgi_id = UUID("33333333-3333-4333-8333-333333333333")
    spec = ProjectionExperienceMaterializationSpec(
        experience_name="home_story",
        projection_key="home",
        branches=("main",),
        views=(
            ProjectionExperienceViewMaterializationSpec(
                observable_key="security",
                view_key="door",
                api_name="home_views",
                api_view_name="home_story_security_door",
                api_view_ref="home_views.home_story_security_door",
                state_model_ref="aware_home.home.Door",
            ),
            ProjectionExperienceViewMaterializationSpec(
                observable_key="entertainment",
                view_key="tv",
                api_name="home_views",
                api_view_name="home_story_entertainment_tv",
                api_view_ref="home_views.home_story_entertainment_tv",
                state_model_ref="aware_home.home.Tv",
            ),
        ),
        runtime_opgi_id=runtime_opgi_id,
    )

    payload = encode_projection_materialization_step_payload(spec=spec)
    decoded = decode_projection_materialization_step_payload(payload)

    assert decoded == spec


def test_resolve_projection_materialization_specs_rejects_missing_default_view() -> (
    None
):
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "branches": [],
                    "observables": [
                        {
                            "key": "security",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "door",
                                    "is_default": False,
                                    "api_view_ref": "home_views.home_story_security_door",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        }
                    ],
                    "nodes": [],
                }
            ]
        }
    ]

    with pytest.raises(RuntimeError, match="exactly one default view"):
        _ = resolve_projection_materialization_specs(compile_plan_payloads=payloads)


@pytest.mark.asyncio
async def test_materialize_experience_compile_plan_projections_skips_when_no_threads() -> (
    None
):
    receipt = await materialize_experience_compile_plan_projections(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
        planned_processes=(
            {
                "process_key": "boot",
                "threads": [],
            },
        ),
    )

    assert receipt is None


def test_resolve_section_surface_materialization_specs_derives_deterministic_specs() -> (
    None
):
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "branches": [],
                    "observables": [
                        {
                            "key": "overview",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "home",
                                    "is_default": True,
                                    "api_view_ref": "home_views.home_story_overview_home",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                        {
                            "key": "security",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "door",
                                    "is_default": True,
                                    "api_view_ref": "home_views.home_story_security_door",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                    ],
                    "nodes": [
                        {
                            "name": "home",
                            "node_ref": "home.Home",
                            "source_path": "experiences.aware",
                            "identities": [
                                {"key": "home", "source_path": "experiences.aware"}
                            ],
                        },
                        {
                            "name": "doors",
                            "node_ref": "home.Home::doors",
                            "source_path": "experiences.aware",
                            "identities": [
                                {
                                    "key": "front_door",
                                    "source_path": "experiences.aware",
                                }
                            ],
                        },
                    ],
                    "section_surfaces": [
                        {
                            "surface_key": "security.front_door",
                            "section_key": "orchestration",
                            "observable_key": "security",
                            "view_key": "door",
                            "source_path": "experiences.aware",
                            "source_surface_key": None,
                            "graph_identity_ref": "home.front_door",
                            "node_identity_ref": None,
                        },
                        {
                            "surface_key": "home.primary",
                            "section_key": "primary",
                            "observable_key": "overview",
                            "view_key": "home",
                            "source_path": "experiences.aware",
                            "source_surface_key": None,
                            "graph_identity_ref": "home",
                            "node_identity_ref": None,
                        },
                    ],
                }
            ],
            "graph_ontology": [
                {
                    "graph": {
                        "name": "home_default",
                        "experience": "home_story",
                        "root_ref": "home",
                        "source_path": "graphs.aware",
                    },
                    "identities": [
                        {
                            "ref": "home",
                            "node_name": "home",
                            "identity_key": "home",
                            "key": "home",
                            "is_root": True,
                            "source_path": "graphs.aware",
                        },
                        {
                            "ref": "front_door",
                            "node_name": "doors",
                            "identity_key": "front_door",
                            "key": "home.front_door",
                            "is_root": False,
                            "source_path": "graphs.aware",
                        },
                    ],
                    "node_identity_edges": [],
                    "graph_identity_edges": [],
                }
            ],
        }
    ]

    specs = resolve_section_surface_materialization_specs(
        compile_plan_payloads=payloads
    )

    assert specs == (
        ProjectionExperienceSectionSurfaceMaterializationSpec(
            experience_name="home_story",
            projection_key="home",
            surfaces=(
                ProjectionExperienceSectionSurfaceBindingSpec(
                    surface_key="security.front_door",
                    section_key="orchestration",
                    observable_key="security",
                    view_key="door",
                    source_path="experiences.aware",
                    source_surface_key=None,
                    graph_identity_ref="home.front_door",
                    node_identity_ref=None,
                ),
                ProjectionExperienceSectionSurfaceBindingSpec(
                    surface_key="home.primary",
                    section_key="primary",
                    observable_key="overview",
                    view_key="home",
                    source_path="experiences.aware",
                    source_surface_key=None,
                    graph_identity_ref="home",
                    node_identity_ref=None,
                ),
            ),
        ),
    )


def test_resolve_section_surface_materialization_specs_binds_layout_section_id() -> (
    None
):
    layout_config_id = stable_layout_config_id(key="coordination_feed")
    layout_section_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key="primary",
    )
    payloads = [
        {
            "fqn_prefix": "aware://experiences/aware_feeds",
            "projection_experience_ownership": [
                {
                    "name": "aware_feeds",
                    "projection": "feed",
                    "source_path": "experiences.aware",
                    "observables": [
                        {
                            "key": "social",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "feed.v1",
                                    "is_default": True,
                                    "api_view_ref": "feed_views.feed_home_v1",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                    ],
                    "nodes": [
                        {
                            "name": "feed",
                            "node_ref": "social.Feed",
                            "source_path": "experiences.aware",
                            "identities": [
                                {"key": "now", "source_path": "experiences.aware"}
                            ],
                        },
                    ],
                    "section_surfaces": [
                        {
                            "surface_key": "feeds.now",
                            "section_key": "primary",
                            "observable_key": "social",
                            "view_key": "feed.v1",
                            "source_path": "experiences.aware",
                            "source_surface_key": None,
                            "graph_identity_ref": "now",
                            "node_identity_ref": None,
                        },
                    ],
                },
            ],
            "graph_ontology": [
                {
                    "graph": {
                        "name": "feeds_default",
                        "experience": "aware_feeds",
                        "root_ref": "now",
                        "source_path": "graphs.aware",
                    },
                    "identities": [
                        {
                            "ref": "now",
                            "node_name": "feed",
                            "identity_key": "now",
                            "key": "now",
                            "is_root": True,
                            "source_path": "graphs.aware",
                        },
                    ],
                    "node_identity_edges": [],
                    "graph_identity_edges": [],
                },
            ],
            "environment_profile_ownership": [
                {
                    "experience_name": "aware_feeds",
                    "key": "coordination.feed",
                    "source_path": "profiles.aware",
                    "process_configs": [
                        {
                            "type": "continuous",
                            "key": "coordination",
                            "process_key": "coordination",
                            "source_path": "profiles.aware",
                            "is_bootstrap_default": True,
                            "thread_configs": [
                                {
                                    "key": "coordination.feed",
                                    "thread_key": "coordination.feed",
                                    "source_path": "profiles.aware",
                                    "is_default": True,
                                    "projection_experiences": [
                                        {
                                            "projection_experience_name": "aware_feeds",
                                            "source_path": "profiles.aware",
                                            "view_key": "social.feed.v1",
                                            "is_default": True,
                                        },
                                    ],
                                    "layout_configs": [
                                        {
                                            "layout_key": "coordination_feed",
                                            "source_path": "profiles.aware",
                                            "key": "coordination_feed",
                                            "is_default": True,
                                            "sections": [
                                                {
                                                    "section_key": "primary",
                                                    "projection_experience_name": (
                                                        "aware_feeds"
                                                    ),
                                                    "view_key": "social.feed.v1",
                                                    "source_path": "profiles.aware",
                                                    "key": "primary",
                                                    "section_graph_binding_key": (
                                                        "feeds.now"
                                                    ),
                                                    "is_default": True,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        }
    ]

    specs = resolve_section_surface_materialization_specs(
        compile_plan_payloads=payloads
    )

    assert specs == (
        ProjectionExperienceSectionSurfaceMaterializationSpec(
            experience_name="aware_feeds",
            projection_key="feed",
            surfaces=(
                ProjectionExperienceSectionSurfaceBindingSpec(
                    surface_key="feeds.now",
                    section_key="primary",
                    observable_key="social",
                    view_key="feed.v1",
                    source_path="experiences.aware",
                    layout_config_section_config_id=layout_section_id,
                    source_surface_key=None,
                    graph_identity_ref="now",
                    node_identity_ref=None,
                ),
            ),
            layout_bindings=(
                ProjectionExperienceLayoutGraphBindingSpec(
                    layout_config_id=layout_config_id,
                    binding_key="coordination_feed",
                    section_graph_binding_keys=("feeds.now",),
                ),
            ),
        ),
    )


def test_build_section_surface_materialization_plan_emits_deterministic_steps() -> None:
    specs = (
        ProjectionExperienceSectionSurfaceMaterializationSpec(
            experience_name="home_story",
            projection_key="home",
            surfaces=(
                ProjectionExperienceSectionSurfaceBindingSpec(
                    surface_key="home.primary",
                    section_key="primary",
                    observable_key="overview",
                    view_key="home",
                    source_path="experiences.aware",
                    graph_identity_ref="home",
                ),
            ),
        ),
    )

    plan = build_section_surface_materialization_plan(lane=_lane(), specs=specs)

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.section_surface"
    assert [step.step_id for step in plan.steps] == ["section_surface:home_story"]
    assert plan.steps[0].payload["projection_key"] == "home"


def test_section_surface_materialization_step_payload_roundtrip_is_typed() -> None:
    spec = ProjectionExperienceSectionSurfaceMaterializationSpec(
        experience_name="home_story",
        projection_key="home",
        layout_bindings=(
            ProjectionExperienceLayoutGraphBindingSpec(
                layout_config_id=stable_layout_config_id(key="configuration_map"),
                binding_key="configuration_map",
                section_graph_binding_keys=(
                    "home.primary",
                    "security.front_door",
                ),
            ),
        ),
        surfaces=(
            ProjectionExperienceSectionSurfaceBindingSpec(
                surface_key="security.front_door",
                section_key="orchestration",
                observable_key="security",
                view_key="door",
                source_path="experiences.aware",
                graph_identity_ref="home.front_door",
            ),
            ProjectionExperienceSectionSurfaceBindingSpec(
                surface_key="home.primary",
                section_key="primary",
                observable_key="overview",
                view_key="home",
                source_path="experiences.aware",
                graph_identity_ref="home",
            ),
        ),
    )

    payload = encode_section_surface_materialization_step_payload(spec=spec)
    decoded = decode_section_surface_materialization_step_payload(payload)

    assert decoded == spec


def test_projection_snapshot_builds_layout_graph_binding_rows() -> None:
    object_projection_graph_identity_id = UUID("55555555-5555-4555-8555-555555555555")
    layout_config_id = stable_layout_config_id(key="configuration_map")
    primary_section_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key="primary",
    )
    orchestration_section_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key="orchestration",
    )
    overview_view_id = UUID("66666666-6666-4666-8666-666666666666")
    door_view_id = UUID("77777777-7777-4777-8777-777777777777")
    home_graph_identity_id = UUID("88888888-8888-4888-8888-888888888888")
    door_graph_identity_id = UUID("99999999-9999-4999-8999-999999999999")

    projection_experience, objects_by_id = (
        snapshot_commit._build_projection_experience_objects(
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            name="home_story",
            branches=(),
            views=(),
            nodes=(),
            oigis=(),
            section_graph_bindings=(
                ExperienceSectionGraphBindingSnapshot(
                    layout_config_section_config_id=primary_section_id,
                    projection_experience_view_id=overview_view_id,
                    projection_experience_graph_identity_id=home_graph_identity_id,
                    binding_key="home.primary",
                    section_key="primary",
                ),
                ExperienceSectionGraphBindingSnapshot(
                    layout_config_section_config_id=orchestration_section_id,
                    projection_experience_view_id=door_view_id,
                    projection_experience_graph_identity_id=door_graph_identity_id,
                    binding_key="security.front_door",
                    section_key="orchestration",
                ),
            ),
            layout_graph_bindings=(
                ExperienceLayoutGraphBindingSnapshot(
                    layout_config_id=layout_config_id,
                    binding_key="configuration_map",
                    section_graph_binding_keys=(
                        "home.primary",
                        "security.front_door",
                    ),
                ),
            ),
        )
    )

    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        name="home_story",
    )
    layout_binding_id = stable_projection_experience_layout_graph_binding_id(
        projection_experience_id=projection_experience_id,
        layout_config_id=layout_config_id,
        binding_key="configuration_map",
    )
    primary_binding_id = stable_projection_experience_section_graph_binding_id(
        projection_experience_id=projection_experience_id,
        layout_config_section_config_id=primary_section_id,
        projection_experience_view_id=overview_view_id,
        projection_experience_graph_identity_id=home_graph_identity_id,
        binding_key="home.primary",
    )
    door_binding_id = stable_projection_experience_section_graph_binding_id(
        projection_experience_id=projection_experience_id,
        layout_config_section_config_id=orchestration_section_id,
        projection_experience_view_id=door_view_id,
        projection_experience_graph_identity_id=door_graph_identity_id,
        binding_key="security.front_door",
    )

    assert len(projection_experience.projection_experience_layout_graph_bindings) == 1
    layout_binding = projection_experience.projection_experience_layout_graph_bindings[
        0
    ]
    assert layout_binding.id == layout_binding_id
    assert layout_binding.layout_config_id == layout_config_id
    assert layout_binding.binding_key == "configuration_map"
    assert {
        row.section_graph_binding_id
        for row in layout_binding.layout_section_graph_bindings
    } == {primary_binding_id, door_binding_id}
    assert {row.id for row in layout_binding.layout_section_graph_bindings} == {
        stable_projection_experience_layout_section_graph_binding_id(
            projection_experience_layout_graph_binding_id=layout_binding_id,
            section_graph_binding_id=primary_binding_id,
        ),
        stable_projection_experience_layout_section_graph_binding_id(
            projection_experience_layout_graph_binding_id=layout_binding_id,
            section_graph_binding_id=door_binding_id,
        ),
    }
    assert layout_binding_id in objects_by_id


def test_section_surface_materialization_step_payload_preserves_runtime_opgi_id() -> (
    None
):
    runtime_opgi_id = UUID("44444444-4444-4444-8444-444444444444")
    spec = ProjectionExperienceSectionSurfaceMaterializationSpec(
        experience_name="layout_section",
        projection_key="layoutsection",
        surfaces=(
            ProjectionExperienceSectionSurfaceBindingSpec(
                surface_key="identity.admission",
                section_key="identity_admission",
                observable_key="default",
                view_key="default",
                source_path="graphs.aware",
                graph_identity_ref="identity.admission",
            ),
        ),
        runtime_opgi_id=runtime_opgi_id,
    )

    payload = encode_section_surface_materialization_step_payload(spec=spec)
    decoded = decode_section_surface_materialization_step_payload(payload)

    assert decoded == spec


def test_section_surface_projection_experience_lookup_scopes_by_runtime_opgi() -> None:
    stale_opgi_id = UUID("88888888-8888-4888-8888-888888888888")
    runtime_opgi_id = UUID("99999999-9999-4999-8999-999999999999")
    stale_experience_id = uuid4()
    runtime_experience_id = uuid4()
    session = _ObjectListSession(
        ProjectionExperience(
            id=stale_experience_id,
            object_projection_graph_identity_id=stale_opgi_id,
            name="aware_conversation_spaces",
        ),
        ProjectionExperience(
            id=runtime_experience_id,
            object_projection_graph_identity_id=runtime_opgi_id,
            name="aware_conversation_spaces",
        ),
    )

    experience_ids = materialization_service._projection_experience_ids_by_name_and_opgi_from_session(
        projection_session=cast(Any, session),
    )

    assert experience_ids[("aware_conversation_spaces", runtime_opgi_id)] == (
        runtime_experience_id
    )
    assert experience_ids[("aware_conversation_spaces", stale_opgi_id)] == (
        stale_experience_id
    )


def test_section_surface_view_lookup_uses_projection_view_key_not_api_identity() -> (
    None
):
    projection_experience_id = uuid4()
    expected_view_id = uuid4()

    session = _ObjectListSession(
        ProjectionExperienceView(
            id=expected_view_id,
            projection_experience_id=projection_experience_id,
            api_view_id=uuid4(),
            name="channel.heads.v1",
        ),
        ProjectionExperienceView(
            id=uuid4(),
            projection_experience_id=uuid4(),
            api_view_id=uuid4(),
            name="channel.heads.v1",
        ),
    )

    view_ids = materialization_service._projection_experience_view_ids_by_projection_key_from_session(
        projection_session=cast(Any, session)
    )

    assert view_ids[(projection_experience_id, "channel.heads.v1")] == (
        expected_view_id
    )


def test_section_surface_view_lookup_rejects_duplicate_projection_view_key() -> None:
    projection_experience_id = uuid4()

    session = _ObjectListSession(
        ProjectionExperienceView(
            id=uuid4(),
            projection_experience_id=projection_experience_id,
            api_view_id=uuid4(),
            name="channel.heads.v1",
        ),
        ProjectionExperienceView(
            id=uuid4(),
            projection_experience_id=projection_experience_id,
            api_view_id=uuid4(),
            name="channel.heads.v1",
        ),
    )

    with pytest.raises(RuntimeError, match="duplicate committed"):
        materialization_service._projection_experience_view_ids_by_projection_key_from_session(
            projection_session=cast(Any, session)
        )


def test_section_surface_snapshot_preserves_committed_projection_view_catalog() -> None:
    projection_experience_id = uuid4()
    view_id = uuid4()
    api_view_id = uuid4()
    api_view_capability_endpoint_id = uuid4()
    api_capability_endpoint_id = uuid4()
    action_config_id = uuid4()
    node_id = uuid4()
    ignored_projection_experience_id = uuid4()

    session = _ObjectListSession(
        ProjectionExperienceBranch(
            id=uuid4(),
            projection_experience_id=projection_experience_id,
            name="main",
        ),
        ProjectionExperienceView(
            id=view_id,
            projection_experience_id=projection_experience_id,
            api_view_id=uuid4(),
            name="chat.selector.v1",
        ),
        ProjectionExperienceViewStateProvider(
            id=uuid4(),
            projection_experience_view_id=view_id,
            provider_ref="aware_conversation_sdk.selector",
            provider_kind="runtime_callable",
            purity="pure_read",
        ),
        ExperienceInvocationActionConfig(
            id=action_config_id,
            projection_experience_id=projection_experience_id,
            target_kind=ExperienceInvocationActionTargetKind.sdk,
            sdk_operation_id=uuid4(),
        ),
        ProjectionExperienceViewInvocationActionConfig(
            id=uuid4(),
            projection_experience_view_id=view_id,
            api_view_capability_endpoint_id=api_view_capability_endpoint_id,
            api_view_capability_endpoint=ApiViewCapabilityEndpoint.model_construct(
                id=api_view_capability_endpoint_id,
                api_view_id=api_view_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                action_key="select_active",
                endpoint_ref="conversation.selector.select_active",
            ),
            experience_invocation_action_config_id=action_config_id,
            action_key="select_active",
        ),
        ProjectionExperienceNode(
            id=node_id,
            projection_experience_id=projection_experience_id,
            object_projection_graph_node_id=uuid4(),
            key="space",
        ),
        ProjectionExperienceNodeIdentity(
            id=uuid4(),
            projection_experience_node_id=node_id,
            key="default",
        ),
        ProjectionExperienceView(
            id=uuid4(),
            projection_experience_id=ignored_projection_experience_id,
            api_view_id=uuid4(),
            name="chat.unrelated.v1",
        ),
    )

    branches = preserve_projection_branch_snapshots_from_session(
        projection_session=cast(Any, session),
        projection_experience_id=projection_experience_id,
    )
    views = preserve_projection_view_snapshots_from_session(
        projection_session=cast(Any, session),
        projection_experience_id=projection_experience_id,
    )
    nodes = preserve_projection_node_snapshots_from_session(
        projection_session=cast(Any, session),
        projection_experience_id=projection_experience_id,
    )

    assert [branch.name for branch in branches] == ["main"]
    assert [view.name for view in views] == ["chat.selector.v1"]
    assert views[0].state_provider_ref == "aware_conversation_sdk.selector"
    assert [action.action_key for action in views[0].invocation_actions] == [
        "select_active"
    ]
    assert [node.key for node in nodes] == ["space"]
    assert nodes[0].identity_keys == ("default",)


@pytest.mark.asyncio
async def test_binding_portal_source_identity_uses_committed_domain_oig(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    domain_oig_id = uuid4()
    author_id = uuid4()
    projection_hash = "projection-experience"
    head_reads: list[dict[str, object]] = []
    ensure_calls: list[dict[str, object]] = []

    class _FakeStore:
        async def head(self, **kwargs: object) -> dict[str, object]:
            head_reads.append(dict(kwargs))
            return {
                "commit_id": uuid4(),
                "object_instance_graph_id": str(domain_oig_id),
            }

    async def _fake_ensure_identity(**kwargs: object) -> None:
        ensure_calls.append(dict(kwargs))

    monkeypatch.setattr(snapshot_commit, "FSCommitStore", _FakeStore)
    monkeypatch.setattr(
        snapshot_commit,
        "ensure_object_instance_graph_identity_lane_head",
        _fake_ensure_identity,
    )
    index = SimpleNamespace(
        opg_by_hash={projection_hash: SimpleNamespace(id=uuid4())},
    )

    await snapshot_commit._ensure_binding_portal_source_identity(  # noqa: SLF001
        index=cast(MetaGraphRuntimeIndex, index),
        author_id=author_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        label="binding-source",
    )

    assert head_reads == [
        {"branch_id": branch_id, "projection_hash": projection_hash}
    ]
    assert len(ensure_calls) == 1
    assert ensure_calls[0]["object_instance_graph_id"] == domain_oig_id
    assert ensure_calls[0]["domain_projection_hash"] == projection_hash


@pytest.mark.asyncio
async def test_projection_snapshot_commits_binding_children_and_portals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class_fqns = (
        "aware_experience.projection.ProjectionExperienceView",
        "aware_experience.projection.ProjectionExperienceGraphIdentity",
        "aware_experience.projection.ProjectionExperienceSectionGraphBinding",
        "aware_attention.layout.LayoutConfig",
        "aware_attention.layout.LayoutConfigSectionConfig",
    )
    class_configs = {}
    for class_fqn in class_fqns:
        class_id = uuid4()
        class_configs[class_id] = SimpleNamespace(
            id=class_id,
            class_fqn=class_fqn,
        )
    index = SimpleNamespace(class_configs_by_id=class_configs)
    projection_branch_id = uuid4()
    layout_config_id = uuid4()
    section_key = "primary"
    section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key=section_key,
    )
    commit_calls: list[dict[str, object]] = []
    attach_calls: list[dict[str, object]] = []
    ensure_calls: list[dict[str, object]] = []
    source_identity_calls: list[dict[str, object]] = []
    branch_ids_by_object_id: dict[UUID, UUID] = {}

    async def _fake_commit_snapshot(**kwargs: object):
        commit_calls.append(dict(kwargs))
        commit_id = uuid4()
        return snapshot_commit._SnapshotCommit(  # noqa: SLF001
            commit_id=commit_id,
            head_commit_id=commit_id,
            object_instance_graph_commit_id=uuid4(),
            object_count=len(cast(dict[UUID, object], kwargs["objects_by_id"])),
            change_count=1,
        )

    async def _fake_resolve_portal_branch(**kwargs: object):
        target_object_id = cast(UUID, kwargs["target_object_id"])
        target_branch_id = branch_ids_by_object_id.setdefault(
            target_object_id,
            uuid4(),
        )
        return SimpleNamespace(target_branch_id=target_branch_id)

    async def _fake_attach_portal(**kwargs: object):
        attach_calls.append(dict(kwargs))
        return await _fake_resolve_portal_branch(**kwargs)

    async def _fake_ensure_portal(**kwargs: object):
        ensure_calls.append(dict(kwargs))
        return SimpleNamespace(target_branch_id=uuid4())

    async def _fake_ensure_source_identity(**kwargs: object) -> None:
        source_identity_calls.append(dict(kwargs))

    monkeypatch.setattr(snapshot_commit, "_commit_snapshot", _fake_commit_snapshot)
    monkeypatch.setattr(
        snapshot_commit,
        "resolve_portal_target_branch_ref_for_object",
        _fake_resolve_portal_branch,
    )
    monkeypatch.setattr(
        snapshot_commit,
        "attach_portal_target_branch_relationship_for_object",
        _fake_attach_portal,
    )
    monkeypatch.setattr(
        snapshot_commit,
        "ensure_portal_target_lane_ref_for_object",
        _fake_ensure_portal,
    )
    monkeypatch.setattr(
        snapshot_commit,
        "_ensure_binding_portal_source_identity",
        _fake_ensure_source_identity,
    )

    result = await snapshot_commit.commit_projection_experience_snapshot(
        index=cast(MetaGraphRuntimeIndex, index),
        actor_id=None,
        branch_id=projection_branch_id,
        projection_hash="projection-experience",
        projection_graph_hash="projection-experience-graph",
        section_graph_binding_hash="section-graph-binding",
        layout_graph_binding_hash="layout-graph-binding",
        attention_layout_config_hash="attention-layout-config",
        object_projection_graph_identity_id=uuid4(),
        name="home_story",
        views=(),
        section_graph_bindings=(
            ExperienceSectionGraphBindingSnapshot(
                layout_config_section_config_id=section_config_id,
                projection_experience_view_id=uuid4(),
                projection_experience_graph_identity_id=uuid4(),
                binding_key="home.primary",
                section_key=section_key,
            ),
        ),
        layout_graph_bindings=(
            ExperienceLayoutGraphBindingSnapshot(
                layout_config_id=layout_config_id,
                binding_key="configuration_map",
                section_graph_binding_keys=("home.primary",),
            ),
        ),
    )

    assert [call["projection_hash"] for call in commit_calls] == [
        "projection-experience",
        "section-graph-binding",
        "layout-graph-binding",
    ]
    assert result.section_graph_binding_branch_ids == (
        cast(UUID, commit_calls[1]["branch_id"]),
    )
    assert result.layout_graph_binding_branch_ids == (
        cast(UUID, commit_calls[2]["branch_id"]),
    )
    assert len(result.section_graph_binding_commit_ids) == 1
    assert len(result.layout_graph_binding_commit_ids) == 1
    assert [cast(str, call["projection_hash"]) for call in source_identity_calls] == [
        "projection-experience",
        "section-graph-binding",
        "layout-graph-binding",
    ]
    assert {cast(str, call["target_projection_hash"]) for call in attach_calls} == {
        "section-graph-binding",
        "layout-graph-binding",
    }
    assert {cast(str, call["target_projection_hash"]) for call in ensure_calls} == {
        "projection-experience",
        "projection-experience-graph",
        "attention-layout-config",
        "section-graph-binding",
    }
    attention_portal_calls = [
        call
        for call in ensure_calls
        if call["target_projection_hash"] == "attention-layout-config"
    ]
    assert len(attention_portal_calls) == 2
    assert {
        cast(UUID, call["target_domain_branch_id"]) for call in attention_portal_calls
    } == {layout_config_id}
    parent_portal_calls = [
        call
        for call in ensure_calls
        if call["target_projection_hash"]
        in {"projection-experience", "projection-experience-graph"}
    ]
    assert len(parent_portal_calls) == 2
    assert {
        cast(UUID, call["target_domain_branch_id"]) for call in parent_portal_calls
    } == {projection_branch_id}
    section_portal_call = next(
        call
        for call in ensure_calls
        if call["target_projection_hash"] == "section-graph-binding"
    )
    assert section_portal_call["target_domain_branch_id"] == (
        result.section_graph_binding_branch_ids[0]
    )


def test_merge_projection_node_snapshots_keeps_graph_node_override() -> None:
    object_projection_graph_node_id = uuid4()
    unrelated_object_projection_graph_node_id = uuid4()

    preserved = (
        ExperienceProjectionNodeSnapshot(
            object_projection_graph_node_id=object_projection_graph_node_id,
            key="space",
            identity_keys=("stale",),
        ),
        ExperienceProjectionNodeSnapshot(
            object_projection_graph_node_id=unrelated_object_projection_graph_node_id,
            key="messages",
            identity_keys=("default",),
        ),
    )
    graph_owned = (
        ExperienceProjectionNodeSnapshot(
            object_projection_graph_node_id=object_projection_graph_node_id,
            key="space",
            identity_keys=("default",),
        ),
    )

    merged = merge_projection_node_snapshots(preserved, graph_owned)

    assert [(node.key, node.identity_keys) for node in merged] == [
        ("messages", ("default",)),
        ("space", ("default",)),
    ]


def test_resolve_section_surface_materialization_specs_rejects_unknown_graph_identity() -> (
    None
):
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "branches": [],
                    "observables": [
                        {
                            "key": "overview",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "home",
                                    "is_default": True,
                                    "api_view_ref": "home_views.home_story_overview_home",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        }
                    ],
                    "nodes": [
                        {
                            "name": "home",
                            "node_ref": "home.Home",
                            "source_path": "experiences.aware",
                            "identities": [
                                {"key": "home", "source_path": "experiences.aware"}
                            ],
                        }
                    ],
                    "section_surfaces": [
                        {
                            "surface_key": "home.primary",
                            "section_key": "primary",
                            "observable_key": "overview",
                            "view_key": "home",
                            "source_path": "experiences.aware",
                            "source_surface_key": None,
                            "graph_identity_ref": "missing",
                            "node_identity_ref": None,
                        }
                    ],
                }
            ],
            "graph_ontology": [
                {
                    "graph": {
                        "name": "home_default",
                        "experience": "home_story",
                        "root_ref": "home",
                        "source_path": "graphs.aware",
                    },
                    "identities": [
                        {
                            "ref": "home",
                            "node_name": "home",
                            "identity_key": "home",
                            "key": "home",
                            "is_root": True,
                            "source_path": "graphs.aware",
                        }
                    ],
                    "node_identity_edges": [],
                    "graph_identity_edges": [],
                }
            ],
        }
    ]

    with pytest.raises(RuntimeError, match="unknown graph identity"):
        _ = resolve_section_surface_materialization_specs(
            compile_plan_payloads=payloads
        )


@pytest.mark.asyncio
async def test_materialize_experience_compile_plan_section_surfaces_skips_when_no_threads() -> (
    None
):
    receipt = await materialize_experience_compile_plan_section_surfaces(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
        planned_processes=(
            {
                "process_key": "boot",
                "threads": [],
            },
        ),
    )

    assert receipt is None


def test_resolve_graph_materialization_specs_derives_deterministic_graph_step_specs() -> (
    None
):
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "nodes": [
                        {
                            "name": "home",
                            "node_ref": "home.Home",
                            "source_path": "experiences.aware",
                            "identities": [
                                {"key": "home", "source_path": "experiences.aware"}
                            ],
                        },
                        {
                            "name": "doors",
                            "node_ref": "home.Home::doors",
                            "source_path": "experiences.aware",
                            "identities": [
                                {
                                    "key": "front_door",
                                    "source_path": "experiences.aware",
                                }
                            ],
                        },
                        {
                            "name": "tvs",
                            "node_ref": "home.Home::tvs",
                            "source_path": "experiences.aware",
                            "identities": [
                                {
                                    "key": "living_room_tv",
                                    "source_path": "experiences.aware",
                                }
                            ],
                        },
                    ],
                }
            ],
            "graph_ontology": [
                {
                    "graph": {
                        "name": "home_default",
                        "experience": "home_story",
                        "root_ref": "home",
                        "source_path": "graphs.aware",
                    },
                    "identities": [
                        {
                            "ref": "home",
                            "node_name": "home",
                            "identity_key": "home",
                            "key": "home",
                            "is_root": True,
                            "source_path": "graphs.aware",
                        },
                        {
                            "ref": "front_door",
                            "node_name": "doors",
                            "identity_key": "front_door",
                            "key": "home.front_door",
                            "is_root": False,
                            "source_path": "graphs.aware",
                        },
                        {
                            "ref": "living_room_tv",
                            "node_name": "tvs",
                            "identity_key": "living_room_tv",
                            "key": "home.living_room_tv",
                            "is_root": False,
                            "source_path": "graphs.aware",
                        },
                    ],
                    "node_identity_edges": [
                        {
                            "parent_ref": "home",
                            "child_ref": "front_door",
                            "parent_key": "home",
                            "child_key": "home.front_door",
                            "key": "home.front_door",
                            "source_path": "graphs.aware",
                        },
                        {
                            "parent_ref": "home",
                            "child_ref": "living_room_tv",
                            "parent_key": "home",
                            "child_key": "home.living_room_tv",
                            "key": "home.living_room_tv",
                            "source_path": "graphs.aware",
                        },
                    ],
                    "graph_identity_edges": [
                        {
                            "parent_ref": "home",
                            "child_ref": "front_door",
                            "parent_key": "home",
                            "child_key": "home.front_door",
                            "key": "home.front_door",
                            "source_path": "graphs.aware",
                        },
                        {
                            "parent_ref": "home",
                            "child_ref": "living_room_tv",
                            "parent_key": "home",
                            "child_key": "home.living_room_tv",
                            "key": "home.living_room_tv",
                            "source_path": "graphs.aware",
                        },
                    ],
                }
            ],
        }
    ]

    specs = resolve_graph_materialization_specs(compile_plan_payloads=payloads)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.experience_name == "home_story"
    assert spec.projection_key == "home"
    assert spec.graph_name == "home_default"
    assert [node.name for node in spec.nodes] == ["doors", "home", "tvs"]
    assert [identity.ref for identity in spec.identities] == [
        "home",
        "front_door",
        "living_room_tv",
    ]
    assert len(spec.node_identity_edges) == 2
    assert len(spec.graph_identity_edges) == 2


def test_resolve_graph_materialization_specs_keeps_source_projection_key_after_runtime_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_opgi_id = UUID("55555555-5555-4555-8555-555555555555")

    class _Resolver:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[str, ...]]] = []

        def resolve(
            self,
            *,
            projection_key: str,
            node_refs,
            experience_name: str,
            context: str,
        ) -> SimpleNamespace:
            _ = experience_name, context
            resolved_node_refs = tuple(node_refs)
            self.calls.append((projection_key, resolved_node_refs))
            return SimpleNamespace(projection_key="Home", opgi_id=runtime_opgi_id)

    resolver = _Resolver()
    monkeypatch.setattr(
        graph_materialization_service,
        "build_projection_runtime_resolver",
        lambda *, index: resolver,
    )
    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "nodes": [
                        {
                            "name": "home",
                            "node_ref": "home.Home",
                            "source_path": "experiences.aware",
                            "identities": [
                                {"key": "home", "source_path": "experiences.aware"}
                            ],
                        },
                    ],
                }
            ],
            "graph_ontology": [
                {
                    "graph": {
                        "name": "home_default",
                        "experience": "home_story",
                        "root_ref": "home",
                        "source_path": "graphs.aware",
                    },
                    "identities": [
                        {
                            "ref": "home",
                            "node_name": "home",
                            "identity_key": "home",
                            "key": "home",
                            "is_root": True,
                            "source_path": "graphs.aware",
                        },
                    ],
                    "node_identity_edges": [],
                    "graph_identity_edges": [],
                }
            ],
        }
    ]

    specs = resolve_graph_materialization_specs(
        compile_plan_payloads=payloads,
        index=_index_stub(),
    )

    assert specs[0].projection_key == "home"
    assert specs[0].runtime_opgi_id == runtime_opgi_id
    assert resolver.calls == [("home", ("home.Home",))]


def test_runtime_opgi_id_resolves_graph_materialization_source_node_alias() -> None:
    runtime_opgi_id = UUID("66666666-6666-4666-8666-666666666666")

    resolved = graph_materialization_service._resolve_projection_opgi_entry(
        opgi_by_key_casefolded={"layout": (runtime_opgi_id, set())},
        projection_key="layoutsection",
        experience_name="layout_section",
        graph_name="layout_graph",
        runtime_opgi_id=runtime_opgi_id,
    )

    assert resolved[0] == runtime_opgi_id


def test_build_graph_materialization_plan_emits_deterministic_steps() -> None:
    specs = (
        ProjectionExperienceGraphMaterializationSpec(
            experience_name="home_story",
            projection_key="home",
            graph_name="home_default",
            nodes=(
                ProjectionExperienceNodeMaterializationSpec(
                    name="home",
                    node_ref="home.Home",
                    identity_keys=("home",),
                ),
            ),
            identities=(
                ProjectionExperienceGraphIdentityMaterializationSpec(
                    ref="home",
                    key="home",
                    is_root=True,
                ),
            ),
            node_identity_edges=(),
            graph_identity_edges=(),
        ),
        ProjectionExperienceGraphMaterializationSpec(
            experience_name="home_story",
            projection_key="home",
            graph_name="home_secondary",
            nodes=(
                ProjectionExperienceNodeMaterializationSpec(
                    name="home",
                    node_ref="home.Home",
                    identity_keys=("home",),
                ),
                ProjectionExperienceNodeMaterializationSpec(
                    name="doors",
                    node_ref="home.Home::doors",
                    identity_keys=("front_door",),
                ),
            ),
            identities=(
                ProjectionExperienceGraphIdentityMaterializationSpec(
                    ref="home",
                    key="home",
                    is_root=True,
                ),
                ProjectionExperienceGraphIdentityMaterializationSpec(
                    ref="front_door",
                    key="home.front_door",
                    is_root=False,
                ),
            ),
            node_identity_edges=(
                ProjectionExperienceNodeIdentityEdgeMaterializationSpec(
                    parent_ref="home",
                    child_ref="front_door",
                    key="home.front_door",
                ),
            ),
            graph_identity_edges=(
                ProjectionExperienceGraphIdentityEdgeMaterializationSpec(
                    parent_ref="home",
                    child_ref="front_door",
                    key="home.front_door",
                ),
            ),
        ),
    )

    plan = build_graph_materialization_plan(lane=_lane(), specs=specs)

    assert plan.module_id == "experience"
    assert plan.pipeline_id == "experience.compile_plan.graph"
    assert [step.step_id for step in plan.steps] == [
        "graph:home_story:home_default",
        "graph:home_story:home_secondary",
    ]
    assert plan.steps[1].payload["graph_name"] == "home_secondary"


def test_graph_materialization_step_payload_roundtrip_is_typed() -> None:
    runtime_opgi_id = UUID("77777777-7777-4777-8777-777777777777")
    spec = ProjectionExperienceGraphMaterializationSpec(
        experience_name="home_story",
        projection_key="home",
        graph_name="home_default",
        nodes=(
            ProjectionExperienceNodeMaterializationSpec(
                name="home",
                node_ref="home.Home",
                identity_keys=("home",),
            ),
            ProjectionExperienceNodeMaterializationSpec(
                name="doors",
                node_ref="home.Home::doors",
                identity_keys=("front_door",),
            ),
        ),
        identities=(
            ProjectionExperienceGraphIdentityMaterializationSpec(
                ref="home",
                key="home",
                is_root=True,
            ),
            ProjectionExperienceGraphIdentityMaterializationSpec(
                ref="front_door",
                key="home.front_door",
                is_root=False,
            ),
        ),
        node_identity_edges=(
            ProjectionExperienceNodeIdentityEdgeMaterializationSpec(
                parent_ref="home",
                child_ref="front_door",
                key=None,
            ),
        ),
        graph_identity_edges=(
            ProjectionExperienceGraphIdentityEdgeMaterializationSpec(
                parent_ref="home",
                child_ref="front_door",
                key="home.front_door",
            ),
        ),
        runtime_opgi_id=runtime_opgi_id,
    )

    payload = encode_graph_materialization_step_payload(spec=spec)
    decoded = decode_graph_materialization_step_payload(payload)

    assert decoded == spec


def test_graph_relationship_token_match_normalizes_plural_snake_to_class_leaf() -> None:
    assert _relationship_token_matches_target_leaf(
        relationship_token_casefolded="condition_config_attribute_configs",
        target_leaf_casefolded="conditionconfigattributeconfig",
    )


def test_graph_materialization_step_payload_rejects_invalid_node_shape() -> None:
    payload = {
        "experience_name": "home_story",
        "projection_key": "home",
        "graph_name": "home_default",
        "nodes": [
            {
                "name": "home",
                "node_ref": "home.Home",
                "identity_keys": ["home", 7],
            }
        ],
        "identities": [],
        "node_identity_edges": [],
        "graph_identity_edges": [],
    }

    with pytest.raises(RuntimeError, match="nodes\\.0\\.identity_keys"):
        _ = decode_graph_materialization_step_payload(cast(dict[str, object], payload))


@pytest.mark.asyncio
async def test_materialize_experience_compile_plan_graphs_skips_when_no_threads() -> (
    None
):
    receipt = await materialize_experience_compile_plan_graphs(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
        planned_processes=(
            {
                "process_key": "boot",
                "threads": [],
            },
        ),
    )

    assert receipt is None
