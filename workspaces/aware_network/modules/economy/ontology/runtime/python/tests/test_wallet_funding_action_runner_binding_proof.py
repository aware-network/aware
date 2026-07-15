from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_api_runtime.invocation import ApiInvocationIR, MaterializedApiCallBinding
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_response_config import (
    ApiCapabilityEndpointResponseConfig,
)
from aware_economy_providers.external_capital import (
    EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY,
    WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME,
)
from aware_experience.action_dispatch.bridge import dispatch_requested_action_intent
from aware_experience.compiler.compile import compile_experience_workspace
from aware_experience.environment.compiler import (
    load_environment_ownership_from_sources,
)
from aware_experience.event.compiler import load_event_ownership_from_sources
from aware_experience.materialization.compile_plan_payloads import (
    _build_source_experience_compile_plan_payload,
)
from aware_experience.materialization.service import (
    resolve_connector_config_materialization_specs,
)
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.action.action_experience_invocation import (
    ActionExperienceInvocation,
)
from aware_experience_ontology.action.action_experience_invocation_request_field import (
    ActionExperienceInvocationRequestField,
)
from aware_experience_ontology.environment.environment_experience_event import (
    EnvironmentExperienceEvent,
)
from aware_experience_ontology.environment.environment_experience_event_action import (
    EnvironmentExperienceEventAction,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_reactivity_ontology.action.action_config import ActionConfig
from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
    ActionIntentStatus,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
    ReactivityActionLifecyclePublishResponse,
)


_REQUEST_SOURCE_REFS: tuple[tuple[str, str], ...] = (
    ("transaction_intent_id", "commit.branch_id"),
    ("transaction_intent_commit_id", "commit.commit_id"),
)


class _ReactivityLifecycleSdk:
    def __init__(self) -> None:
        self.requests: list[ReactivityActionLifecyclePublishRequest] = []
        self.feedback_id = uuid4()

    async def publish_action_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse:
        self.requests.append(request)
        action_execution_id = None
        if request.execution is not None:
            action_execution_id = request.execution.action_execution_id
        if request.terminal is not None:
            action_execution_id = request.terminal.action_execution_id
        return ReactivityActionLifecyclePublishResponse(
            request_id=request.request_id,
            accepted=True,
            published_count=1,
            action_execution_id=action_execution_id,
            action_feedback_id=(self.feedback_id if request.feedback is not None else None),
        )


def _primitive_attribute(*, owner_key: str, name: str) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    return AttributeConfig(
        owner_key=owner_key,
        name=name,
        is_required=True,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _request_class() -> tuple[ClassConfig, dict[str, AttributeConfig]]:
    class_config = ClassConfig(
        name="ExternalCapitalWalletFundingSessionRequest",
        class_fqn=(
            "aware_external_capital_provider_service_dto.external_capital." "ExternalCapitalWalletFundingSessionRequest"
        ),
        value_mode=ClassValueMode.inline_value,
    )
    attributes: dict[str, AttributeConfig] = {}
    for position, (name, _) in enumerate(_REQUEST_SOURCE_REFS):
        attribute = _primitive_attribute(owner_key=class_config.class_fqn, name=name)
        attributes[name] = attribute
        class_config.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                class_config_id=class_config.id,
                attribute_config=attribute,
                attribute_config_id=attribute.id,
                position=position,
            )
        )
    return class_config, attributes


def _profile_with_external_capital_action(
    *,
    action_config_id: UUID,
    endpoint_id: UUID,
    request_class: ClassConfig,
    attributes: dict[str, AttributeConfig],
) -> EnvironmentExperienceProfileConfig:
    profile_id = uuid4()
    environment_event_id = uuid4()
    action_experience_id = uuid4()
    invocation_config_id = uuid4()
    invocation_id = uuid4()
    request_config = ApiCapabilityEndpointRequestConfig(
        id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        class_config_id=request_class.id,
        class_config=request_class,
        response_config=ApiCapabilityEndpointResponseConfig(
            id=uuid4(),
            api_capability_endpoint_request_config_id=uuid4(),
            class_config_id=uuid4(),
        ),
    )
    endpoint = ApiCapabilityEndpoint(
        id=endpoint_id,
        api_capability_id=uuid4(),
        name="create_wallet_funding_session",
        request_config=request_config,
    )
    invocation_config = ExperienceInvocationActionConfig(
        id=invocation_config_id,
        projection_experience_id=uuid4(),
        target_kind=ExperienceInvocationActionTargetKind.api,
        api_capability_endpoint_id=endpoint_id,
        api_capability_endpoint=endpoint,
    )
    action_experience = ActionExperience(
        id=action_experience_id,
        action_config_id=action_config_id,
        action_config=ActionConfig(
            id=action_config_id,
            api_capability_endpoint_id=endpoint_id,
            name=EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY,
            action_type=EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY,
            description="Create an external wallet funding provider session.",
        ),
        action_experience_invocations=[
            ActionExperienceInvocation(
                id=invocation_id,
                action_experience_id=action_experience_id,
                experience_invocation_action_config_id=invocation_config.id,
                experience_invocation_action_config=invocation_config,
                request_fields=[
                    ActionExperienceInvocationRequestField(
                        id=uuid4(),
                        action_experience_invocation_id=invocation_id,
                        attribute_config_id=attributes[field_name].id,
                        attribute_config=attributes[field_name],
                        source_ref=source_ref,
                        required=True,
                        position=position,
                    )
                    for position, (field_name, source_ref) in enumerate(_REQUEST_SOURCE_REFS)
                ],
            )
        ],
    )
    environment_event = EnvironmentExperienceEvent(
        id=environment_event_id,
        environment_experience_profile_config_id=profile_id,
        event_config_id=uuid4(),
        actions=[
            EnvironmentExperienceEventAction(
                id=uuid4(),
                environment_experience_event_id=environment_event_id,
                action_experience_id=action_experience_id,
                action_experience=action_experience,
            )
        ],
    )
    return EnvironmentExperienceProfileConfig(
        id=profile_id,
        environment_experience_id=uuid4(),
        environment_profile_config_id=uuid4(),
        key="aware_economy.external_capital",
        events=[environment_event],
    )


def _api_invocation_ir(
    *,
    endpoint_id: UUID,
    request_class_config_id: UUID,
) -> ApiInvocationIR:
    return ApiInvocationIR(
        api_name="external_capital",
        capability_name="wallet_funding_session",
        endpoint_name="create_wallet_funding_session",
        endpoint_ref=("external_capital.wallet_funding_session.create_wallet_funding_session"),
        discriminant=("external_capital.wallet_funding_session.create_wallet_funding_session"),
        source_path="economy-action-runner-proof",
        request_payload={},
        request_class_ref=(
            "aware_external_capital_provider_service_dto.external_capital." "ExternalCapitalWalletFundingSessionRequest"
        ),
        request_class_config_id=request_class_config_id,
        request_source_path="economy-action-runner-proof",
        response_class_ref=(
            "aware_external_capital_provider_service_dto.external_capital."
            "ExternalCapitalWalletFundingSessionResponse"
        ),
        response_source_path="economy-action-runner-proof",
        stream=None,
        fulfillment_bindings=(),
        description="Create a provider wallet funding session.",
        api_capability_endpoint_id=endpoint_id,
    )


def test_aware_economy_experience_declares_value_free_external_capital_target() -> None:
    repo_root = _repo_root()
    experience_root = repo_root / "workspaces/aware_network/modules/economy/experiences/aware_economy"
    compile_result = compile_experience_workspace(
        toml_path=experience_root / "aware.experience.toml",
        repo_root=repo_root,
    )
    payload = _build_source_experience_compile_plan_payload(
        snapshot=compile_result.snapshot,
    )
    event_ownership = load_event_ownership_from_sources(
        package_root=compile_result.snapshot.package_root,
        source_files=compile_result.snapshot.source_files,
    )
    environment_ownership = load_environment_ownership_from_sources(
        package_root=compile_result.snapshot.package_root,
        source_files=compile_result.snapshot.source_files,
    )

    event = next(item for item in event_ownership if item.symbol == "WalletFundingIntentPrepared")
    assert event.event_name == WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME
    assert [
        (binding.projection, binding.type_ref, binding.operation, binding.attribute) for binding in event.bindings
    ] == [
        (
            "TransactionIntent",
            "TransactionIntent.TransactionIntent",
            "create",
            None,
        )
    ]
    environment = next(item for item in environment_ownership if item.name == "aware_economy_external_capital")
    assert [
        (
            item.event,
            tuple(action.action for action in item.actions),
            tuple(scope.node_ref for scope in item.node_scopes),
        )
        for item in environment.events
    ] == [
        (
            "WalletFundingIntentPrepared",
            ("ExternalCapitalCreateWalletFundingSession",),
            (),
        )
    ]

    connector_specs = resolve_connector_config_materialization_specs(compile_plan_payloads=(payload,))
    connector = next(spec for spec in connector_specs if spec.connector_key == "external_capital")
    assert connector.connector_kind == "economy_external_capital_provider"
    assert connector.projection_experience_name == "aware_economy"
    assert connector.projection_key == "Wallet"
    assert len(connector.actuator_configs) == 1
    invocation = connector.actuator_configs[0].invocation_action_configs[0]
    assert invocation.target_ref == ("external_capital.wallet_funding_session.create_wallet_funding_session")
    assert [(field.attribute, field.source_ref) for field in invocation.request_fields] == list(_REQUEST_SOURCE_REFS)
    assert "action_payload" not in str(invocation.request_fields)


@pytest.mark.asyncio
async def test_action_runner_composes_only_transaction_intent_commit_refs() -> None:
    request_class, attributes = _request_class()
    endpoint_id = uuid4()
    action_config_id = uuid4()
    profile = _profile_with_external_capital_action(
        action_config_id=action_config_id,
        endpoint_id=endpoint_id,
        request_class=request_class,
        attributes=attributes,
    )
    transaction_intent_id = uuid4()
    transaction_intent_commit_id = uuid4()
    intent = ReactivityActionIntent(
        action_intent_id=uuid4(),
        intent_key=f"wallet-funding:{transaction_intent_id}",
        event_id=uuid4(),
        event_type=WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME,
        source="economy.wallet_funding",
        branch_id=transaction_intent_id,
        projection_hash="sha256:economy-wallet-funding-intent",
        commit_id=transaction_intent_commit_id,
        event_config_condition_config_scope_id=uuid4(),
        event_config_condition_config_id=uuid4(),
        event_config_action_config_id=uuid4(),
        action_config_id=action_config_id,
        action_type=EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY,
        status=ActionIntentStatus.requested,
        root_object_id=transaction_intent_id,
        object_instance_graph_id=uuid4(),
        graph_hash_post="sha256:wallet-funding-intent-graph",
    )
    reactivity = _ReactivityLifecycleSdk()
    captured_payloads: list[dict[str, object]] = []

    async def _provider_service_dispatcher(**kwargs: Any) -> object:
        ir = cast(ApiInvocationIR, kwargs["ir"])
        captured_payloads.append(dict(ir.request_payload))
        binding = MaterializedApiCallBinding(
            api_call_id=uuid4(),
            api_capability_endpoint_id=endpoint_id,
            call_key=kwargs["call_key"],
            request_hash="sha256:external-capital-action-runner",
            request_model_id=uuid4(),
            request_class_config_id=request_class.id,
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            branch_id=transaction_intent_id,
            projection_hash="sha256:external-capital-provider-session",
        )
        return SimpleNamespace(materialized_call=SimpleNamespace(binding=binding))

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_api_invocation_ir(
            endpoint_id=endpoint_id,
            request_class_config_id=request_class.id,
        ),
        api_dispatcher=_provider_service_dispatcher,
    )

    assert result.status == "dispatched"
    assert result.api_call is not None
    assert result.execution_start is not None
    assert len(reactivity.requests) == 2
    assert captured_payloads == [
        {
            "transaction_intent_id": transaction_intent_id,
            "transaction_intent_commit_id": transaction_intent_commit_id,
        }
    ]
    assert "action_payload" not in str(captured_payloads)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "workspaces/aware_network").exists():
            return parent
    raise RuntimeError("Could not resolve repo root for Economy Experience proof")
