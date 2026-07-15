from __future__ import annotations

from uuid import UUID, uuid5, NAMESPACE_URL

import pytest

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
from aware_experience.handlers.impl.action import (
    action_experience as action_experience_handler,
)
from aware_experience.handlers.impl.action import (
    action_experience_invocation as action_experience_invocation_handler,
)
from aware_experience.stable_ids import (
    stable_action_experience_id,
    stable_action_experience_invocation_id,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta_ontology.class_.class_config import ClassConfig


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


def _install_sessions(monkeypatch: pytest.MonkeyPatch, session: _Session) -> None:
    for module in (
        action_experience_handler,
        action_experience_invocation_handler,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)


def _install_direct_constructors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        action_experience_handler.ActionExperienceInvocation,
        "build_via_action_experience",
        action_experience_invocation_handler.build_via_action_experience,
    )


def _class_config(ns: UUID, key: str) -> ClassConfig:
    return ClassConfig.model_construct(
        id=uuid5(ns, key),
        name=key,
        class_fqn=f"aware.tests.{key}",
    )


def _api_endpoint_with_typed_contract(ns: UUID) -> ApiCapabilityEndpoint:
    request_class = _class_config(ns, "DoorLockRequest")
    response_class = _class_config(ns, "DoorLockResult")
    feedback_class = _class_config(ns, "DoorLockFeedback")

    endpoint_id = uuid5(ns, "endpoint")
    request_config = ApiCapabilityEndpointRequestConfig.model_construct(
        id=uuid5(ns, "request_config"),
        api_capability_endpoint_id=endpoint_id,
        class_config_id=request_class.id,
        class_config=request_class,
    )
    response_config = ApiCapabilityEndpointResponseConfig.model_construct(
        id=uuid5(ns, "response_config"),
        api_capability_endpoint_request_config_id=request_config.id,
        class_config_id=response_class.id,
        class_config=response_class,
    )
    stream_event_config = ApiCapabilityEndpointStreamEventConfig.model_construct(
        id=uuid5(ns, "stream_delta_event_config"),
        api_capability_endpoint_stream_config_id=uuid5(ns, "stream_config"),
        kind=ApiCapabilityEndpointStreamEventKind.delta,
        class_config_id=feedback_class.id,
        class_config=feedback_class,
    )
    stream_config = ApiCapabilityEndpointStreamConfig.model_construct(
        id=uuid5(ns, "stream_config"),
        api_capability_endpoint_request_config_id=request_config.id,
        stream_mode=ApiCapabilityEndpointStreamMode.server,
        api_capability_endpoint_stream_event_configs=[stream_event_config],
    )
    request_config.response_config = response_config
    request_config.stream_config = stream_config

    return ApiCapabilityEndpoint.model_construct(
        id=endpoint_id,
        api_capability_id=uuid5(ns, "api_capability"),
        name="door.lock",
        request_config=request_config,
    )


@pytest.mark.asyncio
async def test_action_experience_invocation_binding_resolves_endpoint_class_configs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    _install_sessions(monkeypatch, session)
    _install_direct_constructors(monkeypatch)

    ns = uuid5(
        NAMESPACE_URL,
        "aware://tests/experience/action-experience-invocation-binding/v1",
    )
    action_config_id = uuid5(ns, "reactivity_action_config")
    action_experience = await action_experience_handler.build(
        action_config_id=action_config_id,
    )
    session.put(action_experience)

    endpoint = _api_endpoint_with_typed_contract(ns)
    invocation_config = ExperienceInvocationActionConfig.model_construct(
        id=uuid5(ns, "experience_invocation_action_config"),
        action_key="door.lock",
        action_kind="api",
        target_ref="home.devices.door.lock",
        api_capability_endpoint_id=endpoint.id,
        api_capability_endpoint=endpoint,
    )
    session.put(invocation_config)

    binding = await action_experience_handler.add_invocation_action_config(
        action_experience,
        experience_invocation_action_config_id=invocation_config.id,
    )

    assert action_experience.id == stable_action_experience_id(
        action_config_id=action_config_id,
    )
    assert binding.id == stable_action_experience_invocation_id(
        action_experience_id=action_experience.id,
        experience_invocation_action_config_id=invocation_config.id,
    )
    assert binding.action_experience_id == action_experience.id
    assert binding.experience_invocation_action_config_id == invocation_config.id
    assert binding.experience_invocation_action_config is invocation_config
    assert action_experience.action_experience_invocations == [binding]

    resolved_endpoint = (
        binding.experience_invocation_action_config.api_capability_endpoint
    )
    assert resolved_endpoint is endpoint
    assert resolved_endpoint.request_config.class_config.name == "DoorLockRequest"
    assert (
        resolved_endpoint.request_config.response_config.class_config.name
        == "DoorLockResult"
    )
    stream_events = (
        resolved_endpoint.request_config.stream_config.api_capability_endpoint_stream_event_configs
    )
    assert [event.kind for event in stream_events] == [
        ApiCapabilityEndpointStreamEventKind.delta,
    ]
    assert stream_events[0].class_config.name == "DoorLockFeedback"

    repeat = await action_experience_handler.add_invocation_action_config(
        action_experience,
        experience_invocation_action_config_id=invocation_config.id,
    )
    assert repeat is binding
    assert action_experience.action_experience_invocations == [binding]
