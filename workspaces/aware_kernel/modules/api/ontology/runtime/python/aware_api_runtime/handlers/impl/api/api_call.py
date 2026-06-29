from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta.class_.inline_value_instance.builder import (
    build_inline_value_instance_from_mapping,
)
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_meta.runtime.value_resolvers import (
    default_meta_class_instance_resolver,
    default_meta_enum_option_resolver,
)
from aware_orm.session.autobind import disable_autobind
from aware_orm.registry import ORMModelRegistry
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_api_runtime.request_hash import (
    compute_api_request_hash_from_inline_value_instance,
)
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_api_runtime.invocation.materialization.context import (
    current_api_call_materialization_input,
)

# --- AWARE: USER_IMPORTS END


async def create_outcome(
    api_call: ApiCall, status: ApiCallOutcomeStatus = ApiCallOutcomeStatus.succeeded, error: str | None = None
) -> ApiCallOutcome:
    """
    Create one terminal response receipt under this ApiCall.
    """

    # --- AWARE: LOGIC START create_outcome
    if api_call.id is None:
        raise RuntimeError("ApiCall.create_outcome requires ApiCall.id")

    outcome = await ApiCallOutcome.build_via_api_call(
        api_call_id=api_call.id,
        status=status,
        error=error,
    )
    api_call.outcome = outcome
    return outcome
    # --- AWARE: LOGIC END create_outcome


async def create_via_api_capability_endpoint(
    api_capability_endpoint_id: UUID, call_key: UUID, request_class_config_id: UUID, description: str | None = None
) -> ApiCall:
    """
    Create one stage-one API call receipt under ApiCapabilityEndpoint.
    """

    # --- AWARE: LOGIC START create_via_api_capability_endpoint
    session = current_handler_session()
    materialization_input = current_api_call_materialization_input()
    class_config = materialization_input.request_class_config if materialization_input is not None else None
    if class_config is not None:
        if class_config.id != request_class_config_id:
            raise RuntimeError(
                "ApiCall.create_via_api_capability_endpoint received mismatched request ClassConfig in "
                "materialization context: "
                f"expected_request_class_config_id={request_class_config_id} "
                f"got_request_class_config_id={class_config.id}"
            )
    else:
        class_config = session.imap_get(ClassConfig, request_class_config_id)

    if class_config is None:
        orm_class = ORMModelRegistry.get_class_by_class_config_id(request_class_config_id)
        if orm_class is None:
            raise RuntimeError(
                "ApiCall.create_via_api_capability_endpoint requires request ClassConfig resolved by "
                "the endpoint/materialization seam or current session: "
                f"request_class_config_id={request_class_config_id}"
            )
        class_config = orm_class.get_class_config()
        if class_config is None:
            raise RuntimeError(
                "ApiCall.create_via_api_capability_endpoint resolved ORM class without ClassConfig: "
                f"request_class_config_id={request_class_config_id}"
            )
        session.imap_add(class_config)

    if class_config.value_mode != ClassValueMode.inline_value:
        raise RuntimeError(
            "ApiCall request-model construction requires inline_value request ClassConfig: "
            f"request_class_config_id={request_class_config_id} value_mode={class_config.value_mode}"
        )

    if materialization_input is not None and materialization_input.request_payload:
        request_model = build_inline_value_instance_from_mapping(
            owner_key=call_key,
            class_config=class_config,
            values={str(k): v for k, v in materialization_input.request_payload.items()},
            class_configs_by_id=(
                dict(materialization_input.request_class_configs_by_id)
                if materialization_input.request_class_configs_by_id is not None
                else None
            ),
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=default_meta_class_instance_resolver,
        )
    elif materialization_input is not None:
        with disable_autobind():
            request_model = InlineValueInstance(
                id=stable_inline_value_instance_id(
                    class_config_id=request_class_config_id,
                    owner_key=call_key,
                ),
                class_config_id=request_class_config_id,
                class_config=class_config,
                owner_key=call_key,
                inline_value_instance_attributes=[],
            )
    else:
        request_model = await InlineValueInstance.build(
            owner_key=call_key,
            class_config_id=request_class_config_id,
        )
    request_hash = compute_api_request_hash_from_inline_value_instance(
        inline_value_instance=request_model,
        class_config=class_config,
        class_configs_by_id=(
            materialization_input.request_class_configs_by_id if materialization_input is not None else None
        ),
    )
    return ApiCall(
        id=stable_api_call_id(
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=call_key,
        ),
        api_capability_endpoint_id=api_capability_endpoint_id,
        request_model_id=request_model.id,
        request_model=request_model,
        call_key=call_key,
        description=description,
        request_hash=request_hash,
    )
    # --- AWARE: LOGIC END create_via_api_capability_endpoint
