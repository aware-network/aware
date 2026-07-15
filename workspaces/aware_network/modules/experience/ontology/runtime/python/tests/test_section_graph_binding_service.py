from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]

from aware_api_ontology.api.api_view import ApiView
from aware_api_ontology.api.api_view_capability_endpoint import (
    ApiViewCapabilityEndpoint,
)
from aware_experience.section_graph_binding.api_models import (
    ActivateExperienceSectionGraphBindingRequest,
    ApplyExperienceViewEventTransitionRequest,
    ExperienceSectionGraphBindingDescriptor,
    InvokeExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionRequest,
)
from aware_experience.section_graph_binding.catalog import (
    ExperienceSectionGraphBindingCatalog,
    ExperienceSectionGraphBindingCatalogEntry,
)
import aware_experience.section_graph_binding.service as section_graph_binding_service
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.contracts import ServiceOperationContext
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_section import (
    ProjectionExperienceSection,
)
from aware_experience_ontology.projection.projection_experience_section_view import (
    ProjectionExperienceSectionView,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_experience_ontology.projection.projection_experience_view_instance import (
    ProjectionExperienceViewInstance,
)
from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
    ProjectionExperienceViewInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
    InvokeFunctionResponse,
)
from aware_experience.stable_ids import (
    stable_experience_invocation_action_commit_id,
    stable_experience_invocation_action_id,
    stable_projection_experience_view_invocation_action_id,
)


def test_section_graph_binding_service_does_not_import_attention_provider() -> None:
    source = Path(section_graph_binding_service.__file__).read_text(encoding="utf-8")

    assert "from aware_attention_service import" not in source
    assert "build_aware_attention_service_protocol_handler" not in source


def test_section_graph_binding_service_source_is_clean() -> None:
    source = Path(section_graph_binding_service.__file__).read_text(encoding="utf-8")

    assert "aware_" + "runtime" not in source
    assert "hydrate_orm_graph_" + "from_oig" not in source
    assert "AwareRuntime" + "Index" not in source


@pytest.mark.asyncio
async def test_section_graph_binding_reference_hydration_uses_meta_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "projection-experience-section-graph-binding"
    commit_id = uuid4()
    oig_id = uuid4()
    captured: dict[str, object] = {}

    class _FakeStore:
        async def head(self, **_kwargs: object) -> dict[str, str]:
            return {
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(oig_id),
            }

    class _FakeMaterializer:
        async def get(self, **kwargs: object) -> tuple[object, dict[str, object]]:
            captured["materializer_kwargs"] = kwargs
            return object(), {}

    hydrated_obj = SimpleNamespace(id=uuid4())

    class _FakeScratchSession:
        def imap_all_objects(self) -> tuple[object, ...]:
            return (hydrated_obj,)

    class _TargetSession:
        def __init__(self) -> None:
            self.merged: list[object] = []

        def merge(self, obj: object) -> None:
            self.merged.append(obj)

    def _fake_reify_oig_session(**kwargs: object) -> _FakeScratchSession:
        captured["reifier_kwargs"] = kwargs
        return _FakeScratchSession()

    runtime_index = type(
        "_RuntimeIndex",
        (),
        {
            "ocg": object(),
            "opg_by_hash": {projection_hash: object()},
            "attribute_configs_by_id": {},
            "class_configs_by_id": {},
        },
    )()
    runtime_context = section_graph_binding_service._SectionGraphBindingRuntimeContext(
        host_context=cast(Any, object()),
        graph_gateway=cast(Any, object()),
        runtime_index=cast(Any, runtime_index),
        branch_id=branch_id,
        projection_hashes=(projection_hash,),
    )

    monkeypatch.setattr(section_graph_binding_service, "FSCommitStore", _FakeStore)
    monkeypatch.setattr(
        section_graph_binding_service,
        "CachedLaneMaterializer",
        _FakeMaterializer,
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "reify_oig_session",
        _fake_reify_oig_session,
    )
    session = _TargetSession()

    await section_graph_binding_service._hydrate_projection_into_session(
        runtime_context=runtime_context,
        session=cast(Any, session),
        projection_hash=projection_hash,
    )

    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["commit_id"] == commit_id
    assert materializer_kwargs["oig_id"] == oig_id
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is runtime_index
    assert reifier_kwargs["opg"] is runtime_index.opg_by_hash[projection_hash]
    assert reifier_kwargs["branch_id"] == branch_id
    assert session.merged == [hydrated_obj]


def _service_context() -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="experience.section_graph_binding",
    )


def _environment_context(
    operation_context: ServiceOperationContext,
) -> EnvironmentOperationContext:
    return EnvironmentOperationContext(
        actor_id=operation_context.actor_id,
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=operation_context.branch_id,
        projection_hash=operation_context.projection_hash,
    )


def _service_api_route(
    *,
    api_package_name: str,
) -> ServiceApiDependencyRouteDescriptor:
    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware-experience-service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware-attention-service",
        api_package_id=uuid4(),
        api_package_name=api_package_name,
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id="aware-attention-service-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=_REPO_ROOT / ".aware" / "attention.sock",
        request_timeout_s=5.0,
        service_names=("aware_attention",),
    )


@pytest.mark.asyncio
async def test_runtime_context_uses_host_graph_context_provider_for_meta_sdk_gateway() -> (
    None
):
    branch_id = uuid4()
    projection_hash = "projection-experience-hash"
    runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(
                    name="ProjectionExperience",
                    projection_hash=projection_hash,
                ),
            ],
        ),
    )
    captured: dict[str, object] = {}

    class _GraphContextProvider:
        async def resolve_graph_context(self) -> object:
            captured["provider_called"] = True
            return SimpleNamespace(index=runtime_index)

    class _MetaSdkOnlyGraphGateway:
        async def invoke_function(self, **_kwargs: object) -> object:
            raise AssertionError("not used by runtime-context resolution")

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=cast(Any, _MetaSdkOnlyGraphGateway()),
        graph_context_provider=cast(Any, _GraphContextProvider()),
        service_name="aware_experience",
        experience_reference_branch_ids_by_experience_name={
            "aware_control_identity": branch_id,
        },
    ) as host_context:
        runtime_context = await section_graph_binding_service._resolve_runtime_context(
            host_context=host_context,
            experience_name="aware_control_identity",
            projection_names=("ProjectionExperience",),
        )

    assert captured["provider_called"] is True
    assert runtime_context.runtime_index is runtime_index
    assert runtime_context.branch_id == branch_id
    assert runtime_context.projection_hashes == (projection_hash,)


@pytest.mark.asyncio
async def test_activate_section_graph_binding_routes_projection_observable_to_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection_observable_id = uuid4()
    graph_identity_object_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    catalog = ExperienceSectionGraphBindingCatalog(
        experience_name="workspace_coordination",
        catalog_revision="catalog-rev-001",
        entries=(
            ExperienceSectionGraphBindingCatalogEntry(
                descriptor=ExperienceSectionGraphBindingDescriptor(
                    binding_key="issue.primary",
                    section_key="coordination.primary",
                    projection_observable_id=projection_observable_id,
                    projection_experience_graph_identity_id=graph_identity_object_id,
                    object_projection_graph_identity_id=(
                        object_projection_graph_identity_id
                    ),
                    view_ref="workspace_coordination.detail",
                    graph_identity_ref="issue.graph",
                ),
                projection_observable_id=projection_observable_id,
                graph_identity_object_id=graph_identity_object_id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
            ),
        ),
    )

    captured: dict[str, object] = {}

    async def _fake_resolve_catalog(*, host_context, experience_name):  # type: ignore[no-untyped-def]
        _ = host_context
        assert experience_name == "workspace_coordination"
        return catalog

    async def _fake_activate_attention_section_observable(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return type(
            "_AttentionSnapshot",
            (),
            {
                "exists": True,
                "focus_scope_id": uuid4(),
                "focus_id": uuid4(),
                "observable_id": kwargs["observable_id"],
            },
        )()

    monkeypatch.setattr(
        section_graph_binding_service, "_resolve_catalog", _fake_resolve_catalog
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "_activate_attention_section_observable",
        _fake_activate_attention_section_observable,
    )

    request = ActivateExperienceSectionGraphBindingRequest(
        request_id=uuid4(),
        experience_name="workspace_coordination",
        binding_key="issue.primary",
        rationale="operator selected",
        section_title="Coordination",
        focus_scope_title="Primary issue",
    )

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience",
    ) as host_context:
        response = await section_graph_binding_service.activate_section_graph_binding(
            request=request,
            host_context=host_context,
        )

    assert captured["section_key"] == "coordination.primary"
    assert captured["observable_id"] == projection_observable_id
    assert captured["rationale"] == "operator selected"
    assert captured["section_title"] == "Coordination"
    assert captured["focus_scope_title"] == "Primary issue"
    assert response.catalog_revision == "catalog-rev-001"
    assert response.state.binding.binding_key == "issue.primary"
    assert response.state.binding.projection_observable_id == projection_observable_id
    assert (
        response.state.binding.projection_experience_graph_identity_id
        == graph_identity_object_id
    )
    assert response.state.binding.graph_identity_ref == "issue.graph"
    assert response.state.is_active is True
    assert response.state.projection_observable_id == projection_observable_id
    assert (
        response.state.projection_experience_graph_identity_id
        == graph_identity_object_id
    )
    assert response.state.observable_id == projection_observable_id


@pytest.mark.asyncio
async def test_apply_view_event_transition_activates_target_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection_experience_id = uuid4()
    projection_experience_view_id = uuid4()
    api_view_id = uuid4()
    section_graph_binding_id = uuid4()
    section_id = uuid4()
    projection_experience_section_id = uuid4()
    projection_experience_section_view_id = uuid4()
    projection_experience_view_instance_id = uuid4()
    view_invocation_action_config_id = uuid4()
    experience_invocation_action_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    api_view_capability_endpoint_id = uuid4()
    projection_observable_id = uuid4()
    graph_identity_object_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    catalog = ExperienceSectionGraphBindingCatalog(
        experience_name="aware_control_identity",
        catalog_revision="catalog-rev-actor-home",
        entries=(
            ExperienceSectionGraphBindingCatalogEntry(
                descriptor=ExperienceSectionGraphBindingDescriptor(
                    binding_key="actor.home",
                    section_key="actor_home",
                    projection_observable_id=projection_observable_id,
                    projection_experience_graph_identity_id=graph_identity_object_id,
                    object_projection_graph_identity_id=(
                        object_projection_graph_identity_id
                    ),
                    view_ref="aware_control_identity.actor.home.v1",
                    graph_identity_ref="identity.actor",
                ),
                projection_observable_id=projection_observable_id,
                graph_identity_object_id=graph_identity_object_id,
                object_projection_graph_identity_id=object_projection_graph_identity_id,
                projection_experience_id=projection_experience_id,
                projection_experience_view_id=projection_experience_view_id,
                section_graph_binding_id=section_graph_binding_id,
            ),
        ),
    )
    captured: dict[str, object] = {}

    committed_session = type(
        "_Session",
        (),
        {
            "imap_all_objects": lambda _self: [
                ProjectionExperience.model_construct(
                    id=projection_experience_id,
                    object_projection_graph_identity_id=object_projection_graph_identity_id,
                    name="aware_control_identity",
                ),
                ApiView.model_construct(
                    id=api_view_id,
                    object_projection_graph_observable_id=projection_observable_id,
                    state_model_id=uuid4(),
                    name="actor.home.v1",
                    view_ref="aware_control_identity.actor.home.v1",
                ),
                ProjectionExperienceView.model_construct(
                    id=projection_experience_view_id,
                    projection_experience_id=projection_experience_id,
                    api_view_id=api_view_id,
                    name="actor.home.v1",
                ),
                ProjectionExperienceViewInstance.model_construct(
                    id=projection_experience_view_instance_id,
                    projection_experience_view_id=projection_experience_view_id,
                    section_graph_binding_id=section_graph_binding_id,
                    view_instance_key="actor-home.section-instance",
                    status="active",
                ),
                ProjectionExperienceSection.model_construct(
                    id=projection_experience_section_id,
                    projection_experience_id=projection_experience_id,
                    section_id=section_id,
                    section_key="actor_home",
                ),
                ProjectionExperienceSectionView.model_construct(
                    id=projection_experience_section_view_id,
                    projection_experience_section_id=projection_experience_section_id,
                    projection_experience_view_instance_id=projection_experience_view_instance_id,
                    status="active",
                ),
                ExperienceInvocationActionConfig.model_construct(
                    id=experience_invocation_action_config_id,
                    projection_experience_id=projection_experience_id,
                    target_kind=ExperienceInvocationActionTargetKind.api,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                ),
                ApiViewCapabilityEndpoint.model_construct(
                    id=api_view_capability_endpoint_id,
                    api_view_id=api_view_id,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                    action_key="identity.admit",
                    endpoint_ref="aware.identity.admit",
                ),
                ProjectionExperienceViewInvocationActionConfig.model_construct(
                    id=view_invocation_action_config_id,
                    projection_experience_view_id=projection_experience_view_id,
                    api_view_capability_endpoint_id=api_view_capability_endpoint_id,
                    action_key="identity.admit",
                    label="Admit",
                    receipt_policy="required",
                    experience_invocation_action_config_id=(
                        experience_invocation_action_config_id
                    ),
                    experience_invocation_action_config=(
                        ExperienceInvocationActionConfig.model_construct(
                            id=experience_invocation_action_config_id,
                            projection_experience_id=projection_experience_id,
                            target_kind=ExperienceInvocationActionTargetKind.api,
                            api_capability_endpoint_id=api_capability_endpoint_id,
                        )
                    ),
                ),
            ]
        },
    )()

    async def _fake_resolve_catalog(*, host_context, experience_name):  # type: ignore[no-untyped-def]
        _ = host_context
        assert experience_name == "aware_control_identity"
        return catalog

    async def _fake_resolve_transition_target(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["experience_name"] == "aware_control_identity"
        assert kwargs["profile_key"] == "os.default"
        assert kwargs["transition_key"] == "identity_admission.actor_home"
        assert kwargs["event_type"] == "identity.admitted"
        return section_graph_binding_service._ViewEventTransitionTargetResolution(
            transition_key="identity_admission.actor_home",
            source_view_ref="aware_control_identity.identity.admission.v1",
            event_type="identity.admitted",
            action_type=None,
            target_view_ref="aware_control_identity.actor.home.v1",
            target_binding_key="actor.home",
            target_section_key="actor_home",
            target_graph_identity_ref="identity.actor",
            rationale=None,
            focus_scope_title="Actor home",
        )

    async def _fake_activate_attention_section_observable(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return type(
            "_AttentionSnapshot",
            (),
            {
                "section_id": section_id,
                "section_key": kwargs["section_key"],
                "exists": True,
                "focus_scope_id": uuid4(),
                "focus_id": uuid4(),
                "observable_id": kwargs["observable_id"],
            },
        )()

    async def _fake_hydrate_experience_reference_session(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["experience_name"] == "aware_control_identity"
        return committed_session

    monkeypatch.setattr(
        section_graph_binding_service, "_resolve_catalog", _fake_resolve_catalog
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "_resolve_view_event_transition_target",
        _fake_resolve_transition_target,
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "_activate_attention_section_observable",
        _fake_activate_attention_section_observable,
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "hydrate_experience_reference_session",
        _fake_hydrate_experience_reference_session,
    )

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience",
    ) as host_context:
        response = await section_graph_binding_service.apply_view_event_transition(
            request=ApplyExperienceViewEventTransitionRequest(
                request_id=uuid4(),
                experience_name="aware_control_identity",
                profile_key="os.default",
                transition_key="identity_admission.actor_home",
                source_view_ref="aware_control_identity.identity.admission.v1",
                event_type="identity.admitted",
                action_type="experience.focus.actor_home",
            ),
            host_context=host_context,
        )

    assert captured["section_key"] == "actor_home"
    assert captured["observable_id"] == projection_observable_id
    assert (
        captured["rationale"]
        == "experience_view_event_transition:identity_admission.actor_home:identity.admitted"
    )
    assert response.catalog_revision == "catalog-rev-actor-home"
    assert response.receipt.transition_key == "identity_admission.actor_home"
    assert (
        response.receipt.trigger.source_view_ref
        == "aware_control_identity.identity.admission.v1"
    )
    assert response.receipt.trigger.event_type == "identity.admitted"
    assert response.receipt.trigger.action_type == "experience.focus.actor_home"
    assert response.receipt.target.target_binding_key == "actor.home"
    assert response.receipt.target.target_view_ref == (
        "aware_control_identity.actor.home.v1"
    )
    assert response.state.is_active is True
    assert response.state.section_view is not None
    assert (
        response.state.section_view.projection_experience_section_view_id
        == projection_experience_section_view_id
    )
    assert (
        response.state.section_view.projection_experience_view_instance_id
        == projection_experience_view_instance_id
    )
    assert (
        response.state.section_view.view_instance_key == "actor-home.section-instance"
    )
    assert (
        response.state.section_view.actions[0].action_id
        == view_invocation_action_config_id
    )
    assert (
        response.state.section_view.actions[0].view_invocation_action_config_id
        == view_invocation_action_config_id
    )
    assert (
        response.state.section_view.actions[0].experience_invocation_action_config_id
        == experience_invocation_action_config_id
    )
    assert response.state.section_view.actions[0].action_key == "identity.admit"
    assert response.state.section_view.actions[0].target_kind == "api"
    assert (
        response.state.section_view.actions[0].api_capability_endpoint_id
        == api_capability_endpoint_id
    )
    assert response.state.section_view.actions[0].endpoint_ref == "aware.identity.admit"
    assert response.receipt.target.section_view == response.state.section_view
    assert str(projection_experience_section_view_id) in (response.receipt.info or "")


@pytest.mark.asyncio
async def test_record_experience_view_invocation_action_invokes_view_instance_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection_experience_id = uuid4()
    projection_experience_view_id = uuid4()
    api_view_id = uuid4()
    projection_experience_view_instance_id = uuid4()
    view_invocation_action_config_id = uuid4()
    experience_invocation_action_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    api_view_capability_endpoint_id = uuid4()
    invocation_key = uuid4()
    actor_id = uuid4()
    api_call_id = uuid4()
    function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "projection-experience-hash"
    commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    captured: dict[str, object] = {}

    class _GraphGateway:
        async def resolve_graph_context(self) -> object:
            return runtime_index

        async def invoke_function(self, *, request, graph_context=None):  # type: ignore[no-untyped-def]
            captured["request"] = request
            captured["runtime_index"] = runtime_index
            return InvokeFunctionResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="succeeded",
                root_object_id=request.object_id,
                payload={},
                commit_id=commit_id,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )

    runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(
                    name="ProjectionExperience",
                    projection_hash=projection_hash,
                ),
                SimpleNamespace(
                    name="ExperienceInvocationActionConfig",
                    projection_hash="experience-invocation-action-config-hash",
                ),
                SimpleNamespace(
                    name="ProjectionExperienceGraph",
                    projection_hash="projection-experience-graph-hash",
                ),
                SimpleNamespace(
                    name="ProjectionExperienceSectionGraphBinding",
                    projection_hash="projection-experience-section-graph-binding-hash",
                ),
                SimpleNamespace(
                    name="ExperienceInvocationAction",
                    projection_hash="experience-invocation-action-hash",
                ),
            ]
        ),
        class_configs_by_id={
            uuid4(): SimpleNamespace(
                name="ProjectionExperienceViewInstance",
                class_fqn=(
                    "aware_experience_ontology.projection."
                    "projection_experience_view_instance.ProjectionExperienceViewInstance"
                ),
                class_config_function_configs=[
                    SimpleNamespace(
                        function_config=SimpleNamespace(
                            id=function_id,
                            name="record_action_invocation",
                        )
                    )
                ],
            )
        },
        opg_by_hash={},
        attribute_configs_by_id={},
    )
    committed_session = SimpleNamespace(
        imap_all_objects=lambda: [
            ProjectionExperience.model_construct(
                id=projection_experience_id,
                object_projection_graph_identity_id=uuid4(),
                name="aware_control_identity",
            ),
            ApiView.model_construct(
                id=api_view_id,
                object_projection_graph_observable_id=uuid4(),
                state_model_id=uuid4(),
                name="actor.home.v1",
                view_ref="aware_control_identity.actor.home.v1",
            ),
            ProjectionExperienceView.model_construct(
                id=projection_experience_view_id,
                projection_experience_id=projection_experience_id,
                api_view_id=api_view_id,
                name="actor.home.v1",
            ),
            ProjectionExperienceViewInstance.model_construct(
                id=projection_experience_view_instance_id,
                projection_experience_view_id=projection_experience_view_id,
                section_graph_binding_id=uuid4(),
                view_instance_key="actor-home.section-instance",
                status="active",
            ),
            ExperienceInvocationActionConfig.model_construct(
                id=experience_invocation_action_config_id,
                projection_experience_id=projection_experience_id,
                target_kind=ExperienceInvocationActionTargetKind.api,
                api_capability_endpoint_id=api_capability_endpoint_id,
            ),
            ApiViewCapabilityEndpoint.model_construct(
                id=api_view_capability_endpoint_id,
                api_view_id=api_view_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                action_key="identity.admit",
                endpoint_ref="aware.identity.admit",
            ),
            ProjectionExperienceViewInvocationActionConfig.model_construct(
                id=view_invocation_action_config_id,
                projection_experience_view_id=projection_experience_view_id,
                api_view_capability_endpoint_id=api_view_capability_endpoint_id,
                action_key="identity.admit",
                experience_invocation_action_config_id=(
                    experience_invocation_action_config_id
                ),
            ),
        ]
    )

    async def _fake_hydrate_session(*, runtime_context):  # type: ignore[no-untyped-def]
        assert runtime_context.branch_id == branch_id
        return committed_session

    monkeypatch.setattr(
        section_graph_binding_service,
        "_hydrate_section_graph_binding_session",
        _fake_hydrate_session,
    )

    operation_context = _service_context()
    with service_api_host_context(
        operation_context=operation_context,
        environment_context=_environment_context(operation_context),
        graph_gateway=_GraphGateway(),
        service_name="aware_experience",
        experience_reference_branch_ids_by_experience_name={
            "aware_control_identity": branch_id,
        },
    ) as host_context:
        response = await section_graph_binding_service.record_experience_view_invocation_action(
            request=RecordExperienceViewInvocationActionRequest(
                request_id=uuid4(),
                experience_name="aware_control_identity",
                projection_experience_view_instance_id=(
                    projection_experience_view_instance_id
                ),
                view_invocation_action_config_id=view_invocation_action_config_id,
                invocation_key=invocation_key,
                actor_id=actor_id,
                api_call_id=api_call_id,
                request_ref=" request:identity.admit ",
                status=" succeeded ",
            ),
            host_context=host_context,
        )

    invoke_request = cast(Any, captured["request"])
    assert invoke_request.branch_id == branch_id
    assert invoke_request.projection_hash == projection_hash
    assert invoke_request.object_id == projection_experience_view_instance_id
    assert invoke_request.function_id == function_id
    assert invoke_request.kwargs["view_invocation_action_config_id"] == str(
        view_invocation_action_config_id
    )
    assert invoke_request.kwargs["invocation_key"] == str(invocation_key)
    assert invoke_request.kwargs["status"] == "succeeded"
    assert response.receipt.experience_invocation_action_config_id == (
        experience_invocation_action_config_id
    )
    expected_experience_invocation_action_id = stable_experience_invocation_action_id(
        experience_invocation_action_config_id=(
            experience_invocation_action_config_id
        ),
        invocation_key=invocation_key,
    )
    assert response.receipt.experience_invocation_action_id == (
        expected_experience_invocation_action_id
    )
    assert response.receipt.projection_experience_view_invocation_action_id == (
        stable_projection_experience_view_invocation_action_id(
            view_invocation_action_config_id=view_invocation_action_config_id,
            experience_invocation_action_id=expected_experience_invocation_action_id,
        )
    )
    assert response.receipt.object_instance_graph_commit_id == (
        object_instance_graph_commit_id
    )
    assert response.receipt.commit_id == commit_id


@pytest.mark.asyncio
async def test_invoke_experience_view_invocation_action_dispatches_api_and_records_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection_experience_id = uuid4()
    projection_experience_view_id = uuid4()
    api_view_id = uuid4()
    projection_experience_view_instance_id = uuid4()
    view_invocation_action_config_id = uuid4()
    experience_invocation_action_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    api_view_capability_endpoint_id = uuid4()
    invocation_key = uuid4()
    actor_id = uuid4()
    role_config_id = uuid4()
    other_role_config_id = uuid4()
    actor_role_id = uuid4()
    class_instance_identity_id = uuid4()
    api_call_id = uuid4()
    function_id = uuid4()
    add_commit_function_id = uuid4()
    branch_id = uuid4()
    projection_hash = "projection-experience-hash"
    action_projection_hash = "experience-invocation-action-hash"
    commit_id = uuid4()
    object_instance_graph_commit_id = uuid4()
    service_operation_commit_id = uuid4()
    api_call_outcome_commit_id = uuid4()
    captured: dict[str, object] = {}

    class _GraphGateway:
        async def resolve_graph_context(self) -> object:
            return runtime_index

        async def invoke_function(self, *, request, graph_context=None):  # type: ignore[no-untyped-def]
            captured.setdefault("function_requests", []).append(request)
            captured["runtime_index"] = runtime_index
            return InvokeFunctionResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="succeeded",
                root_object_id=request.object_id,
                payload={},
                commit_id=commit_id,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )

    class _FakeApiInvoker:
        async def invoke_api_endpoint_raw(self, **kwargs):  # type: ignore[no-untyped-def]
            captured["api_invocation"] = kwargs
            return SimpleNamespace(
                status="succeeded",
                error=None,
                response_payload={"admitted": True, "actor_id": str(actor_id)},
                receipt={
                    "endpoint_ref": "identity.signup_via_profile.signup_via_profile",
                    "discriminant": ("identity.signup_via_profile.signup_via_profile"),
                    "status": "succeeded",
                    "api_call_id": api_call_id,
                    "api_capability_endpoint_id": api_capability_endpoint_id,
                    "call_key": uuid4(),
                    "service_operation_commit_id": service_operation_commit_id,
                    "service_operation_head_commit_id": service_operation_commit_id,
                    "api_call_outcome_commit_id": api_call_outcome_commit_id,
                    "api_call_outcome_head_commit_id": api_call_outcome_commit_id,
                },
            )

    runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(
                    name="ProjectionExperience",
                    projection_hash=projection_hash,
                ),
                SimpleNamespace(
                    name="ExperienceInvocationActionConfig",
                    projection_hash="experience-invocation-action-config-hash",
                ),
                SimpleNamespace(
                    name="ProjectionExperienceGraph",
                    projection_hash="projection-experience-graph-hash",
                ),
                SimpleNamespace(
                    name="ProjectionExperienceSectionGraphBinding",
                    projection_hash="projection-experience-section-graph-binding-hash",
                ),
                SimpleNamespace(
                    name="ExperienceInvocationAction",
                    projection_hash=action_projection_hash,
                ),
            ]
        ),
        class_configs_by_id={
            uuid4(): SimpleNamespace(
                name="ProjectionExperienceViewInstance",
                class_fqn=(
                    "aware_experience_ontology.projection."
                    "projection_experience_view_instance.ProjectionExperienceViewInstance"
                ),
                class_config_function_configs=[
                    SimpleNamespace(
                        function_config=SimpleNamespace(
                            id=function_id,
                            name="record_action_invocation",
                        )
                    )
                ],
            ),
            uuid4(): SimpleNamespace(
                name="ExperienceInvocationAction",
                class_fqn=(
                    "aware_experience_ontology.invocation."
                    "experience_invocation_action.ExperienceInvocationAction"
                ),
                class_config_function_configs=[
                    SimpleNamespace(
                        function_config=SimpleNamespace(
                            id=add_commit_function_id,
                            name="add_commit",
                        )
                    )
                ],
            ),
        },
        opg_by_hash={},
        attribute_configs_by_id={},
    )
    committed_session = SimpleNamespace(
        imap_all_objects=lambda: [
            ProjectionExperience.model_construct(
                id=projection_experience_id,
                object_projection_graph_identity_id=uuid4(),
                name="aware_control_identity",
            ),
            ApiView.model_construct(
                id=api_view_id,
                object_projection_graph_observable_id=uuid4(),
                state_model_id=uuid4(),
                name="identity.admission.v1",
                view_ref="aware_control_identity.identity.admission.v1",
            ),
            ProjectionExperienceView.model_construct(
                id=projection_experience_view_id,
                projection_experience_id=projection_experience_id,
                api_view_id=api_view_id,
                name="identity.admission.v1",
            ),
            ProjectionExperienceViewInstance.model_construct(
                id=projection_experience_view_instance_id,
                projection_experience_view_id=projection_experience_view_id,
                section_graph_binding_id=uuid4(),
                view_instance_key="identity-admission.section-instance",
                status="active",
            ),
            ExperienceInvocationActionConfig.model_construct(
                id=experience_invocation_action_config_id,
                projection_experience_id=projection_experience_id,
                target_kind=ExperienceInvocationActionTargetKind.api,
                api_capability_endpoint_id=api_capability_endpoint_id,
            ),
            ApiViewCapabilityEndpoint.model_construct(
                id=api_view_capability_endpoint_id,
                api_view_id=api_view_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                action_key="identity.signup",
                endpoint_ref="identity.signup_via_profile.signup_via_profile",
            ),
            ProjectionExperienceViewInvocationActionConfig.model_construct(
                id=view_invocation_action_config_id,
                projection_experience_view_id=projection_experience_view_id,
                api_view_capability_endpoint_id=api_view_capability_endpoint_id,
                action_key="identity.signup",
                experience_invocation_action_config_id=(
                    experience_invocation_action_config_id
                ),
            ),
        ]
    )

    async def _fake_hydrate_session(*, runtime_context):  # type: ignore[no-untyped-def]
        assert runtime_context.branch_id == branch_id
        return committed_session

    def _fake_build_service_api_client_for_api_package(routes, **kwargs):  # type: ignore[no-untyped-def]
        captured["route_kwargs"] = {"routes": routes, **kwargs}
        return _FakeApiInvoker()

    monkeypatch.setattr(
        section_graph_binding_service,
        "_hydrate_section_graph_binding_session",
        _fake_hydrate_session,
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "build_service_api_client_for_api_package",
        _fake_build_service_api_client_for_api_package,
    )

    operation_context = _service_context()
    route = _service_api_route(api_package_name="identity-service-api")
    with service_api_host_context(
        operation_context=operation_context,
        environment_context=_environment_context(operation_context),
        graph_gateway=_GraphGateway(),
        service_name="aware_experience",
        service_api_dependency_routes=(route,),
        invocation_context={"surface": {"section_key": "identity_admission"}},
        experience_reference_branch_ids_by_experience_name={
            "aware_control_identity": branch_id,
        },
    ) as host_context:
        response = await section_graph_binding_service.invoke_experience_view_invocation_action(
            request=InvokeExperienceViewInvocationActionRequest(
                request_id=uuid4(),
                experience_name="aware_control_identity",
                projection_experience_view_instance_id=(
                    projection_experience_view_instance_id
                ),
                view_invocation_action_config_id=view_invocation_action_config_id,
                invocation_key=invocation_key,
                actor_id=actor_id,
                admitted_actor_role_bindings=[
                    {
                        "actor_config_role_config_id": uuid4(),
                        "role_config_id": role_config_id,
                        "role_config_name": "aware.identity.participant",
                        "actor_id": actor_id,
                        "role_id": uuid4(),
                        "actor_role_id": actor_role_id,
                        "role_class_instance_id": uuid4(),
                        "class_instance_identity_id": class_instance_identity_id,
                        "role_config_class_config_id": uuid4(),
                        "object_instance_graph_identity_id": uuid4(),
                    },
                    {
                        "actor_config_role_config_id": uuid4(),
                        "role_config_id": other_role_config_id,
                        "role_config_name": "aware.identity.observer",
                        "actor_id": actor_id,
                        "role_id": uuid4(),
                        "actor_role_id": uuid4(),
                        "role_class_instance_id": uuid4(),
                        "class_instance_identity_id": uuid4(),
                        "role_config_class_config_id": uuid4(),
                        "object_instance_graph_identity_id": uuid4(),
                    },
                ],
                admission_evidence={
                    "experience_invocation_action_admission_preflight": {
                        "accepted": True,
                        "matched_role_config_id": str(role_config_id),
                        "matched_actor_role_id": str(actor_role_id),
                    }
                },
                request_payload={"profile": {"display_name": "Luis"}},
                request_ref="interface.identity_admission.submit",
            ),
            host_context=host_context,
        )

    route_kwargs = cast(dict[str, object], captured["route_kwargs"])
    api_invocation = cast(dict[str, object], captured["api_invocation"])
    function_requests = cast(list[Any], captured["function_requests"])
    function_request = function_requests[0]
    assert route_kwargs["routes"] == (route,)
    assert route_kwargs["api_package_name"] == "identity-service-api"
    assert route_kwargs["actor_id"] == actor_id
    invocation_context = cast(dict[str, object], route_kwargs["invocation_context"])
    assert invocation_context["surface"] == {"section_key": "identity_admission"}
    assert (
        cast(dict[str, object], invocation_context["experience_invocation"])[
            "action_key"
        ]
        == "identity.signup"
    )
    service_admission = cast(
        dict[str, object],
        invocation_context["service_operation_admission_context"],
    )
    role_evidence = cast(
        list[dict[str, object]],
        service_admission["service_actor_role_evidence"],
    )
    assert len(role_evidence) == 1
    assert role_evidence[0]["role_config_id"] == str(role_config_id)
    assert role_evidence[0]["actor_id"] == str(actor_id)
    assert role_evidence[0]["class_instance_identity_id"] == str(
        class_instance_identity_id
    )
    assert role_evidence[0]["role_assignment_binding_id"] == str(actor_role_id)
    assert api_invocation["endpoint_ref"] == (
        "identity.signup_via_profile.signup_via_profile"
    )
    assert api_invocation["discriminant"] == (
        "identity.signup_via_profile.signup_via_profile"
    )
    assert api_invocation["request_payload"] == {"profile": {"display_name": "Luis"}}
    assert function_request.kwargs["api_call_id"] == str(api_call_id)
    assert function_request.kwargs["request_ref"] == (
        "interface.identity_admission.submit"
    )
    assert function_request.kwargs["receipt_ref"] == f"api_call:{api_call_id}"
    assert function_request.kwargs["status"] == "succeeded"
    assert response.success is True
    assert response.response_payload == {"admitted": True, "actor_id": str(actor_id)}
    assert response.api_dispatch_receipt is not None
    assert response.api_dispatch_receipt.api_call_id == api_call_id
    assert response.receipt.api_call_id == api_call_id
    assert response.receipt.object_instance_graph_commit_id == (
        object_instance_graph_commit_id
    )
    assert response.receipt.commit_id == commit_id
    expected_experience_invocation_action_id = stable_experience_invocation_action_id(
        experience_invocation_action_config_id=(
            experience_invocation_action_config_id
        ),
        invocation_key=invocation_key,
    )
    assert [request.function_id for request in function_requests] == [
        function_id,
        add_commit_function_id,
        add_commit_function_id,
    ]
    assert [request.object_id for request in function_requests[1:]] == [
        expected_experience_invocation_action_id,
        expected_experience_invocation_action_id,
    ]
    assert [request.projection_hash for request in function_requests[1:]] == [
        action_projection_hash,
        action_projection_hash,
    ]
    assert [
        request.kwargs["object_instance_graph_commit_id"]
        for request in function_requests[1:]
    ] == [
        str(service_operation_commit_id),
        str(api_call_outcome_commit_id),
    ]
    assert [request.kwargs["commit_role"] for request in function_requests[1:]] == [
        "service_operation",
        "api_call_outcome",
    ]


@pytest.mark.asyncio
async def test_invocation_action_commit_evidence_attaches_real_dispatch_event_ids() -> (
    None
):
    experience_invocation_action_id = uuid4()
    service_operation_commit_id = uuid4()
    api_call_outcome_commit_id = uuid4()
    service_operation_event_id = uuid4()
    service_operation_head_event_id = uuid4()
    api_call_outcome_event_id = uuid4()
    add_commit_function_id = uuid4()
    add_event_function_id = uuid4()
    action_projection_hash = "experience-invocation-action-hash"
    captured: dict[str, object] = {}

    class _GraphGateway:
        async def invoke_function(self, *, request, graph_context=None):  # type: ignore[no-untyped-def]
            captured.setdefault("function_requests", []).append(request)
            captured["runtime_index"] = runtime_index
            return InvokeFunctionResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="succeeded",
                root_object_id=request.object_id,
                payload={},
                commit_id=uuid4(),
                object_instance_graph_commit_id=uuid4(),
            )

    runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(
                    name="ExperienceInvocationAction",
                    projection_hash=action_projection_hash,
                ),
            ]
        ),
        class_configs_by_id={
            uuid4(): SimpleNamespace(
                name="ExperienceInvocationAction",
                class_fqn=(
                    "aware_experience_ontology.invocation."
                    "experience_invocation_action.ExperienceInvocationAction"
                ),
                class_config_function_configs=[
                    SimpleNamespace(
                        function_config=SimpleNamespace(
                            id=add_commit_function_id,
                            name="add_commit",
                        )
                    )
                ],
            ),
            uuid4(): SimpleNamespace(
                name="ExperienceInvocationActionCommit",
                class_fqn=(
                    "aware_experience_ontology.invocation."
                    "experience_invocation_action_commit.ExperienceInvocationActionCommit"
                ),
                class_config_function_configs=[
                    SimpleNamespace(
                        function_config=SimpleNamespace(
                            id=add_event_function_id,
                            name="add_event",
                        )
                    )
                ],
            ),
        },
    )
    operation_context = _service_context()
    with service_api_host_context(
        operation_context=operation_context,
        environment_context=_environment_context(operation_context),
        graph_gateway=_GraphGateway(),
        service_name="aware_experience",
    ) as host_context:
        runtime_context = (
            section_graph_binding_service._SectionGraphBindingRuntimeContext(
                host_context=host_context,
                graph_gateway=cast(Any, host_context.graph_gateway),
                runtime_index=cast(Any, runtime_index),
                branch_id=operation_context.branch_id,
                projection_hashes=(action_projection_hash,),
            )
        )
        receipt = SimpleNamespace(
            service_operation_commit_id=service_operation_commit_id,
            service_operation_head_commit_id=service_operation_commit_id,
            service_operation_event_ids=(
                service_operation_event_id,
                service_operation_event_id,
            ),
            service_operation_head_event_ids=(service_operation_head_event_id,),
            api_call_outcome_commit_id=api_call_outcome_commit_id,
            api_call_outcome_head_commit_id=api_call_outcome_commit_id,
            api_call_outcome_event_ids=(api_call_outcome_event_id,),
            api_call_outcome_head_event_ids=(api_call_outcome_event_id,),
        )

        await section_graph_binding_service._attach_invocation_action_commit_evidence(
            runtime_context=runtime_context,
            experience_invocation_action_id=experience_invocation_action_id,
            commit_evidence=(
                section_graph_binding_service._api_dispatch_commit_evidence(
                    receipt=cast(Any, receipt),
                )
            ),
            actor_id=operation_context.actor_id,
        )

    service_operation_action_commit_id = stable_experience_invocation_action_commit_id(
        experience_invocation_action_id=experience_invocation_action_id,
        object_instance_graph_commit_id=service_operation_commit_id,
    )
    api_call_outcome_action_commit_id = stable_experience_invocation_action_commit_id(
        experience_invocation_action_id=experience_invocation_action_id,
        object_instance_graph_commit_id=api_call_outcome_commit_id,
    )
    function_requests = cast(list[Any], captured["function_requests"])
    assert [request.function_id for request in function_requests] == [
        add_commit_function_id,
        add_event_function_id,
        add_event_function_id,
        add_commit_function_id,
        add_event_function_id,
    ]
    assert [request.object_id for request in function_requests] == [
        experience_invocation_action_id,
        service_operation_action_commit_id,
        service_operation_action_commit_id,
        experience_invocation_action_id,
        api_call_outcome_action_commit_id,
    ]
    assert [request.projection_hash for request in function_requests] == [
        action_projection_hash,
        action_projection_hash,
        action_projection_hash,
        action_projection_hash,
        action_projection_hash,
    ]
    assert [
        request.kwargs["object_instance_graph_commit_id"]
        for request in function_requests
        if request.function_id == add_commit_function_id
    ] == [
        str(service_operation_commit_id),
        str(api_call_outcome_commit_id),
    ]
    assert [
        request.kwargs["event_id"]
        for request in function_requests
        if request.function_id == add_event_function_id
    ] == [
        str(service_operation_event_id),
        str(service_operation_head_event_id),
        str(api_call_outcome_event_id),
    ]


@pytest.mark.asyncio
async def test_apply_view_event_transition_rejects_target_view_hint_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = ExperienceSectionGraphBindingDescriptor(
        binding_key="actor.home",
        section_key="actor_home",
        projection_observable_id=uuid4(),
        projection_experience_graph_identity_id=uuid4(),
        object_projection_graph_identity_id=uuid4(),
        view_ref="aware_control_identity.actor.home.v1",
        graph_identity_ref="identity.actor",
    )
    catalog = ExperienceSectionGraphBindingCatalog(
        experience_name="aware_control_identity",
        catalog_revision="catalog-rev-actor-home",
        entries=(
            ExperienceSectionGraphBindingCatalogEntry(
                descriptor=descriptor,
                projection_observable_id=descriptor.projection_observable_id,
                graph_identity_object_id=(
                    descriptor.projection_experience_graph_identity_id
                ),
                object_projection_graph_identity_id=(
                    descriptor.object_projection_graph_identity_id
                ),
            ),
        ),
    )
    activated = False

    async def _fake_resolve_catalog(*, host_context, experience_name):  # type: ignore[no-untyped-def]
        _ = host_context, experience_name
        return catalog

    async def _fake_resolve_transition_target(**kwargs):  # type: ignore[no-untyped-def]
        _ = kwargs
        return section_graph_binding_service._ViewEventTransitionTargetResolution(
            transition_key="identity_admission.actor_home",
            source_view_ref="aware_control_identity.identity.admission.v1",
            event_type="identity.admitted",
            action_type=None,
            target_view_ref="aware_control_identity.actor.home.v1",
            target_binding_key="actor.home",
            target_section_key="actor_home",
            target_graph_identity_ref="identity.actor",
            rationale=None,
            focus_scope_title=None,
        )

    async def _fake_activate_attention_section_observable(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal activated
        activated = True
        return object()

    monkeypatch.setattr(
        section_graph_binding_service, "_resolve_catalog", _fake_resolve_catalog
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "_resolve_view_event_transition_target",
        _fake_resolve_transition_target,
    )
    monkeypatch.setattr(
        section_graph_binding_service,
        "_activate_attention_section_observable",
        _fake_activate_attention_section_observable,
    )

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience",
    ) as host_context:
        with pytest.raises(ValueError, match="target_view_ref"):
            await section_graph_binding_service.apply_view_event_transition(
                request=ApplyExperienceViewEventTransitionRequest(
                    request_id=uuid4(),
                    experience_name="aware_control_identity",
                    transition_key="identity_admission.actor_home",
                    event_type="identity.admitted",
                    target_view_ref="aware_control_identity.identity.admission.v1",
                ),
                host_context=host_context,
            )

    assert activated is False


@pytest.mark.asyncio
async def test_activate_attention_section_observable_uses_attention_service_api_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observable_id = uuid4()
    captured: dict[str, object] = {}

    def _fake_build_api_client(routes, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["routes"] = routes
        captured["route_kwargs"] = kwargs
        return object()

    class _FakeActivateCapability:
        async def activate_section_observable(self, request):  # type: ignore[no-untyped-def]
            captured["request"] = request
            return type(
                "_Response",
                (),
                {
                    "snapshot": type(
                        "_Snapshot",
                        (),
                        {
                            "exists": True,
                            "focus_scope_id": uuid4(),
                            "focus_id": uuid4(),
                            "observable_id": request.observable_id,
                        },
                    )()
                },
            )()

    class _FakeAttentionApi:
        activate_section_observable = _FakeActivateCapability()

    class _FakeAttentionServiceApiClient:
        def __init__(self, invoker):  # type: ignore[no-untyped-def]
            captured["invoker"] = invoker
            self.attention = _FakeAttentionApi()

    import aware_attention_service_api

    monkeypatch.setattr(
        section_graph_binding_service,
        "build_service_api_client_for_api_package",
        _fake_build_api_client,
    )
    monkeypatch.setattr(
        aware_attention_service_api,
        "AwareAttentionServiceApiClient",
        _FakeAttentionServiceApiClient,
    )
    invocation_context = {"surface": {"section_key": "coordination.primary"}}

    with service_api_host_context(
        operation_context=_service_context(),
        graph_gateway=None,
        service_name="aware_experience",
        service_api_dependency_routes=(
            _service_api_route(api_package_name="attention-service-api"),
        ),
        invocation_context=invocation_context,
    ) as host_context:
        snapshot = await section_graph_binding_service._activate_attention_section_observable(  # noqa: SLF001
            host_context=host_context,
            section_key="coordination.primary",
            observable_id=observable_id,
            activation_scope=None,
            rationale="test",
            section_title="Coordination",
            section_description=None,
            focus_scope_title="Primary",
            focus_scope_description=None,
        )

    route_kwargs = captured["route_kwargs"]
    assert route_kwargs["api_package_name"] == "attention-service-api"
    assert route_kwargs["invocation_context"] == invocation_context
    request = captured["request"]
    assert request.section_key == "coordination.primary"
    assert request.observable_id == observable_id
    assert request.rationale == "test"
    assert getattr(snapshot, "observable_id") == observable_id
