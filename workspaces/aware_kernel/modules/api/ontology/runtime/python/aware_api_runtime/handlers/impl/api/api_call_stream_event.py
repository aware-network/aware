from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_call_stream_event import ApiCallStreamEvent

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import inspect

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
    ApiCapabilityEndpointStreamEventConfig,
)
from aware_api_ontology.stable_ids import stable_api_call_stream_event_id
from aware_api_runtime.invocation.materialization.context import (
    current_api_call_stream_event_materialization_input,
)
from aware_meta.class_.inline_value_instance.builder import (
    build_inline_value_instance_from_mapping,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)
from aware_meta.runtime.value_resolvers import (
    default_meta_class_instance_resolver,
    default_meta_enum_option_resolver,
)
from aware_orm.registry import ORMModelRegistry
from aware_orm.session.autobind import disable_autobind


def _serialization_copy(stream_event: ApiCallStreamEvent) -> ApiCallStreamEvent:
    return ApiCallStreamEvent(
        id=stream_event.id,
        api_call_id=stream_event.api_call_id,
        api_capability_endpoint_stream_event_config_id=(stream_event.api_capability_endpoint_stream_event_config_id),
        api_capability_endpoint_stream_event_config=(stream_event.api_capability_endpoint_stream_event_config),
        event_model_id=stream_event.event_model_id,
        event_model=stream_event.event_model,
        sequence=stream_event.sequence,
        description=stream_event.description,
    )


async def _resolve_stream_event_class_config(
    *,
    stream_event_config: ApiCapabilityEndpointStreamEventConfig,
    class_config_hint: ClassConfig | None,
) -> ClassConfig:
    if class_config_hint is not None:
        if class_config_hint.id != stream_event_config.class_config_id:
            raise RuntimeError(
                "ApiCallStreamEvent.create_via_api_call received mismatched stream event "
                "ClassConfig context: "
                f"expected_class_config_id={stream_event_config.class_config_id} "
                f"got_class_config_id={class_config_hint.id}"
            )
        return class_config_hint

    class_config = stream_event_config.class_config
    if inspect.isawaitable(class_config):
        class_config = await class_config
    if class_config is None:
        class_config = current_handler_session().imap_get(
            ClassConfig,
            stream_event_config.class_config_id,
        )
    if class_config is None:
        class_config = current_handler_index().class_configs_by_id.get(stream_event_config.class_config_id)
    if class_config is None:
        orm_class = ORMModelRegistry.get_class_by_class_config_id(stream_event_config.class_config_id)
        if orm_class is not None:
            class_config = orm_class.get_class_config()
    if class_config is None or class_config.id is None:
        raise RuntimeError(
            "ApiCallStreamEvent.create_via_api_call requires stream event "
            "config.class_config to resolve before event_model construction: "
            "api_capability_endpoint_stream_event_config_id="
            f"{stream_event_config.id} "
            f"class_config_id={stream_event_config.class_config_id}"
        )
    if class_config.id != stream_event_config.class_config_id:
        raise RuntimeError(
            "ApiCallStreamEvent.create_via_api_call resolved mismatched stream event "
            "ClassConfig: "
            f"expected_class_config_id={stream_event_config.class_config_id} "
            f"got_class_config_id={class_config.id}"
        )
    return class_config


# --- AWARE: USER_IMPORTS END


async def create_via_api_call(
    api_call_id: UUID,
    sequence: int,
    api_capability_endpoint_stream_event_config_id: UUID,
    description: str | None = None,
) -> ApiCallStreamEvent:
    """
    Create one API-owned typed stream event receipt beneath ApiCall.
    Runtime derives the event_model owner key from this receipt identity and
    builds the InlineValueInstance from the referenced stream event
    ClassConfig; callers do not supply a schema/id shortcut.
    """

    # --- AWARE: LOGIC START create_via_api_call
    materialization_input = current_api_call_stream_event_materialization_input()
    api_call = materialization_input.api_call if materialization_input is not None else None
    if api_call is not None and api_call.id != api_call_id:
        raise RuntimeError(
            "ApiCallStreamEvent.create_via_api_call received mismatched ApiCall "
            "materialization context: "
            f"expected_api_call_id={api_call_id} got_api_call_id={api_call.id}"
        )
    if api_call is None:
        api_call = current_handler_session().imap_get(ApiCall, api_call_id)
    if api_call is None:
        raise RuntimeError(
            "ApiCallStreamEvent.create_via_api_call requires ApiCall in the current "
            "receipt context: "
            f"api_call_id={api_call_id}"
        )

    stream_event_config = materialization_input.stream_event_config if materialization_input is not None else None
    if stream_event_config is not None:
        if stream_event_config.id != api_capability_endpoint_stream_event_config_id:
            raise RuntimeError(
                "ApiCallStreamEvent.create_via_api_call received mismatched stream event "
                "config context: "
                "expected_stream_event_config_id="
                f"{api_capability_endpoint_stream_event_config_id} "
                f"got_stream_event_config_id={stream_event_config.id}"
            )
    else:
        stream_event_config = current_handler_session().imap_get(
            ApiCapabilityEndpointStreamEventConfig,
            api_capability_endpoint_stream_event_config_id,
        )
    if stream_event_config is None:
        raise RuntimeError(
            "ApiCallStreamEvent.create_via_api_call requires committed stream event "
            "config context: "
            "api_capability_endpoint_stream_event_config_id="
            f"{api_capability_endpoint_stream_event_config_id}"
        )

    stream_event_id = stable_api_call_stream_event_id(
        api_call_id=api_call_id,
        sequence=sequence,
    )
    existing = ApiCallStreamEvent.by_id_cached(stream_event_id)
    if existing is not None:
        if existing.api_capability_endpoint_stream_event_config_id != api_capability_endpoint_stream_event_config_id:
            raise RuntimeError(
                "ApiCallStreamEvent.create_via_api_call found id collision with "
                "mismatched stream event config: "
                f"id={stream_event_id} expected_stream_event_config_id="
                f"{api_capability_endpoint_stream_event_config_id} "
                "got_stream_event_config_id="
                f"{existing.api_capability_endpoint_stream_event_config_id}"
            )
        return _serialization_copy(existing)

    class_config = await _resolve_stream_event_class_config(
        stream_event_config=stream_event_config,
        class_config_hint=(materialization_input.event_class_config if materialization_input is not None else None),
    )
    if class_config.value_mode != ClassValueMode.inline_value:
        raise RuntimeError(
            "ApiCallStreamEvent event-model construction requires inline_value stream "
            "event ClassConfig: "
            f"api_call_id={api_call_id} "
            f"stream_event_class_config_id={class_config.id} "
            f"value_mode={class_config.value_mode}"
        )

    event_values = materialization_input.event_values if materialization_input is not None else None
    if event_values:
        event_model = build_inline_value_instance_from_mapping(
            owner_key=stream_event_id,
            class_config=class_config,
            values={str(k): v for k, v in event_values.items()},
            class_configs_by_id=(
                dict(materialization_input.event_class_configs_by_id)
                if materialization_input is not None and materialization_input.event_class_configs_by_id is not None
                else None
            ),
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=default_meta_class_instance_resolver,
        )
    else:
        with disable_autobind():
            event_model = InlineValueInstance(
                id=stable_inline_value_instance_id(
                    class_config_id=class_config.id,
                    owner_key=stream_event_id,
                ),
                class_config_id=class_config.id,
                class_config=class_config,
                owner_key=stream_event_id,
                inline_value_instance_attributes=[],
            )

    return _serialization_copy(
        ApiCallStreamEvent(
            id=stream_event_id,
            api_call_id=api_call_id,
            api_capability_endpoint_stream_event_config_id=api_capability_endpoint_stream_event_config_id,
            api_capability_endpoint_stream_event_config=stream_event_config,
            event_model_id=event_model.id,
            event_model=event_model,
            sequence=sequence,
            description=description,
        )
    )
    # --- AWARE: LOGIC END create_via_api_call
