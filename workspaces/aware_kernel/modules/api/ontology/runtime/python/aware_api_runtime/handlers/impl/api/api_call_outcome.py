from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
import inspect

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_runtime.invocation.materialization.context import (
    current_api_call_outcome_materialization_input,
)
from aware_meta.class_.inline_value_instance.builder import (
    build_inline_value_instance_from_mapping,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_orm.registry import ORMModelRegistry
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)
from aware_meta.runtime.value_resolvers import (
    default_meta_class_instance_resolver,
    default_meta_enum_option_resolver,
)


def _serialization_copy(outcome: ApiCallOutcome) -> ApiCallOutcome:
    return ApiCallOutcome(
        id=outcome.id,
        api_call_id=outcome.api_call_id,
        response_model_id=outcome.response_model_id,
        status=outcome.status,
        error=outcome.error,
    )


# --- AWARE: USER_IMPORTS END


async def build_via_api_call(
    api_call_id: UUID, status: ApiCallOutcomeStatus = ApiCallOutcomeStatus.succeeded, error: str | None = None
) -> ApiCallOutcome:
    """
    Create one terminal response receipt under ApiCall.
    """

    # --- AWARE: LOGIC START build_via_api_call
    session = current_handler_session()
    materialization_input = current_api_call_outcome_materialization_input()
    api_call = (
        materialization_input.api_call
        if materialization_input is not None and materialization_input.api_call is not None
        else None
    )
    if api_call is not None and api_call.id != api_call_id:
        raise RuntimeError(
            "ApiCallOutcome.build_via_api_call received mismatched ApiCall materialization context: "
            f"expected_api_call_id={api_call_id} got_api_call_id={api_call.id}"
        )
    if api_call is None:
        api_call = session.imap_get(ApiCall, api_call_id)
    if api_call is None:
        raise RuntimeError(
            "ApiCallOutcome.build_via_api_call requires ApiCall to exist in the current session: "
            f"api_call_id={api_call_id}"
        )

    existing = api_call.outcome
    if inspect.isawaitable(existing):
        existing = await existing
    if existing is not None:
        existing.status = status
        existing.error = error
        return _serialization_copy(existing)

    response_model = None
    if materialization_input is not None and materialization_input.response_payload is not None:
        class_config = materialization_input.response_class_config
        if class_config is None:
            api_capability_endpoint = session.imap_get(ApiCapabilityEndpoint, api_call.api_capability_endpoint_id)
            if api_capability_endpoint is None:
                raise RuntimeError(
                    "ApiCallOutcome.build_via_api_call requires ApiCapabilityEndpoint in session when "
                    "response ClassConfig is not provided through materialization input: "
                    f"api_call_id={api_call_id} api_capability_endpoint_id={api_call.api_capability_endpoint_id}"
                )
            request_config = api_capability_endpoint.request_config
            if inspect.isawaitable(request_config):
                request_config = await request_config
            if request_config is None:
                raise RuntimeError(
                    "ApiCallOutcome.build_via_api_call requires endpoint request_config when "
                    "response ClassConfig is not provided through materialization input: "
                    f"api_call_id={api_call_id}"
                )
            response_config = request_config.response_config
            if inspect.isawaitable(response_config):
                response_config = await response_config
            if response_config is None:
                raise RuntimeError(
                    "ApiCallOutcome.build_via_api_call received response payload without an endpoint response "
                    "contract: "
                    f"api_call_id={api_call_id}"
                )
            class_config = session.imap_get(ClassConfig, response_config.class_config_id)
            if class_config is None:
                class_config = current_handler_index().class_configs_by_id.get(response_config.class_config_id)
            if class_config is None:
                orm_class = ORMModelRegistry.get_class_by_class_config_id(response_config.class_config_id)
                if orm_class is not None:
                    class_config = orm_class.get_class_config()
        if class_config is None or class_config.id is None:
            raise RuntimeError(
                "ApiCallOutcome.build_via_api_call could not resolve endpoint response ClassConfig: "
                f"api_call_id={api_call_id}"
            )
        if class_config.value_mode != ClassValueMode.inline_value:
            raise RuntimeError(
                "ApiCallOutcome response-model construction requires inline_value response ClassConfig: "
                f"api_call_id={api_call_id} response_class_config_id={class_config.id} "
                f"value_mode={class_config.value_mode}"
            )
        response_model = build_inline_value_instance_from_mapping(
            owner_key=api_call.call_key,
            class_config=class_config,
            values={str(k): v for k, v in materialization_input.response_payload.items()},
            class_configs_by_id=(
                dict(materialization_input.response_class_configs_by_id)
                if materialization_input.response_class_configs_by_id is not None
                else None
            ),
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=default_meta_class_instance_resolver,
        )

    persisted_outcome = ApiCallOutcome(
        api_call_id=api_call_id,
        response_model_id=response_model.id if response_model is not None else None,
        response_model=response_model,
        status=status,
        error=error,
    )
    return _serialization_copy(persisted_outcome)
    # --- AWARE: LOGIC END build_via_api_call
