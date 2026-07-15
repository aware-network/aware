from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_experience.handlers._generated import (
    meta_handlers as experience_meta_handlers,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphCommitIndex,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationKind,
    MetaGraphImplementationPolicy,
    MetaGraphRuntimeContext,
    MetaGraphRuntimeIndex,
    MetaGraphRuntimeIndexView,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.class_.inline_value_instance.resolution import (
    resolve_class_config_attribute_configs,
)
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from ._experience_runtime_test_paths import REPO_ROOT


_EXPERIENCE_META_HANDLERS_ANY: Any = experience_meta_handlers
_EXPERIENCE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _EXPERIENCE_META_HANDLERS_ANY,
)
_EXPERIENCE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _EXPERIENCE_META_HANDLERS_ANY,
)


def _api_capability_endpoint_id(
    *,
    api_name: str = "identity",
    capability_name: str = "admission",
    endpoint_name: str = "admit_identity",
) -> UUID:
    from aware_api_ontology.stable_ids import (  # noqa: WPS433
        stable_api_capability_endpoint_id,
        stable_api_capability_id,
        stable_api_id,
    )

    api_id = stable_api_id(name=api_name)
    capability_id = stable_api_capability_id(
        api_id=api_id,
        name=capability_name,
    )
    return stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name=endpoint_name,
    )


def _api_view_capability_endpoint_id(
    *, api_view_id: UUID, api_capability_endpoint_id: UUID
) -> UUID:
    from aware_api_ontology.stable_ids import (  # noqa: WPS433
        stable_api_view_capability_endpoint_id,
    )

    return stable_api_view_capability_endpoint_id(
        api_view_id=api_view_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    root: Path
    persistence_backend: str = "fs"
    database_url: str | None = None
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)
        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        if self.database_url is None:
            _ = os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.database_url
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        for key, previous in self._env_overrides.items():
            if previous is None:
                _ = os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _experience_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    )


def _build_experience_meta_runtime(repo_root: Path, *, workspace_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_package_manifest_paths(repo_root),
        workspace_root=workspace_root,
        handler_modules=(_EXPERIENCE_META_HANDLER_MODULE,),
        bootstrap_modules=(_EXPERIENCE_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _implementation_kind(
    context: MetaGraphRuntimeContext,
    *,
    owner_key: str,
    function_name: str,
) -> MetaGraphImplementationKind:
    view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, cast(object, context.index)),
        implementation_policy=context.implementation_policy,
    )
    for descriptor in view.implementation_descriptors_by_id.values():
        function_config = descriptor.function_config
        if (
            function_config.owner_key == owner_key
            and function_config.name == function_name
        ):
            return descriptor.kind
    raise AssertionError(f"Function descriptor not found: {owner_key}.{function_name}")


def _has_meta_handler(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in experience_meta_handlers.AWARE_META_GRAPH_HANDLERS
    )


def _has_empty_lane_bootstrap(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in experience_meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
    )


def _projection_contains_class(
    context: MetaGraphRuntimeContext,
    *,
    projection_name: str,
    class_fqn: str,
) -> bool:
    projection_hash = context.projection_hash_for_name(projection_name)
    opg = context.index.opg_by_hash[projection_hash]
    class_config_ids = {
        class_config.id
        for class_config in context.index.class_configs_by_id.values()
        if class_config.class_fqn == class_fqn
    }
    return any(
        node.class_config_id in class_config_ids
        for node in opg.object_projection_graph_nodes
    )


def _class_config_id(context: MetaGraphRuntimeContext, *, class_name: str) -> UUID:
    matches = tuple(
        class_config.id
        for class_config in context.index.class_configs_by_id.values()
        if class_config.name == class_name
    )
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one ClassConfig named {class_name!r}, got {len(matches)}"
        )
    return matches[0]


def _attribute_config_for_class(
    context: MetaGraphRuntimeContext,
    *,
    class_config_id: UUID,
    attribute_name: str,
):
    class_config = context.index.class_configs_by_id[class_config_id]
    matches = tuple(
        link.attribute_config
        for link in resolve_class_config_attribute_configs(
            class_config=class_config,
            class_configs_by_id=context.index.class_configs_by_id,
        )
        if link.attribute_config is not None
        and link.attribute_config.name == attribute_name
    )
    if len(matches) != 1:
        raise AssertionError(
            "Expected one AttributeConfig "
            f"{attribute_name!r} on ClassConfig {class_config_id}, got {len(matches)}"
        )
    return matches[0]


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


@pytest.mark.asyncio
async def test_experience_view_invocation_action_uses_meta_generated_handler_contract(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_experience_ontology  # noqa: F401

    generated_source = Path(experience_meta_handlers.__file__).read_text(
        encoding="utf-8",
    )
    assert "aware_runtime.function_call.executor" not in generated_source

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None

    assert _has_meta_handler(
        owner_key="aware_experience.projection.ProjectionExperienceView",
        function_name="add_invocation_action",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.projection.ProjectionExperienceView",
        function_name="create_instance",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.projection.ProjectionExperienceSection",
        function_name="bind_view",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.projection.ProjectionExperienceViewInstance",
        function_name="record_action_invocation",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=(
            "aware_experience.projection."
            "ProjectionExperienceViewInvocationActionConfig"
        ),
        function_name="build_via_projection_experience_view",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=("aware_experience.invocation." "ExperienceInvocationActionConfig"),
        function_name="build_via_projection_experience",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=("aware_experience.invocation." "ExperienceInvocationAction"),
        function_name="build",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=("aware_experience.projection." "ProjectionExperienceViewInstance"),
        function_name="build_via_projection_experience_view",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=("aware_experience.projection." "ProjectionExperienceSection"),
        function_name="build_via_projection_experience",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=("aware_experience.projection." "ProjectionExperienceSectionView"),
        function_name="build_via_projection_experience_section",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=(
            "aware_experience.projection." "ProjectionExperienceViewInvocationAction"
        ),
        function_name="build",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=("aware_experience.invocation." "ExperienceInvocationActionCommit"),
        function_name="build_via_experience_invocation_action",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=(
            "aware_experience.invocation." "ExperienceInvocationActionCommitEvent"
        ),
        function_name="build_via_experience_invocation_action_commit",
    )
    assert _has_empty_lane_bootstrap(
        owner_key=(
            "aware_experience.invocation." "ExperienceInvocationActionPropagation"
        ),
        function_name="build_via_experience_invocation_action",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.connector.ConnectorConfig",
        function_name="create",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.connector.ConnectorProvider",
        function_name="build_via_connector_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.connector.ConnectorSession",
        function_name="build_via_connector_provider",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.connector.Connector",
        function_name="build_via_connector_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.sensor.SensorConfig",
        function_name="build_via_connector_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.sensor.Sensor",
        function_name="build_via_sensor_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.sensor.SensorInvocationActionConfig",
        function_name="build_via_sensor_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.sensor.SensorInvocationAction",
        function_name="build",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.actuator.ActuatorConfig",
        function_name="build_via_connector_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.actuator.Actuator",
        function_name="build_via_actuator_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.actuator.ActuatorInvocationActionConfig",
        function_name="build_via_actuator_config",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_experience.actuator.ActuatorInvocationAction",
        function_name="build",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.connector.ConnectorConfig",
        function_name="add_provider",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.connector.ConnectorProvider",
        function_name="create_session",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.connector.ConnectorConfig",
        function_name="add_sensor_config",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.connector.ConnectorConfig",
        function_name="add_actuator_config",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.connector.ConnectorConfig",
        function_name="create_connector",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.sensor.SensorConfig",
        function_name="create_sensor",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.sensor.SensorConfig",
        function_name="bind_invocation_action_config",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.sensor.SensorInvocationActionConfig",
        function_name="record_invocation",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.actuator.ActuatorConfig",
        function_name="create_actuator",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.actuator.ActuatorConfig",
        function_name="bind_invocation_action_config",
    )
    assert _has_meta_handler(
        owner_key="aware_experience.actuator.ActuatorInvocationActionConfig",
        function_name="record_invocation",
    )
    assert _projection_contains_class(
        context,
        projection_name="ProjectionExperience",
        class_fqn=("aware_experience.projection." "ProjectionExperienceViewInstance"),
    )
    assert _projection_contains_class(
        context,
        projection_name="ProjectionExperience",
        class_fqn=("aware_experience.projection." "ProjectionExperienceSection"),
    )
    assert _projection_contains_class(
        context,
        projection_name="ProjectionExperience",
        class_fqn=("aware_experience.projection." "ProjectionExperienceSectionView"),
    )
    assert _projection_contains_class(
        context,
        projection_name="ProjectionExperience",
        class_fqn=(
            "aware_experience.projection."
            "ProjectionExperienceViewInvocationActionConfig"
        ),
    )
    assert _projection_contains_class(
        context,
        projection_name="ExperienceInvocationActionConfig",
        class_fqn=("aware_experience.invocation." "ExperienceInvocationActionConfig"),
    )
    assert _projection_contains_class(
        context,
        projection_name="ProjectionExperience",
        class_fqn=(
            "aware_experience.projection." "ProjectionExperienceViewInvocationAction"
        ),
    )
    assert _projection_contains_class(
        context,
        projection_name="ExperienceInvocationAction",
        class_fqn=("aware_experience.invocation." "ExperienceInvocationAction"),
    )
    assert not _projection_contains_class(
        context,
        projection_name="ProjectionExperience",
        class_fqn="aware_experience.connector.ConnectorConfig",
    )
    assert _projection_contains_class(
        context,
        projection_name="ConnectorConfig",
        class_fqn="aware_experience.connector.ConnectorConfig",
    )
    assert _projection_contains_class(
        context,
        projection_name="ConnectorProvider",
        class_fqn="aware_experience.connector.ConnectorProvider",
    )
    assert _projection_contains_class(
        context,
        projection_name="ConnectorSession",
        class_fqn="aware_experience.connector.ConnectorSession",
    )
    assert _projection_contains_class(
        context,
        projection_name="Connector",
        class_fqn="aware_experience.connector.Connector",
    )
    assert _projection_contains_class(
        context,
        projection_name="SensorConfig",
        class_fqn="aware_experience.sensor.SensorConfig",
    )
    assert _projection_contains_class(
        context,
        projection_name="SensorInvocationActionConfig",
        class_fqn="aware_experience.sensor.SensorInvocationActionConfig",
    )
    assert _projection_contains_class(
        context,
        projection_name="SensorInvocationAction",
        class_fqn="aware_experience.sensor.SensorInvocationAction",
    )
    assert _projection_contains_class(
        context,
        projection_name="ActuatorConfig",
        class_fqn="aware_experience.actuator.ActuatorConfig",
    )
    assert _projection_contains_class(
        context,
        projection_name="ActuatorInvocationActionConfig",
        class_fqn=("aware_experience.actuator." "ActuatorInvocationActionConfig"),
    )
    assert _projection_contains_class(
        context,
        projection_name="ActuatorInvocationAction",
        class_fqn="aware_experience.actuator.ActuatorInvocationAction",
    )
    assert (
        _implementation_kind(
            context,
            owner_key="aware_experience.projection.ProjectionExperienceView",
            function_name="add_invocation_action",
        )
        is MetaGraphImplementationKind.language_handler
    )


@pytest.mark.asyncio
async def test_experience_view_invocation_action_commits_via_meta_runtime(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_experience_ontology.projection.projection_experience import (
        ProjectionExperience,
    )
    from aware_experience_ontology.stable_ids import (
        stable_experience_invocation_action_config_id,
        stable_projection_experience_id,
        stable_projection_experience_view_id,
        stable_projection_experience_view_invocation_action_config_id,
    )

    opgi_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-invocation-action/meta-runtime/opgi",
    )
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="aware_identity_admission",
    )
    api_view_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-invocation-action/api-view",
    )
    view_id = stable_projection_experience_view_id(
        projection_experience_id=projection_experience_id,
        name="identity.admission",
    )
    api_capability_endpoint_id = _api_capability_endpoint_id(endpoint_name="open_home")
    api_view_capability_endpoint_id = _api_view_capability_endpoint_id(
        api_view_id=api_view_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )
    experience_action_config_id = stable_experience_invocation_action_config_id(
        projection_experience_id=projection_experience_id,
        target_kind="api",
        entity_id=api_capability_endpoint_id,
    )
    action_config_id = stable_projection_experience_view_invocation_action_config_id(
        projection_experience_view_id=view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
    )
    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ProjectionExperience",
            branch_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/view-invocation-action/branch",
            ),
        )
        with lane.activate(commit=True, publish=False):
            projection_experience = await ProjectionExperience.create(
                object_projection_graph_identity_id=opgi_id,
                name="aware_identity_admission",
            )
        with lane.activate(commit=True, publish=False):
            view = await projection_experience.create_view(
                api_view_id=api_view_id,
                name="identity.admission",
            )
        with lane.activate(commit=True, publish=False):
            experience_action_config = (
                await projection_experience.create_invocation_action_config(
                    target_kind=ExperienceInvocationActionTargetKind.api,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                )
            )
        with lane.activate(commit=True, publish=False):
            action = await view.add_invocation_action(
                api_view_capability_endpoint_id=api_view_capability_endpoint_id,
                experience_invocation_action_config_id=experience_action_config.id,
                action_key="open_home",
                label="Open home",
                receipt_policy="show_receipt",
            )

        assert projection_experience.id == projection_experience_id
        assert view.id == view_id
        assert action.id == action_config_id
        assert (
            action.experience_invocation_action_config_id == experience_action_config_id
        )
        assert action.api_view_capability_endpoint_id == api_view_capability_endpoint_id
        assert lane.last_response is not None
        assert lane.last_response.root_object_id == projection_experience_id
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(projection_experience_id)
    assertions.expect_instance(projection_experience_id)
    assertions.expect_instance(view_id)
    assertions.expect_edge(
        source_id=projection_experience_id,
        target_id=view_id,
        relationship_name="projection_experience_views",
    )


@pytest.mark.asyncio
async def test_action_dispatch_binding_resolves_from_committed_meta_runtime_chain(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_api_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_reactivity_ontology  # noqa: F401
    import aware_sdk_ontology  # noqa: F401
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_api_ontology.api.api_capability_endpoint_request_config import (
        ApiCapabilityEndpointRequestConfig,
    )
    from aware_api_ontology.api.api_capability_endpoint_response_config import (
        ApiCapabilityEndpointResponseConfig,
    )
    from aware_api_ontology.api.api_capability_endpoint_stream_config import (
        ApiCapabilityEndpointStreamConfig,
    )
    from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
        ApiCapabilityEndpointStreamEventKind,
        ApiCapabilityEndpointStreamMode,
    )
    from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )
    from aware_experience.action_dispatch.bridge import (
        derive_action_dispatch_action_execution_id,
        derive_action_dispatch_api_call_key,
        resolve_action_dispatch_binding_from_environment_profile,
    )
    from aware_experience.action_dispatch.composer import (
        ActionDispatchCompositionContext,
        compose_action_request_payload,
    )
    from aware_experience_ontology.action.action_experience import ActionExperience
    from aware_experience_ontology.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )
    from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
        ExperienceInvocationActionTargetKind,
    )
    from aware_experience_ontology.projection.projection_experience import (
        ProjectionExperience,
    )
    from aware_experience_ontology.stable_ids import (
        stable_action_experience_id,
        stable_action_experience_invocation_id,
        stable_action_experience_invocation_request_field_id,
        stable_environment_experience_event_action_id,
        stable_environment_experience_event_id,
        stable_environment_experience_id,
        stable_environment_experience_profile_config_id,
        stable_experience_invocation_action_config_id,
        stable_projection_experience_id,
    )
    from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
        ActionIntentStatus,
    )
    from aware_reactivity_service_dto.reactivity.action_intent import (
        ReactivityActionIntent,
    )
    from aware_reactivity_ontology.action.action_config import ActionConfig

    fqn_prefix = "tests.action_dispatch.home"
    environment_experience_id = stable_environment_experience_id(
        fqn_prefix=fqn_prefix,
    )
    environment_profile_config_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/action-dispatch/meta-runtime/environment-profile",
    )
    profile_key = "home.default"
    profile_config_id = stable_environment_experience_profile_config_id(
        environment_experience_id=environment_experience_id,
        environment_profile_config_id=environment_profile_config_id,
        key=profile_key,
    )
    event_config_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/action-dispatch/meta-runtime/event-config",
    )
    environment_event_id = stable_environment_experience_event_id(
        environment_experience_profile_config_id=profile_config_id,
        event_config_id=event_config_id,
    )
    action_config_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/action-dispatch/meta-runtime/action-config",
    )
    action_experience_id = stable_action_experience_id(
        action_config_id=action_config_id,
    )
    environment_event_action_id = stable_environment_experience_event_action_id(
        environment_experience_event_id=environment_event_id,
        action_experience_id=action_experience_id,
    )
    opgi_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/action-dispatch/meta-runtime/opgi",
    )
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="home_controls",
    )
    api_capability_endpoint_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/action-dispatch/meta-runtime/api-endpoint",
    )
    experience_invocation_action_config_id = (
        stable_experience_invocation_action_config_id(
            projection_experience_id=projection_experience_id,
            target_kind="api",
            entity_id=api_capability_endpoint_id,
        )
    )
    action_binding_id = stable_action_experience_invocation_id(
        action_experience_id=action_experience_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None

        request_class_config_id = _class_config_id(
            context,
            class_name="ActionExperience",
        )
        request_class_config = context.index.class_configs_by_id[
            request_class_config_id
        ]
        request_action_config_attribute = _attribute_config_for_class(
            context,
            class_config_id=request_class_config_id,
            attribute_name="action_config_id",
        )
        response_class_config_id = _class_config_id(
            context,
            class_name="EnvironmentExperienceEvent",
        )
        stream_event_class_config_id = _class_config_id(
            context,
            class_name="EnvironmentExperienceEventAction",
        )
        request_config_id = uuid5(
            NAMESPACE_URL,
            "experience://tests/action-dispatch/meta-runtime/request-config",
        )
        stream_config_id = uuid5(
            NAMESPACE_URL,
            "experience://tests/action-dispatch/meta-runtime/stream-config",
        )
        api_endpoint = ApiCapabilityEndpoint(
            id=api_capability_endpoint_id,
            api_capability_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/action-dispatch/meta-runtime/api-capability",
            ),
            name="lock_door",
            request_config=ApiCapabilityEndpointRequestConfig(
                id=request_config_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                class_config_id=request_class_config_id,
                class_config=request_class_config,
                response_config=ApiCapabilityEndpointResponseConfig(
                    id=uuid5(
                        NAMESPACE_URL,
                        "experience://tests/action-dispatch/meta-runtime/response-config",
                    ),
                    api_capability_endpoint_request_config_id=request_config_id,
                    class_config_id=response_class_config_id,
                ),
                stream_config=ApiCapabilityEndpointStreamConfig(
                    id=stream_config_id,
                    api_capability_endpoint_request_config_id=request_config_id,
                    stream_mode=ApiCapabilityEndpointStreamMode.server,
                    api_capability_endpoint_stream_event_configs=[
                        ApiCapabilityEndpointStreamEventConfig(
                            id=uuid5(
                                NAMESPACE_URL,
                                "experience://tests/action-dispatch/meta-runtime/stream-notice",
                            ),
                            api_capability_endpoint_stream_config_id=stream_config_id,
                            kind=ApiCapabilityEndpointStreamEventKind.notice,
                            class_config_id=stream_event_class_config_id,
                        )
                    ],
                ),
            ),
        )

        projection_lane = runtime.bind(
            projection="ProjectionExperience",
            branch_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/action-dispatch/meta-runtime/projection-branch",
            ),
        )
        with projection_lane.activate(commit=True, publish=False):
            projection_experience = await ProjectionExperience.create(
                object_projection_graph_identity_id=opgi_id,
                name="home_controls",
            )
        with projection_lane.activate(commit=True, publish=False):
            invocation_config = (
                await projection_experience.create_invocation_action_config(
                    target_kind=ExperienceInvocationActionTargetKind.api,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                )
            )
        invocation_config.api_capability_endpoint = api_endpoint
        assert projection_experience.id == projection_experience_id
        assert invocation_config.id == experience_invocation_action_config_id

        action_lane = runtime.bind(
            projection="ActionExperience",
            branch_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/action-dispatch/meta-runtime/action-branch",
            ),
        )
        with action_lane.activate(commit=True, publish=False):
            action_experience = await ActionExperience.build(
                action_config_id=action_config_id,
            )
        action_config = ActionConfig(
            id=action_config_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            api_capability_endpoint=api_endpoint,
            name="lock_door",
            description="Lock the home door",
            action_type="home.door.lock",
        )
        action_experience.action_config = action_config
        with action_lane.activate(commit=True, publish=False):
            action_binding = await action_experience.add_invocation_action_config(
                experience_invocation_action_config_id=invocation_config.id,
            )
        request_field_id = stable_action_experience_invocation_request_field_id(
            action_experience_invocation_id=action_binding_id,
            attribute_config_id=request_action_config_attribute.id,
        )
        with action_lane.activate(commit=True, publish=False):
            request_field = await action_binding.add_request_field(
                attribute_config_id=request_action_config_attribute.id,
                source_ref="intent.action_config_id",
            )
        request_field.attribute_config = request_action_config_attribute
        assert request_field.id == request_field_id
        action_binding.experience_invocation_action_config = invocation_config
        action_binding.request_fields = [request_field]
        action_experience.action_experience_invocations = [action_binding]

        profile_config_lane = runtime.bind(
            projection="EnvironmentExperienceProfileConfig",
            branch_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/action-dispatch/meta-runtime/profile-config-branch",
            ),
        )
        with profile_config_lane.activate(commit=True, publish=False):
            profile_config = await EnvironmentExperienceProfileConfig.build_via_environment_experience(
                environment_experience_id=environment_experience_id,
                environment_profile_config_id=environment_profile_config_id,
                key=profile_key,
                title="Home default",
            )
        with profile_config_lane.activate(commit=True, publish=False):
            event = await profile_config.add_event(event_config_id=event_config_id)
        with profile_config_lane.activate(commit=True, publish=False):
            event_action = await event.add_action_experience(
                action_experience_id=action_experience.id,
            )
        event_action.action_experience = action_experience
        event.actions = [event_action]
        profile_config.events = [event]

        assert profile_config.id == profile_config_id

        profile_config_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=profile_config_lane,
        )

        projection_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=projection_lane,
        )
        action_oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=action_lane,
        )
        intent = ReactivityActionIntent(
            action_intent_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/action-dispatch/meta-runtime/intent",
            ),
            intent_key="tests.action_dispatch.home.lock_door",
            event_id=environment_event_id,
            event_type="home.door.lock_requested",
            source="tests.action_dispatch",
            branch_id=profile_config_lane.branch_id,
            projection_hash=profile_config_lane.binding.projection_hash,
            commit_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/action-dispatch/meta-runtime/event-commit",
            ),
            event_config_condition_config_scope_id=profile_config.id,
            event_config_action_config_id=environment_event_action_id,
            action_config_id=action_config_id,
            action_type="lock_door",
            status=ActionIntentStatus.requested,
        )

    index = cast(MetaGraphRuntimeIndex, cast(object, context.index))
    projection_assertions = MetaOIGAssertions(oig=projection_oig, index=index)
    projection_assertions.expect_root(projection_experience_id)

    action_assertions = MetaOIGAssertions(oig=action_oig, index=index)
    action_assertions.expect_root(action_experience_id)
    action_assertions.expect_instance(action_binding_id)
    _expect_uuid_primitive(
        action_assertions,
        instance_id=action_experience_id,
        field_name="action_config_id",
        expected=action_config_id,
    )
    action_assertions.expect_edge(
        source_id=action_experience_id,
        target_id=action_binding_id,
        relationship_name="action_experience_invocations",
    )
    action_assertions.expect_instance(request_field_id)
    action_assertions.expect_edge(
        source_id=action_binding_id,
        target_id=request_field_id,
        relationship_name="request_fields",
    )
    _expect_uuid_primitive(
        action_assertions,
        instance_id=action_binding_id,
        field_name="experience_invocation_action_config_id",
        expected=experience_invocation_action_config_id,
    )
    _expect_uuid_primitive(
        action_assertions,
        instance_id=request_field_id,
        field_name="attribute_config_id",
        expected=request_action_config_attribute.id,
    )
    assert (
        action_assertions.primitive(
            instance_id=request_field_id,
            field_name="source_ref",
        )
        == "intent.action_config_id"
    )

    profile_config_assertions = MetaOIGAssertions(oig=profile_config_oig, index=index)
    profile_config_assertions.expect_root(profile_config_id)
    profile_config_assertions.expect_instance(environment_event_id)
    profile_config_assertions.expect_instance(environment_event_action_id)
    profile_config_assertions.expect_edge(
        source_id=profile_config_id,
        target_id=environment_event_id,
        relationship_name="events",
    )
    profile_config_assertions.expect_edge(
        source_id=environment_event_id,
        target_id=environment_event_action_id,
        relationship_name="actions",
    )
    _expect_uuid_primitive(
        profile_config_assertions,
        instance_id=environment_event_action_id,
        field_name="action_experience_id",
        expected=action_experience_id,
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile_config,
        intent=intent,
    )

    assert resolution.status == "resolved", resolution
    assert resolution.candidate_count == 1
    assert resolution.binding is not None
    binding = resolution.binding
    assert binding.action_binding_id == action_binding_id
    assert (
        binding.experience_invocation_action_config_id
        == experience_invocation_action_config_id
    )
    assert binding.api_capability_endpoint_id == api_capability_endpoint_id
    assert binding.request_class_config_id == request_class_config_id
    assert binding.response_class_config_id == response_class_config_id
    assert binding.stream_event_class_config_ids == {
        "notice": stream_event_class_config_id,
    }
    assert binding.environment_experience_profile_config_id == profile_config_id
    assert binding.environment_profile_config_id == environment_profile_config_id
    assert binding.environment_profile_key == profile_key
    assert binding.environment_experience_event_id == environment_event_id
    assert binding.action_experience_id == action_experience_id
    assert binding.request_class_config is request_class_config
    assert len(binding.request_fields) == 1
    assert binding.request_fields[0].request_field_id == request_field_id
    assert (
        binding.request_fields[0].attribute_config_id
        == request_action_config_attribute.id
    )
    assert binding.request_fields[0].source_ref == "intent.action_config_id"

    action_execution_id = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
    )
    api_call_key = derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id,
    )
    composed_payload = compose_action_request_payload(
        request_class_config=binding.request_class_config,
        request_fields=binding.request_fields,
        context=ActionDispatchCompositionContext(
            event_id=intent.event_id,
            event_config_id=binding.event_config_id,
            event_activation_id=None,
            event_type=intent.event_type,
            event_source=intent.source,
            event_status=None,
            commit_branch_id=intent.branch_id,
            commit_projection_hash=intent.projection_hash,
            commit_id=intent.commit_id,
            commit_object_instance_graph_id=intent.object_instance_graph_id,
            commit_object_instance_graph_commit_id=None,
            intent_id=intent.action_intent_id,
            intent_key=intent.intent_key,
            intent_action_config_id=intent.action_config_id,
            execution_id=action_execution_id,
            execution_key="primary",
            api_call_key=api_call_key,
            action_binding_id=binding.action_binding_id,
            action_experience_id=binding.action_experience_id,
            environment_profile_id=binding.environment_profile_config_id,
            environment_event_id=binding.environment_experience_event_id,
            invocation_config_id=binding.experience_invocation_action_config_id,
            endpoint_id=binding.api_capability_endpoint_id,
            actor_id=None,
            subscription_id=None,
        ),
        class_configs_by_id=index.class_configs_by_id,
    )
    assert composed_payload == {"action_config_id": intent.action_config_id}


@pytest.mark.asyncio
async def test_experience_view_instance_records_action_invocation_provenance(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_api_ontology  # noqa: F401
    import aware_attention_ontology  # noqa: F401
    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_sdk_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import stable_api_call_id
    from aware_attention_ontology.stable_ids import stable_section_id
    from aware_experience_ontology.projection.projection_experience import (
        ProjectionExperience,
    )
    from aware_experience_ontology.stable_ids import (
        stable_experience_invocation_action_config_id,
        stable_experience_invocation_action_id,
        stable_projection_experience_id,
        stable_projection_experience_section_id,
        stable_projection_experience_section_view_id,
        stable_projection_experience_view_id,
        stable_projection_experience_view_instance_id,
        stable_projection_experience_view_invocation_action_id,
        stable_projection_experience_view_invocation_action_config_id,
    )

    opgi_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-instance-action-invocation/opgi",
    )
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="aware_identity_admission",
    )
    api_view_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-instance-action-invocation/api-view",
    )
    view_id = stable_projection_experience_view_id(
        projection_experience_id=projection_experience_id,
        name="identity.admission",
    )
    api_capability_endpoint_id = _api_capability_endpoint_id(
        endpoint_name="admit_identity"
    )
    api_view_capability_endpoint_id = _api_view_capability_endpoint_id(
        api_view_id=api_view_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )
    experience_action_config_id = stable_experience_invocation_action_config_id(
        projection_experience_id=projection_experience_id,
        target_kind="api",
        entity_id=api_capability_endpoint_id,
    )
    action_config_id = stable_projection_experience_view_invocation_action_config_id(
        projection_experience_view_id=view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
    )
    section_graph_binding_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-instance-action-invocation/section-binding",
    )
    view_instance_id = stable_projection_experience_view_instance_id(
        projection_experience_view_id=view_id,
        section_graph_binding_id=section_graph_binding_id,
        view_instance_key="primary.identity.admission",
    )
    section_id = stable_section_id(key="layout.primary")
    projection_experience_section_id = stable_projection_experience_section_id(
        projection_experience_id=projection_experience_id,
        section_id=section_id,
    )
    projection_experience_section_view_id = (
        stable_projection_experience_section_view_id(
            projection_experience_section_id=projection_experience_section_id,
            projection_experience_view_instance_id=view_instance_id,
        )
    )
    invocation_key = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-instance-action-invocation/invocation",
    )
    experience_invocation_action_id = stable_experience_invocation_action_id(
        experience_invocation_action_config_id=experience_action_config_id,
        invocation_key=invocation_key,
    )
    action_invocation_id = stable_projection_experience_view_invocation_action_id(
        view_invocation_action_config_id=action_config_id,
        experience_invocation_action_id=experience_invocation_action_id,
    )
    api_call_id = stable_api_call_id(
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=invocation_key,
    )
    state_commit_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-instance-action-invocation/state-commit",
    )
    actor_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-instance-action-invocation/actor",
    )
    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ProjectionExperience",
            branch_id=uuid5(
                NAMESPACE_URL,
                "experience://tests/view-instance-action-invocation/branch",
            ),
        )
        with lane.activate(commit=True, publish=False):
            projection_experience = await ProjectionExperience.create(
                object_projection_graph_identity_id=opgi_id,
                name="aware_identity_admission",
            )
        with lane.activate(commit=True, publish=False):
            view = await projection_experience.create_view(
                api_view_id=api_view_id,
                name="identity.admission",
            )
        with lane.activate(commit=True, publish=False):
            experience_action_config = (
                await projection_experience.create_invocation_action_config(
                    target_kind=ExperienceInvocationActionTargetKind.api,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                )
            )
        with lane.activate(commit=True, publish=False):
            action = await view.add_invocation_action(
                api_view_capability_endpoint_id=api_view_capability_endpoint_id,
                experience_invocation_action_config_id=experience_action_config.id,
                action_key="admit_identity",
                label="Admit identity",
                receipt_policy="show_receipt",
            )
        with lane.activate(commit=True, publish=False):
            view_instance = await view.create_instance(
                section_graph_binding_id=section_graph_binding_id,
                view_instance_key="primary.identity.admission",
                state_commit_id=state_commit_id,
                status="active",
            )
        with lane.activate(commit=True, publish=False):
            projection_experience_section = await projection_experience.create_section(
                section_id=section_id,
                section_key="layout.primary",
            )
        with lane.activate(commit=True, publish=False):
            projection_experience_section_view = (
                await projection_experience_section.bind_view(
                    projection_experience_view_instance_id=view_instance.id,
                    status="active",
                )
            )
        with lane.activate(commit=True, publish=False):
            action_invocation = await view_instance.record_action_invocation(
                view_invocation_action_config_id=action.id,
                invocation_key=invocation_key,
                api_call_id=api_call_id,
                actor_id=actor_id,
                request_ref="api://identity/admission/admit_identity/request",
                receipt_ref="event://identity/admitted",
                status="succeeded",
            )

        assert view_instance.id == view_instance_id
        assert projection_experience_section.id == projection_experience_section_id
        assert (
            projection_experience_section_view.id
            == projection_experience_section_view_id
        )
        assert action.id == action_config_id
        assert action_invocation.id == action_invocation_id
        assert action_invocation.view_invocation_action_config_id == action_config_id
        assert (
            action_invocation.experience_invocation_action_id
            == experience_invocation_action_id
        )
        assert action_invocation.experience_invocation_action is not None
        assert action_invocation.experience_invocation_action.status == "succeeded"
        assert lane.last_response is not None
        assert lane.last_response.root_object_id == projection_experience_id
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(projection_experience_id)
    assertions.expect_instance(view_id)
    assertions.expect_instance(projection_experience_section_id)
    assertions.expect_instance(projection_experience_section_view_id)
    assertions.expect_instance(view_instance_id)
    assertions.expect_edge(
        source_id=projection_experience_id,
        target_id=projection_experience_section_id,
        relationship_name="projection_experience_sections",
    )
    assertions.expect_edge(
        source_id=projection_experience_section_id,
        target_id=projection_experience_section_view_id,
        relationship_name="section_views",
    )
    assertions.expect_edge(
        source_id=view_id,
        target_id=view_instance_id,
        relationship_name="view_instances",
    )
    assertions.expect_primitive(
        instance_id=view_instance_id,
        field_name="view_instance_key",
        expected="primary.identity.admission",
    )
    assertions.expect_primitive(
        instance_id=projection_experience_section_id,
        field_name="section_key",
        expected="layout.primary",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=view_id,
        field_name="api_view_id",
        expected=api_view_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=projection_experience_section_view_id,
        field_name="projection_experience_view_instance_id",
        expected=view_instance_id,
    )
    assertions.expect_primitive(
        instance_id=view_instance_id,
        field_name="status",
        expected="active",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=view_instance_id,
        field_name="state_commit_id",
        expected=state_commit_id,
    )


@pytest.mark.asyncio
async def test_projection_snapshot_commits_view_invocation_actions_with_meta_index(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_experience_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    import aware_sdk_ontology  # noqa: F401
    from aware_experience.materialization.snapshot_commit import (
        ExperienceProjectionViewInvocationActionConfigSnapshot,
        ExperienceProjectionViewSnapshot,
        commit_projection_experience_snapshot,
    )
    from aware_experience_ontology.stable_ids import (
        stable_experience_invocation_action_config_id,
        stable_projection_experience_id,
        stable_projection_experience_view_id,
        stable_projection_experience_view_invocation_action_config_id,
    )
    from aware_sdk_ontology.stable_ids import (
        stable_sdk_config_id,
        stable_sdk_operation_api_capability_endpoint_id,
        stable_sdk_operation_api_view_capability_endpoint_id,
        stable_sdk_operation_id,
    )

    opgi_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-invocation-action/snapshot/opgi",
    )
    sdk_config_id = stable_sdk_config_id(name="identity_sdk")
    sdk_operation_id = stable_sdk_operation_id(
        sdk_config_id=sdk_config_id,
        name="admit_identity",
    )
    projection_experience_id = stable_projection_experience_id(
        object_projection_graph_identity_id=opgi_id,
        name="aware_identity_admission",
    )
    api_view_id = uuid5(
        NAMESPACE_URL,
        "experience://tests/view-invocation-action/snapshot/api-view",
    )
    view_id = stable_projection_experience_view_id(
        projection_experience_id=projection_experience_id,
        name="identity.admission",
    )
    api_capability_endpoint_id = _api_capability_endpoint_id(
        endpoint_name="admit_identity"
    )
    api_view_capability_endpoint_id = _api_view_capability_endpoint_id(
        api_view_id=api_view_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )
    sdk_operation_api_capability_endpoint_id = (
        stable_sdk_operation_api_capability_endpoint_id(
            sdk_operation_id=sdk_operation_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            name="admit_identity",
        )
    )
    sdk_operation_api_view_capability_endpoint_id = (
        stable_sdk_operation_api_view_capability_endpoint_id(
            sdk_operation_id=sdk_operation_id,
            sdk_operation_api_capability_endpoint_id=(
                sdk_operation_api_capability_endpoint_id
            ),
            api_view_id=api_view_id,
            api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        )
    )
    experience_action_config_id = stable_experience_invocation_action_config_id(
        projection_experience_id=projection_experience_id,
        target_kind="sdk",
        entity_id=sdk_operation_id,
    )
    action_config_id = stable_projection_experience_view_invocation_action_config_id(
        projection_experience_view_id=view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        projection_hash = context.projection_hash_for_name("ProjectionExperience")
        branch_id = uuid5(
            NAMESPACE_URL,
            "experience://tests/view-invocation-action/snapshot/branch",
        )
        result = await commit_projection_experience_snapshot(
            index=cast(Any, context.index),
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_projection_graph_identity_id=opgi_id,
            name="aware_identity_admission",
            views=(
                ExperienceProjectionViewSnapshot(
                    api_view_id=api_view_id,
                    name="identity.admission",
                    invocation_actions=(
                        ExperienceProjectionViewInvocationActionConfigSnapshot(
                            api_view_capability_endpoint_id=(
                                api_view_capability_endpoint_id
                            ),
                            action_key="admit_identity",
                            sdk_operation_api_view_capability_endpoint_id=(
                                sdk_operation_api_view_capability_endpoint_id
                            ),
                            api_capability_endpoint_id=api_capability_endpoint_id,
                            sdk_operation_id=sdk_operation_id,
                            label="Admit identity",
                            receipt_policy="show_receipt",
                        ),
                    ),
                ),
            ),
        )
        assert len(result.projection_experience.invocation_action_configs) == 1
        assert (
            result.projection_experience.invocation_action_configs[0].id
            == experience_action_config_id
        )
        assert len(result.projection_experience.projection_experience_views) == 1
        snapshot_view = result.projection_experience.projection_experience_views[0]
        assert len(snapshot_view.invocation_action_configs) == 1
        assert snapshot_view.invocation_action_configs[0].id == action_config_id
        head = await FSCommitStore(root_dir=aware_root).head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        assert head is not None
        opg = context.index.opg_by_hash[projection_hash]
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=context.index.ocg,
            opg=opg,
            commit_id=result.commit_id,
            oig_id=UUID(str(head["object_instance_graph_id"])),
            attribute_configs_by_id=context.index.attribute_configs_by_id,
            class_configs_by_id=context.index.class_configs_by_id,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(projection_experience_id)
    assertions.expect_instance(view_id)
    assertions.expect_edge(
        source_id=projection_experience_id,
        target_id=view_id,
        relationship_name="projection_experience_views",
    )
