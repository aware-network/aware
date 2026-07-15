from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from aware_api_ontology.stable_ids import stable_api_id
from aware_api_runtime.invocation import (
    ResolvedApiInvocationEnvelope,
    ResolvedApiInvocationFulfillmentBinding,
)
from aware_api_runtime.service_protocol import ApiServiceDispatchPlan
from aware_api_runtime.service_protocol import ApiServiceDispatchFulfillmentBinding
from aware_code.types import JsonObject
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_orm.session.session import Session
from aware_service_ontology.stable_ids import (
    stable_service_config_api_id,
    stable_service_config_id,
    stable_service_operation_config_api_endpoint_id,
    stable_service_operation_config_id,
)
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_contract_operation_permit_policy import (
    ServiceContractOperationPermitPolicy,
)
from aware_service_ontology.service.service_contract_operation_price_policy import (
    ServiceContractOperationPricePolicy,
)
from aware_service_ontology.service.service_contract_operation_quota_policy import (
    ServiceContractOperationQuotaPolicy,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
    ServiceContractOperationPriceSource,
    ServiceContractOperationQuotaOverLimitBehavior,
    ServiceContractOperationQuotaUnit,
    ServiceContractOperationQuotaWindow,
    ServiceContractStatus,
    ServiceOperationFulfillmentKind,
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
    ServiceOperationConfigApiEndpointFunction,
)
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_runtime.api_ingress import (
    build_service_api_graph_execution_plan,
    require_single_service_api_dispatch_candidate,
    resolve_service_api_dispatch,
    validate_service_api_fulfillment_contract,
)
from aware_service_runtime.implementation_package import (
    ActivatedServicePackageBinding,
    build_prepared_service_config_session_for_api_dispatch,
)
from aware_service_runtime.models import (
    ServiceConfigApiPlan,
    ServiceConfigPlan,
    ServiceOperationConfigApiEndpointPlan,
    ServiceOperationConfigPlan,
)
from aware_service_runtime.ontology.materialization.service_operation import (
    MaterializedServiceOperationBinding,
    ServiceOperationMaterializationResult,
)
from aware_service_runtime.api_ingress.execution import (
    ExecutedServiceApiDispatch,
    ServiceApiActorRoleEvidence,
    ServiceApiDispatchReceiptPolicy,
    ServiceApiOperationAccessContext,
    ServiceOperationAdmissionDenied,
    execute_service_api_dispatch_plan,
    read_service_operation_contract_admission,
    service_actor_role_evidence_from_invocation_context,
    service_operation_admission_blocked_payload,
    service_api_dispatch_receipt,
    service_api_dispatch_response_payload,
    service_operation_contract_admission_payload,
    validate_service_api_dispatch_preflight,
    _api_call_hint_from_dispatch_envelope,
)
from aware_service_runtime.api_ingress.settlement import (
    ServiceOperationSettlementReceiptRefs,
)
from aware_service_runtime.api_ingress.admission_context import (
    normalize_service_operation_admission_context,
    service_operation_admission_context_payload,
)
from aware_service_runtime.api_ingress.contract_access_context import (
    read_service_contract_access_context_bootstrap,
    service_contract_access_context_bootstrap_payload,
)


class _OpenRequest(BaseModel):
    label: str


async def _invoke_open(*_: object) -> object | None:
    return None


def _activated_binding_for_compile_plan(
    *, compile_plan
) -> ActivatedServicePackageBinding:
    return cast(
        ActivatedServicePackageBinding,
        cast(
            object,
            SimpleNamespace(
                prepared=SimpleNamespace(
                    compile_result=SimpleNamespace(
                        compile_plan=compile_plan,
                    )
                )
            ),
        ),
    )


def _dispatch_plan(
    *,
    api_capability_endpoint_id,
    request_model_id,
    request_class_config_id,
    fulfillment_name: str,
    api_capability_endpoint_function_id=None,
    call_target_kind: str | None = "instance",
    exact_output_field_name: str | None = None,
    include_fulfillment: bool = True,
):
    resolved_fulfillment_bindings = (
        (
            ResolvedApiInvocationFulfillmentBinding(
                name=fulfillment_name,
                graph_target="aware_home",
                graph_capability_function_name=fulfillment_name,
                source_path="runtime-proof",
                api_capability_endpoint_function_id=(
                    api_capability_endpoint_function_id or uuid4()
                ),
            ),
        )
        if include_fulfillment
        else ()
    )
    envelope = ResolvedApiInvocationEnvelope(
        api_call_id=uuid4(),
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=uuid4(),
        request_hash="sha256:service-dispatch-proof",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="service-proof-projection",
        api_name="openai",
        capability_name="door",
        endpoint_name="open",
        endpoint_ref="openai.door.open",
        discriminant="openai.door.open",
        source_path="runtime-proof",
        request_model_id=request_model_id,
        request_class_config_id=request_class_config_id,
        request_class_ref="aware_proof_types.door.OpenRequest",
        request_source_path="runtime-proof",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=resolved_fulfillment_bindings,
        description="Dispatch proof",
    )
    dispatch_fulfillment_bindings = (
        (
            ApiServiceDispatchFulfillmentBinding(
                name=fulfillment_name,
                graph_target="aware_home",
                graph_capability_function_name=fulfillment_name,
                graph_function_python_ref="aware_home.home.Door.open",
                graph_function_runtime_target="aware_home_ontology.home.home.Door.open",
                call_target_kind=call_target_kind,
                exact_output_field_name=exact_output_field_name,
                method_name=fulfillment_name,
                request_type_ref="aware_proof_protocol.protocols.OpenExecutionRequest",
                response_type_ref="aware_proof_protocol.protocols.OpenExecutionResponse",
                source_path="runtime-proof",
                api_capability_endpoint_function_id=(
                    api_capability_endpoint_function_id or uuid4()
                ),
            ),
        )
        if include_fulfillment
        else ()
    )
    return ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root="aware_proof_api",
        service_protocol_import_root="aware_proof_protocol",
        endpoint_ref=envelope.endpoint_ref,
        api_name=envelope.api_name,
        capability_name=envelope.capability_name,
        endpoint_name=envelope.endpoint_name,
        request_type_ref="aware_proof_api.models.open_request.OpenRequest",
        response_type_ref=None,
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=dispatch_fulfillment_bindings,
        request_object=_OpenRequest(label="front-door"),
        invoke=_invoke_open,
    )


def test_build_prepared_service_config_session_for_endpoint_only_api_dispatch() -> None:
    service_name = "aware_openai"
    service_config_id = stable_service_config_id(name=service_name)
    api_id = stable_api_id(name="openai")
    service_config_api_id = stable_service_config_api_id(
        service_config_id=service_config_id,
        api_id=api_id,
    )
    service_operation_config_id = stable_service_operation_config_id(
        service_config_id=service_config_id,
        name="open_door",
    )
    api_capability_endpoint_id = uuid4()
    endpoint_binding_id = stable_service_operation_config_api_endpoint_id(
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
    )
    compile_plan = SimpleNamespace(
        service_configs=(
            ServiceConfigPlan(
                name=service_name,
                source_path="aware.service.toml",
                apis=(
                    ServiceConfigApiPlan(
                        api_ref="openai",
                        source_path="aware.service.toml",
                    ),
                ),
                experiences=(),
                service_operation_configs=(
                    ServiceOperationConfigPlan(
                        name="open_door",
                        source_path="aware.service.toml",
                        fulfillment_kind="view",
                        api_endpoints=(
                            ServiceOperationConfigApiEndpointPlan(
                                endpoint_ref="openai.door.open",
                                api_ref="openai",
                                source_path="aware.service.toml",
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service-config-proof",
    )
    dispatch_plan = _dispatch_plan(
        api_capability_endpoint_id=api_capability_endpoint_id,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        fulfillment_name="open",
        include_fulfillment=False,
    )

    session = build_prepared_service_config_session_for_api_dispatch(
        activated=_activated_binding_for_compile_plan(compile_plan=compile_plan),
        service_name=service_name,
        dispatch_plan=dispatch_plan,
        service_config_lane=lane,
    )

    assert isinstance(session, Session)
    operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    resolved = resolve_service_api_dispatch(
        session=session,
        dispatch_plan=dispatch_plan,
    )
    candidate = require_single_service_api_dispatch_candidate(
        resolved_dispatch=resolved,
    )
    validated = validate_service_api_fulfillment_contract(
        session=session,
        resolved_dispatch=resolved,
    )

    assert candidate.service_config_api_id == service_config_api_id
    assert candidate.service_operation_config_id == service_operation_config_id
    assert candidate.service_operation_config_api_endpoint_id == endpoint_binding_id
    assert operation_config.fulfillment_kind is ServiceOperationFulfillmentKind.view
    assert validated.bindings == ()


def test_build_prepared_service_config_session_defers_fulfillment_dispatch() -> None:
    compile_plan = SimpleNamespace(
        service_configs=(
            ServiceConfigPlan(
                name="aware_openai",
                source_path="aware.service.toml",
                apis=(),
                experiences=(),
                service_operation_configs=(
                    ServiceOperationConfigPlan(
                        name="open_door",
                        source_path="aware.service.toml",
                        api_endpoints=(
                            ServiceOperationConfigApiEndpointPlan(
                                endpoint_ref="openai.door.open",
                                api_ref="openai",
                                source_path="aware.service.toml",
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    dispatch_plan = _dispatch_plan(
        api_capability_endpoint_id=uuid4(),
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        fulfillment_name="open",
    )
    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service-config-proof",
    )

    session = build_prepared_service_config_session_for_api_dispatch(
        activated=_activated_binding_for_compile_plan(compile_plan=compile_plan),
        service_name="aware_openai",
        dispatch_plan=dispatch_plan,
        service_config_lane=lane,
    )

    assert session is None


def test_resolve_service_api_dispatch_matches_endpoint_binding() -> None:
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_config_api_id = uuid4()
    service_operation_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    endpoint_binding_id = uuid4()

    service_config_api = ServiceConfigApi(
        id=service_config_api_id,
        service_config_id=service_config_id,
        api_id=uuid4(),
        description="Shared API bridge",
    )
    operation_config = ServiceOperationConfig(
        id=service_operation_config_id,
        service_config_id=service_config_id,
        name="open_door",
        description="Open one door",
    )
    endpoint_binding = ServiceOperationConfigApiEndpoint(
        id=endpoint_binding_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        description="Public endpoint",
    )

    for obj in (
        service_config_api,
        operation_config,
        endpoint_binding,
    ):
        session.imap_add(obj)

    dispatch_plan = _dispatch_plan(
        api_capability_endpoint_id=api_capability_endpoint_id,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        fulfillment_name="open",
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )
    candidate = require_single_service_api_dispatch_candidate(
        resolved_dispatch=resolved
    )

    assert resolved.dispatch_plan is dispatch_plan
    assert (
        resolved.dispatch_plan.envelope.request_hash == "sha256:service-dispatch-proof"
    )
    assert candidate.service_config_api_id == service_config_api_id
    assert candidate.service_operation_config_id == service_operation_config_id
    assert candidate.service_operation_config_api_endpoint_id == endpoint_binding_id


def test_service_api_dispatch_preflight_requires_contract_config_operation_grant() -> (
    None
):
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        dispatch_plan,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    preflight = validate_service_api_dispatch_preflight(
        session=session,
        resolved_dispatch=resolved,
        service_id=service_id,
        actor_id=None,
        operation_access_context=ServiceApiOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(
                _subscription(
                    service_id=service_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                ),
            ),
            service_contracts_by_smart_contract_id={
                smart_contract_id: _service_contract(
                    service_id=service_id,
                    service_contract_config_id=service_contract_config_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                )
            },
            service_contract_configs_by_id={
                service_contract_config_id: _contract_config(
                    service_contract_config_id=service_contract_config_id,
                    operation_grants=(grant,),
                )
            },
            now=now,
        ),
    )

    assert (
        preflight.candidate.service_operation_config_id == service_operation_config_id
    )
    assert preflight.access_evidence is not None
    assert preflight.access_evidence.access_granted is True
    assert (
        preflight.access_evidence.service_contract_config_operation_grant_id == grant.id
    )
    assert preflight.contract_admission.allowed is True
    assert preflight.contract_admission.operation_policy is not None
    assert (
        preflight.contract_admission.operation_policy.service_contract_config_operation_grant_id
        == grant.id
    )


def test_service_contract_admission_read_model_summarizes_typed_operation_policies() -> (
    None
):
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        include_typed_policies=True,
    )

    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        operation_access_context=ServiceApiOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(
                _subscription(
                    service_id=service_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                ),
            ),
            service_contracts_by_smart_contract_id={
                smart_contract_id: _service_contract(
                    service_id=service_id,
                    service_contract_config_id=service_contract_config_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                )
            },
            service_contract_configs_by_id={
                service_contract_config_id: _contract_config(
                    service_contract_config_id=service_contract_config_id,
                    operation_grants=(grant,),
                )
            },
            now=now,
        ),
    )

    assert admission.schema == "aware.service.contract_admission.read_model.v0"
    assert admission.allowed is True
    assert admission.status == "allowed"
    assert admission.next_action is None
    assert admission.operation_policy is not None
    assert admission.operation_policy.source == "typed_objects"
    assert admission.operation_policy.quota is not None
    assert admission.operation_policy.quota.unit == "request"
    assert admission.operation_policy.quota.limit_amount == 42
    assert admission.operation_policy.quota.window == "hour"
    assert admission.operation_policy.quota.over_limit_behavior == "throttle"
    assert admission.operation_policy.permit is not None
    assert admission.operation_policy.permit.requires_smart_contract_permit is True
    assert admission.operation_policy.permit.requires_reservation_before_execute is True
    assert admission.operation_policy.permit.idempotency_scope == "operation_nonce"
    assert admission.operation_policy.price is not None
    assert admission.operation_policy.price.price_source == "contract_override"
    assert admission.operation_policy.price.price_ref == "price://workspace/session"
    assert admission.operation_policy.price.pricing_policy_ref == "pricing://agent"
    assert admission.operation_policy.price.settlement_policy_override == (
        "reserve_before_execute"
    )
    assert admission.operation_policy.price.max_cost_required is True


def test_service_contract_admission_binds_permit_to_contract_operation_and_request() -> (
    None
):
    now = datetime(2026, 7, 12, tzinfo=UTC)
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(
        admission_mode="contract_and_permit_required"
    )
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    permit_id = uuid4()
    operation_key = "submit_inference"
    request_hash = "sha256:" + "a" * 64
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        include_typed_policies=True,
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    access_context = ServiceApiOperationAccessContext(
        consumer_finance_entity_id=consumer_finance_entity_id,
        subscriptions=(subscription,),
        service_contracts_by_smart_contract_id={smart_contract_id: service_contract},
        service_contract_configs_by_id={
            service_contract_config_id: _contract_config(
                service_contract_config_id=service_contract_config_id,
                operation_grants=(grant,),
            )
        },
        now=now,
    )

    with pytest.raises(ValueError, match="Unsupported Service operation authorization"):
        normalize_service_operation_admission_context(
            invocation_context={
                "service_operation_authorization": {
                    "contract_version": "aware.service.operation_authorization.legacy",
                }
            }
        )

    missing = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        operation_access_context=access_context,
        operation_key=operation_key,
        request_hash=request_hash,
    )
    assert "missing_operation_authorization" in missing.blocking_reasons

    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "service_operation_authorization": {
                "contract_version": "aware.service.operation_authorization.v1",
                "service_contract_id": str(service_contract.id),
                "permit_id": str(permit_id),
                "operation_key": operation_key,
                "request_hash": request_hash,
            }
        }
    )
    allowed = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        operation_access_context=access_context,
        admission_context=admission_context,
        operation_key=operation_key,
        request_hash=request_hash,
    )
    assert allowed.allowed is True

    wrong_contract_context = normalize_service_operation_admission_context(
        invocation_context={
            "service_operation_authorization": {
                "contract_version": "aware.service.operation_authorization.v1",
                "service_contract_id": str(uuid4()),
                "permit_id": str(permit_id),
                "operation_key": "other_operation",
                "request_hash": request_hash,
            }
        }
    )
    wrong_contract = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        operation_access_context=access_context,
        admission_context=wrong_contract_context,
        operation_key=operation_key,
        request_hash=request_hash,
    )
    assert "authorization_service_contract_mismatch" in wrong_contract.blocking_reasons
    assert "authorization_operation_mismatch" in wrong_contract.blocking_reasons

    mismatched = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        operation_access_context=access_context,
        admission_context=admission_context,
        operation_key=operation_key,
        request_hash="sha256:" + "b" * 64,
    )
    assert "authorization_request_hash_mismatch" in mismatched.blocking_reasons


def test_read_model_dispatch_payload_carries_contract_admission_evidence() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        include_typed_policies=True,
    )
    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        operation_access_context=ServiceApiOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(
                _subscription(
                    service_id=service_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                ),
            ),
            service_contracts_by_smart_contract_id={
                smart_contract_id: _service_contract(
                    service_id=service_id,
                    service_contract_config_id=service_contract_config_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                )
            },
            service_contract_configs_by_id={
                service_contract_config_id: _contract_config(
                    service_contract_config_id=service_contract_config_id,
                    operation_grants=(grant,),
                )
            },
            now=now,
        ),
    )
    executed = ExecutedServiceApiDispatch(
        resolved_dispatch=cast(Any, SimpleNamespace()),
        preflight=cast(
            Any,
            SimpleNamespace(contract_admission=admission),
        ),
        materialized_operation=None,
        updated_operation=None,
        recorded_api_call_outcome=None,
        validated_fulfillment=cast(Any, SimpleNamespace()),
        fulfillment_execution_plan=None,
        execution_object=None,
        response_object={"operation": "status", "result": {"workspace_root": "."}},
        receipt_policy=ServiceApiDispatchReceiptPolicy.read_model,
    )

    payload = service_api_dispatch_response_payload(executed=executed)

    assert isinstance(payload, dict)
    payload_dict = cast(dict[str, Any], payload)
    result_payload = cast(dict[str, Any], payload_dict["result"])
    blocks = cast(list[dict[str, Any]], result_payload["blocks"])
    service_admission = cast(dict[str, Any], payload_dict["service_admission"])
    operation_policy = cast(dict[str, Any], service_admission["operation_policy"])
    price_policy = cast(dict[str, Any], operation_policy["price"])
    assert payload_dict["operation"] == "status"
    assert blocks[0]["name"] == "service_admission"
    assert blocks[0]["authority_kind"] == ("service_contract_admission")
    assert service_admission["schema"] == (
        "aware.service.contract_admission.read_model.v0"
    )
    assert service_admission["admission_mode"] == "public_read"
    assert service_admission["contract_context_required"] is False
    assert service_admission["permit_required"] is False
    assert service_admission["settlement_required"] is False
    assert service_admission["allowed"] is True
    assert operation_policy["source"] == "typed_objects"
    assert price_policy["price_ref"] == "price://workspace/session"


def test_committed_dispatch_payload_does_not_carry_read_model_admission() -> None:
    executed = ExecutedServiceApiDispatch(
        resolved_dispatch=cast(Any, SimpleNamespace()),
        preflight=cast(Any, SimpleNamespace()),
        materialized_operation=None,
        updated_operation=None,
        recorded_api_call_outcome=None,
        validated_fulfillment=cast(Any, SimpleNamespace()),
        fulfillment_execution_plan=None,
        execution_object=None,
        response_object={"operation": "commit"},
        receipt_policy=ServiceApiDispatchReceiptPolicy.committed,
    )

    payload = service_api_dispatch_response_payload(executed=executed)

    assert payload == {"operation": "commit"}


def test_committed_dispatch_receipt_carries_call_and_operation_metadata() -> None:
    api_call_id = uuid4()
    api_capability_endpoint_id = uuid4()
    call_key = uuid4()
    request_model_id = uuid4()
    network_request_id = uuid4()
    service_operation_id = uuid4()
    service_operation_config_id = uuid4()
    service_operation_config_api_endpoint_id = uuid4()
    service_operation_commit_id = uuid4()
    api_call_outcome_id = uuid4()
    response_model_id = uuid4()
    api_call_outcome_commit_id = uuid4()
    api_call_outcome_branch_id = uuid4()
    service_contract_id = uuid4()
    permit_id = uuid4()
    settlement_id = uuid4()
    executed = ExecutedServiceApiDispatch(
        resolved_dispatch=cast(
            Any,
            SimpleNamespace(
                dispatch_plan=SimpleNamespace(
                    envelope=SimpleNamespace(
                        endpoint_ref="identity.admit_identity",
                        discriminant="identity.admit_identity",
                        api_call_id=api_call_id,
                        api_capability_endpoint_id=api_capability_endpoint_id,
                        call_key=call_key,
                        request_hash="request-hash",
                        request_model_id=request_model_id,
                    )
                )
            ),
        ),
        preflight=cast(Any, SimpleNamespace()),
        materialized_operation=None,
        updated_operation=cast(
            Any,
            SimpleNamespace(
                binding=SimpleNamespace(
                    service_operation_id=service_operation_id,
                    service_operation_config_id=service_operation_config_id,
                    api_endpoint_id=service_operation_config_api_endpoint_id,
                    commit_id=service_operation_commit_id,
                    head_commit_id=service_operation_commit_id,
                    branch_id=uuid4(),
                    projection_hash="service.config",
                )
            ),
        ),
        recorded_api_call_outcome=cast(
            Any,
            SimpleNamespace(
                binding=SimpleNamespace(
                    api_call_outcome_id=api_call_outcome_id,
                    response_model_id=response_model_id,
                    commit_id=api_call_outcome_commit_id,
                    head_commit_id=api_call_outcome_commit_id,
                    branch_id=api_call_outcome_branch_id,
                    projection_hash="api.call",
                )
            ),
        ),
        validated_fulfillment=cast(Any, SimpleNamespace()),
        fulfillment_execution_plan=None,
        execution_object=None,
        response_object={"operation": "commit"},
        settlement_receipt=ServiceOperationSettlementReceiptRefs(
            service_operation_id=service_operation_id,
            service_contract_id=service_contract_id,
            permit_id=permit_id,
            price_id=uuid4(),
            price_schedule_id=uuid4(),
            rate_snapshot_id=uuid4(),
            price_reservation_id=uuid4(),
            smart_contract_reservation_id=uuid4(),
            settlement_id=settlement_id,
            transaction_id=uuid4(),
            payer_wallet_balance_id=uuid4(),
            receiver_wallet_balance_id=uuid4(),
            status="settled",
            idempotent_replay=False,
        ),
        receipt_policy=ServiceApiDispatchReceiptPolicy.committed,
    )

    receipt = service_api_dispatch_receipt(
        executed=executed,
        network_request_id=network_request_id,
    )

    assert receipt.endpoint_ref == "identity.admit_identity"
    assert receipt.network_request_id == network_request_id
    assert receipt.api_call_id == api_call_id
    assert receipt.api_capability_endpoint_id == api_capability_endpoint_id
    assert receipt.call_key == call_key
    assert receipt.request_model_id == request_model_id
    assert receipt.service_operation_id == service_operation_id
    assert receipt.service_operation_config_id == service_operation_config_id
    assert (
        receipt.service_operation_config_api_endpoint_id
        == service_operation_config_api_endpoint_id
    )
    assert receipt.service_operation_commit_id == service_operation_commit_id
    assert receipt.api_call_outcome_id == api_call_outcome_id
    assert receipt.response_model_id == response_model_id
    assert receipt.api_call_outcome_commit_id == api_call_outcome_commit_id
    assert receipt.api_call_outcome_branch_id == api_call_outcome_branch_id
    assert receipt.economic_receipt is not None
    assert receipt.economic_receipt.service_contract_id == service_contract_id
    assert receipt.economic_receipt.permit_id == permit_id
    assert receipt.economic_receipt.settlement_id == settlement_id
    assert receipt.economic_receipt.status == "settled"


def test_api_call_hint_from_dispatch_envelope_carries_request_anchor() -> None:
    request_model_id = uuid4()
    request_class_config_id = uuid4()
    call_key = uuid4()
    envelope = SimpleNamespace(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=call_key,
        request_hash="sha256:request",
        request_model_id=request_model_id,
        request_class_config_id=request_class_config_id,
        description="deferred final receipt",
    )

    api_call = _api_call_hint_from_dispatch_envelope(envelope)

    assert api_call.request_model_id == request_model_id
    assert api_call.request_model is not None
    assert api_call.request_model.id == request_model_id
    assert api_call.request_model.class_config_id == request_class_config_id
    assert api_call.request_model.owner_key == call_key
    assert api_call.request_model.inline_value_instance_attributes == []


def test_service_contract_admission_read_model_reports_identity_blocker_without_raising() -> (
    None
):
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        role_config_id,
    ) = _service_api_dispatch_preflight_session(with_role_requirement=True)

    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
    )

    assert admission.allowed is False
    assert admission.status == "denied"
    assert admission.blocking_reasons == ("missing_actor_id",)
    assert admission.next_action == "resolve_identity"
    assert admission.actor_role_requirements
    assert admission.actor_role_requirements[0].role_config_id == role_config_id
    assert admission.actor_role_requirements[0].satisfied is False


def test_service_contract_admission_read_model_blocks_missing_contract_context() -> (
    None
):
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")

    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
    )

    assert admission.admission_mode == "contract_required"
    assert admission.contract_context_required is True
    assert admission.allowed is False
    assert admission.status == "denied"
    assert admission.blocking_reasons == ("missing_contract_access_context",)
    assert admission.next_action == "resolve_service_contract_context"


def test_service_admission_context_normalizes_workspace_actor_session_payload() -> None:
    actor_id = uuid4()

    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "actor_context": {
                "status": "ready",
                "kind": "agent_operator",
                "source": "aware-dev",
                "actor_id": str(actor_id),
                "identity_id": str(uuid4()),
                "execution_id": "codex-test",
                "provider_key": "codex",
                "provider_session_id": "test-session",
                "agent_process_thread_id": "thread-1",
            },
            "session_scope": {
                "workspace_root": "/repo/workspaces/aware_kernel",
                "branch_key": "main",
                "session_key": "workspace-session:test",
                "actor_id": str(actor_id),
            },
        },
    )

    assert admission_context.effective_actor_id == actor_id
    assert admission_context.participant_admission is not None
    assert admission_context.participant_admission.admitted is True
    assert admission_context.session_scope is not None
    assert admission_context.session_scope.workspace_root == (
        "/repo/workspaces/aware_kernel"
    )
    payload = service_operation_admission_context_payload(admission_context)
    assert payload is not None
    actor_payload = cast(dict[str, object], payload["actor_context"])
    participant_payload = cast(dict[str, object], payload["participant_admission"])
    assert actor_payload["kind"] == "agent_operator"
    assert actor_payload["actor_id"] == str(actor_id)
    assert participant_payload["status"] == "admitted"
    assert participant_payload["admitted"] is True


def test_service_admission_context_preserves_explicit_actor_identity_refs() -> None:
    actor_id = uuid4()
    identity_id = uuid4()

    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "actor_context": {
                "status": "ready",
                "kind": "agent_operator",
                "actor_id": str(actor_id),
                "actor_ref": f"actor:{actor_id}",
                "identity_id": str(identity_id),
                "identity_ref": f"identity:{identity_id}",
            },
            "session_scope": {
                "scope_kind": "experience_session",
                "scope_ref": "aware_conversations:main",
                "actor_id": str(actor_id),
                "actor_ref": f"session-actor:{actor_id}",
            },
            "participant_admission": {
                "status": "admitted",
                "admitted": True,
                "actor_id": str(actor_id),
                "actor_ref": f"participant-actor:{actor_id}",
                "identity_id": str(identity_id),
                "identity_ref": f"participant-identity:{identity_id}",
            },
        },
    )

    assert admission_context.actor_context is not None
    assert admission_context.actor_context.actor_ref == f"actor:{actor_id}"
    assert admission_context.actor_context.identity_ref == f"identity:{identity_id}"
    assert admission_context.session_scope is not None
    assert admission_context.session_scope.actor_ref == f"session-actor:{actor_id}"
    assert admission_context.participant_admission is not None
    assert admission_context.participant_admission.actor_ref == (
        f"participant-actor:{actor_id}"
    )
    assert admission_context.participant_admission.identity_ref == (
        f"participant-identity:{identity_id}"
    )


def test_service_contract_admission_read_model_allows_identity_context() -> None:
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="identity_required")
    actor_id = uuid4()
    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "actor_context": {
                "status": "ready",
                "kind": "human_identity",
                "source": "identity-service",
                "actor_id": str(actor_id),
            }
        },
    )

    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        admission_context=admission_context,
    )

    assert admission.allowed is True
    assert admission.actor_context_required is True
    assert admission.actor_id == actor_id
    assert admission.admission_context is admission_context
    assert admission.blocking_reasons == ()
    payload = service_operation_admission_context_payload(admission.admission_context)
    assert payload is not None
    participant_payload = cast(dict[str, object], payload["participant_admission"])
    assert participant_payload["admitted"] is True


def test_service_contract_admission_read_model_blocks_session_scope_mismatch() -> None:
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="identity_required")
    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "actor_context": {
                "status": "ready",
                "kind": "service_actor",
                "source": "experience-service",
                "actor_id": str(uuid4()),
            },
            "session_scope": {
                "experience_name": "aware_control_identity",
                "actor_id": str(uuid4()),
            },
        },
    )

    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
        admission_context=admission_context,
    )

    assert admission.allowed is False
    assert admission.blocking_reasons == ("session_actor_scope_mismatch",)
    assert admission.next_action == "bind_session_actor"
    read_model_context = admission.admission_context
    assert read_model_context is admission_context
    assert read_model_context is not None
    participant_admission = read_model_context.participant_admission
    assert participant_admission is not None
    assert participant_admission.reason == "actor_scope_mismatch"


def test_service_contract_admission_read_model_allows_public_read_without_contract_context() -> (
    None
):
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="public_read")

    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=None,
    )

    assert admission.admission_mode == "public_read"
    assert admission.contract_context_required is False
    assert admission.allowed is True
    assert admission.status == "allowed"
    assert admission.blocking_reasons == ()


def test_service_api_dispatch_preflight_denies_missing_contract_context() -> None:
    (
        session,
        dispatch_plan,
        service_id,
        _,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    with pytest.raises(
        ServiceOperationAdmissionDenied,
        match="missing_contract_access_context",
    ) as exc_info:
        validate_service_api_dispatch_preflight(
            session=session,
            resolved_dispatch=resolved,
            service_id=service_id,
            actor_id=None,
        )
    blocked_payload = service_operation_admission_blocked_payload(
        admission=exc_info.value.admission,
        endpoint_ref=dispatch_plan.endpoint_ref,
        discriminant=dispatch_plan.envelope.discriminant,
        network_request_id=uuid4(),
    )
    assert blocked_payload["schema"] == ("aware.service.admission.blocked_response.v0")
    assert blocked_payload["status"] == "blocked"
    assert blocked_payload["blocker"] == "missing_contract_access_context"
    assert blocked_payload["missing_requirements"] == [
        "missing_contract_access_context"
    ]
    assert blocked_payload["next_action"] == "resolve_service_contract_context"
    assert blocked_payload["admission_mode"] == "contract_required"
    assert blocked_payload["contract_context_required"] is True
    service_admission = cast(dict[str, Any], blocked_payload["service_admission"])
    assert service_admission["allowed"] is False
    assert service_admission["blocking_reasons"] == ["missing_contract_access_context"]


def test_service_api_dispatch_preflight_resolves_contract_context_from_admission_ref() -> (
    None
):
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        dispatch_plan,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        include_typed_policies=True,
    )
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    contract_config = _contract_config(
        service_contract_config_id=service_contract_config_id,
        operation_grants=(grant,),
    )
    for obj in (subscription, service_contract, contract_config):
        session.imap_add(obj)
    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "service_contract_access_context": {
                "consumer_finance_entity_id": str(consumer_finance_entity_id),
                "service_subscription_id": str(subscription.id),
                "service_contract_id": str(service_contract.id),
                "service_contract_config_id": str(contract_config.id),
                "smart_contract_id": str(smart_contract_id),
            }
        },
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    preflight = validate_service_api_dispatch_preflight(
        session=session,
        resolved_dispatch=resolved,
        service_id=service_id,
        actor_id=None,
        admission_context=admission_context,
        operation_access_context=ServiceApiOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(subscription,),
            service_contracts_by_smart_contract_id={
                smart_contract_id: service_contract,
            },
            service_contract_configs_by_id={
                service_contract_config_id: contract_config,
            },
            now=now,
        ),
    )

    assert preflight.access_evidence is not None
    assert preflight.access_evidence.access_granted is True
    assert preflight.access_evidence.service_subscription_id == subscription.id
    assert preflight.access_evidence.service_contract_id == service_contract.id
    assert preflight.contract_admission.allowed is True
    assert preflight.contract_admission.contract_access_resolution is None
    admission_payload = service_operation_contract_admission_payload(
        preflight.contract_admission
    )
    assert admission_payload["contract_access_resolution"] is None


def test_service_contract_access_context_bootstrap_returns_admission_refs() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        dispatch_plan,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        include_typed_policies=True,
    )
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    contract_config = _contract_config(
        service_contract_config_id=service_contract_config_id,
        operation_grants=(grant,),
    )
    for obj in (subscription, service_contract, contract_config):
        session.imap_add(obj)

    bootstrap = read_service_contract_access_context_bootstrap(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
    )

    assert bootstrap.schema == (
        "aware.service.contract_access_context.bootstrap_read_model.v0"
    )
    assert bootstrap.ready is True
    assert bootstrap.status == "ready"
    assert bootstrap.blockers == ()
    assert bootstrap.next_action is None
    assert bootstrap.service_subscription_id == subscription.id
    assert bootstrap.service_contract_id == service_contract.id
    assert bootstrap.service_contract_config_id == contract_config.id
    assert bootstrap.smart_contract_id == smart_contract_id
    payload = service_contract_access_context_bootstrap_payload(bootstrap)
    contract_access_context = cast(
        dict[str, Any],
        payload["service_contract_access_context"],
    )
    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "service_contract_access_context": contract_access_context,
        },
    )
    resolved = resolve_service_api_dispatch(
        session=session,
        dispatch_plan=dispatch_plan,
    )

    preflight = validate_service_api_dispatch_preflight(
        session=session,
        resolved_dispatch=resolved,
        service_id=service_id,
        actor_id=None,
        admission_context=admission_context,
        operation_access_context=ServiceApiOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(subscription,),
            service_contracts_by_smart_contract_id={
                smart_contract_id: service_contract,
            },
            service_contract_configs_by_id={
                service_contract_config_id: contract_config,
            },
            now=now,
        ),
    )

    assert preflight.contract_admission.allowed is True
    assert preflight.contract_admission.contract_access_resolution is None


def test_service_contract_access_context_bootstrap_allows_generic_context_ref() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        include_typed_policies=True,
    )
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    contract_config = _contract_config(
        service_contract_config_id=service_contract_config_id,
        operation_grants=(grant,),
    )
    for obj in (subscription, service_contract, contract_config):
        session.imap_add(obj)

    bootstrap = read_service_contract_access_context_bootstrap(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
    )

    assert bootstrap.ready is True
    assert bootstrap.status == "ready"
    assert bootstrap.service_operation_config_id is None
    assert bootstrap.blockers == ()
    assert bootstrap.contract_access_context_ref is not None
    assert bootstrap.contract_access_context_ref.consumer_finance_entity_id == (
        consumer_finance_entity_id
    )
    payload = service_contract_access_context_bootstrap_payload(bootstrap)
    assert payload["ready"] is True
    assert "service_operation_config_id" not in payload
    assert payload["service_contract_access_context"]


def test_service_contract_access_context_bootstrap_reports_actionable_blockers() -> (
    None
):
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        now=now,
    )
    contract_config = _contract_config(
        service_contract_config_id=service_contract_config_id,
        operation_grants=(),
    )
    for obj in (subscription, service_contract, contract_config):
        session.imap_add(obj)

    bootstrap = read_service_contract_access_context_bootstrap(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
    )

    assert bootstrap.ready is False
    assert bootstrap.status == "blocked"
    assert bootstrap.blocker == "operation_not_granted"
    assert bootstrap.blockers == ("operation_not_granted",)
    assert bootstrap.next_action == "grant_service_operation"
    payload = service_contract_access_context_bootstrap_payload(bootstrap)
    assert payload["blockers"] == ["operation_not_granted"]
    assert "service_contract_access_context" not in payload


def test_service_contract_access_context_bootstrap_reports_missing_setup() -> None:
    (
        session,
        _,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")

    bootstrap = read_service_contract_access_context_bootstrap(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=uuid4(),
        service_operation_config_id=service_operation_config_id,
    )

    assert bootstrap.ready is False
    assert bootstrap.blocker == "missing_subscription"
    assert bootstrap.blockers == (
        "missing_subscription",
        "missing_service_contract",
        "missing_contract_config",
    )
    assert bootstrap.next_action == "resolve_service_subscription"


def test_service_api_dispatch_preflight_blocks_unresolved_contract_ref() -> None:
    (
        session,
        dispatch_plan,
        service_id,
        _,
        _,
    ) = _service_api_dispatch_preflight_session(admission_mode="contract_required")
    consumer_finance_entity_id = uuid4()
    missing_subscription_id = uuid4()
    admission_context = normalize_service_operation_admission_context(
        invocation_context={
            "service_contract_access_context": {
                "consumer_finance_entity_id": str(consumer_finance_entity_id),
                "service_subscription_id": str(missing_subscription_id),
            }
        },
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    with pytest.raises(
        ServiceOperationAdmissionDenied,
        match="missing_subscription",
    ) as exc_info:
        validate_service_api_dispatch_preflight(
            session=session,
            resolved_dispatch=resolved,
            service_id=service_id,
            actor_id=None,
            admission_context=admission_context,
        )

    admission = exc_info.value.admission
    assert admission.blocking_reasons == ("missing_subscription",)
    assert admission.next_action == "resolve_service_subscription"
    resolution = admission.contract_access_resolution
    assert resolution is not None
    assert resolution.status == "partial"
    assert resolution.resolved is False
    assert resolution.blocker == "service_subscription_not_found"
    blocked_payload = service_operation_admission_blocked_payload(
        admission=admission,
        endpoint_ref=dispatch_plan.endpoint_ref,
        discriminant=dispatch_plan.envelope.discriminant,
        network_request_id=uuid4(),
    )
    resolution_payload = cast(
        dict[str, Any],
        blocked_payload["contract_access_resolution"],
    )
    assert blocked_payload["blocker"] == "missing_subscription"
    assert resolution_payload["blocker"] == "service_subscription_not_found"


def test_service_api_dispatch_preflight_denies_missing_operation_grant() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        dispatch_plan,
        service_id,
        service_operation_config_id,
        _,
    ) = _service_api_dispatch_preflight_session()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    with pytest.raises(PermissionError, match="missing_operation_grant"):
        validate_service_api_dispatch_preflight(
            session=session,
            resolved_dispatch=resolved,
            service_id=service_id,
            actor_id=None,
            operation_access_context=ServiceApiOperationAccessContext(
                consumer_finance_entity_id=consumer_finance_entity_id,
                subscriptions=(
                    _subscription(
                        service_id=service_id,
                        consumer_finance_entity_id=consumer_finance_entity_id,
                        smart_contract_id=smart_contract_id,
                        now=now,
                    ),
                ),
                service_contracts_by_smart_contract_id={
                    smart_contract_id: _service_contract(
                        service_id=service_id,
                        service_contract_config_id=service_contract_config_id,
                        consumer_finance_entity_id=consumer_finance_entity_id,
                        smart_contract_id=smart_contract_id,
                        now=now,
                    )
                },
                service_contract_configs_by_id={
                    service_contract_config_id: _contract_config(
                        service_contract_config_id=service_contract_config_id,
                        operation_grants=(),
                    )
                },
                now=now,
            ),
        )


def test_service_api_dispatch_preflight_requires_actor_role_evidence() -> None:
    (
        session,
        dispatch_plan,
        service_id,
        service_operation_config_id,
        role_config_id,
    ) = _service_api_dispatch_preflight_session(with_role_requirement=True)
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    with pytest.raises(PermissionError, match="actor_id is required"):
        validate_service_api_dispatch_preflight(
            session=session,
            resolved_dispatch=resolved,
            service_id=service_id,
            actor_id=None,
        )

    with pytest.raises(PermissionError, match=str(role_config_id)):
        validate_service_api_dispatch_preflight(
            session=session,
            resolved_dispatch=resolved,
            service_id=service_id,
            actor_id=uuid4(),
        )

    assert service_operation_config_id is not None


def test_service_api_dispatch_preflight_accepts_actor_role_evidence() -> None:
    (
        session,
        dispatch_plan,
        service_id,
        _,
        role_config_id,
    ) = _service_api_dispatch_preflight_session(with_role_requirement=True)
    actor_id = uuid4()
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )

    preflight = validate_service_api_dispatch_preflight(
        session=session,
        resolved_dispatch=resolved,
        service_id=service_id,
        actor_id=actor_id,
        actor_role_evidence=(
            ServiceApiActorRoleEvidence(
                actor_id=actor_id,
                role_config_id=role_config_id,
                access_scope="operation",
                scope_kind="operation",
                scope_ref="default",
                role_assignment_binding_id=uuid4(),
            ),
        ),
    )

    assert len(preflight.actor_role_evidence) == 1
    assert preflight.actor_role_evidence[0].role_config_id == role_config_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "operation_kind",
        "receipt_policy",
        "include_fulfillment",
        "stream_requested",
        "expected_match",
    ),
    (
        (
            ServiceOperationFulfillmentKind.view,
            ServiceApiDispatchReceiptPolicy.committed,
            True,
            False,
            "actual='view' required='coordination'",
        ),
        (
            ServiceOperationFulfillmentKind.coordination,
            ServiceApiDispatchReceiptPolicy.committed,
            False,
            True,
            "actual='coordination' required='actuation'",
        ),
        (
            ServiceOperationFulfillmentKind.actuation,
            ServiceApiDispatchReceiptPolicy.committed,
            True,
            False,
            "actual='actuation' required='coordination'",
        ),
        (
            ServiceOperationFulfillmentKind.coordination,
            ServiceApiDispatchReceiptPolicy.read_model,
            False,
            False,
            "actual='coordination' required='view'",
        ),
    ),
)
async def test_service_api_dispatch_rejects_incompatible_fulfillment_kind_before_handler(
    operation_kind: ServiceOperationFulfillmentKind,
    receipt_policy: ServiceApiDispatchReceiptPolicy,
    include_fulfillment: bool,
    stream_requested: bool,
    expected_match: str,
) -> None:
    (
        session,
        dispatch_plan,
        service_id,
        _,
        _,
    ) = _service_api_dispatch_preflight_session(
        fulfillment_kind=operation_kind,
        include_fulfillment=include_fulfillment,
    )
    handler_invoked = False

    async def _invoke_should_not_run(*_: object) -> object | None:
        nonlocal handler_invoked
        handler_invoked = True
        return None

    async def _record_stream_event(_: object) -> None:
        return None

    dispatch_plan = replace(dispatch_plan, invoke=_invoke_should_not_run)

    with pytest.raises(
        RuntimeError,
        match=expected_match,
    ):
        await execute_service_api_dispatch_plan(
            runtime=object(),
            index=object(),
            session=session,
            actor_id=None,
            target_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="service-proof-projection",
            ),
            dispatch_plan=dispatch_plan,
            service_id=service_id,
            operation_key="open_door",
            handler=object(),
            receipt_policy=receipt_policy,
            stream_requested=stream_requested,
            stream_event_sink=(_record_stream_event if stream_requested else None),
        )

    assert handler_invoked is False


@pytest.mark.asyncio
async def test_service_api_dispatch_lifts_actor_role_evidence_from_invocation_context() -> (
    None
):
    (
        session,
        dispatch_plan,
        service_id,
        _,
        role_config_id,
    ) = _service_api_dispatch_preflight_session(
        with_role_requirement=True,
        include_fulfillment=False,
        fulfillment_kind=ServiceOperationFulfillmentKind.view,
    )
    actor_id = uuid4()
    role_assignment_binding_id = uuid4()
    target_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service-context-role-evidence",
    )
    invocation_context = {
        "service_operation_admission_context": {
            "actor_context": {
                "status": "ready",
                "kind": "experience_service",
                "actor_id": str(actor_id),
            },
            "service_actor_role_evidence": [
                {
                    "actor_id": str(actor_id),
                    "role_config_id": str(role_config_id),
                    "access_scope": "operation",
                    "scope_kind": "operation",
                    "scope_ref": "default",
                    "role_assignment_binding_id": str(role_assignment_binding_id),
                    "granted": True,
                }
            ],
        }
    }

    parsed_evidence = service_actor_role_evidence_from_invocation_context(
        invocation_context=invocation_context,
    )
    assert parsed_evidence[0].role_assignment_binding_id == (role_assignment_binding_id)

    executed = await execute_service_api_dispatch_plan(
        runtime=object(),
        index=object(),
        session=session,
        actor_id=None,
        target_lane=target_lane,
        dispatch_plan=dispatch_plan,
        service_id=service_id,
        operation_key="api_ingress:openai.door.open:test",
        handler=object(),
        invocation_context=cast(JsonObject, invocation_context),
        receipt_policy=ServiceApiDispatchReceiptPolicy.read_model,
    )

    assert executed.preflight.actor_role_evidence == parsed_evidence
    assert executed.preflight.contract_admission.actor_id == actor_id


@pytest.mark.asyncio
async def test_read_model_dispatch_materialization_context_uses_execution_target_lane() -> (
    None
):
    from aware_service_runtime.api_ingress.host_context import (
        require_current_service_api_materialization_context,
    )

    session, dispatch_plan, service_id, _, _ = _service_api_dispatch_preflight_session(
        include_fulfillment=False,
        fulfillment_kind=ServiceOperationFulfillmentKind.view,
    )
    service_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service-lane-projection",
    )
    execution_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="execution-lane-projection",
    )
    observed_lanes: list[MaterializationLaneContext] = []

    async def _invoke(*_: object) -> object:
        materialization = require_current_service_api_materialization_context()
        observed_lanes.append(materialization.target_lane)
        return SimpleNamespace(ok=True)

    dispatch_plan = replace(dispatch_plan, invoke=_invoke)

    executed = await execute_service_api_dispatch_plan(
        runtime=object(),
        index=object(),
        session=session,
        actor_id=None,
        target_lane=service_lane,
        execution_target_lane=execution_lane,
        dispatch_plan=dispatch_plan,
        service_id=service_id,
        operation_key="api_ingress:openai.door.open:test",
        handler=object(),
        receipt_policy=ServiceApiDispatchReceiptPolicy.read_model,
    )

    assert executed.response_object == SimpleNamespace(ok=True)
    assert observed_lanes == [execution_lane]


@pytest.mark.asyncio
async def test_committed_endpoint_only_dispatch_uses_single_final_service_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.api_ingress.execution as execution_mod
    from aware_api_runtime.invocation.materialization.telemetry import (
        api_invocation_trace_phase,
    )
    from aware_service_runtime.api_ingress.telemetry import (
        collect_service_api_trace_timings,
    )

    session, dispatch_plan, service_id, service_operation_config_id, _ = (
        _service_api_dispatch_preflight_session(include_fulfillment=False)
    )
    target_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service-final-receipt",
    )
    materialized_statuses: list[ServiceOperationStatus] = []
    hydrate_flags: list[object] = []
    service_operation_id = uuid4()
    api_endpoint_id = uuid4()

    async def _fake_materialize_service_operation(**kwargs: object) -> object:
        status = cast(ServiceOperationStatus, kwargs["status"])
        materialized_statuses.append(status)
        hydrate_flags.append(kwargs.get("hydrate_committed_operation"))
        binding = MaterializedServiceOperationBinding(
            service_operation_id=service_operation_id,
            service_operation_config_id=service_operation_config_id,
            service_id=service_id,
            api_call_id=dispatch_plan.envelope.api_call_id,
            api_endpoint_id=api_endpoint_id,
            operation_key=cast(str, kwargs["operation_key"]),
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
        )
        return ServiceOperationMaterializationResult(
            resolved_dispatch=cast(Any, kwargs["resolved_dispatch"]),
            candidate=execution_mod.require_single_service_api_dispatch_candidate(
                resolved_dispatch=cast(Any, kwargs["resolved_dispatch"])
            ),
            binding=binding,
            service_operation=cast(
                Any,
                SimpleNamespace(
                    id=service_operation_id,
                    status=status,
                    result_info=kwargs.get("result_info"),
                    api_call_id=dispatch_plan.envelope.api_call_id,
                    api_endpoint_id=api_endpoint_id,
                ),
            ),
        )

    async def _fail_materialize_service_operation_status(**_: object) -> object:
        raise AssertionError("endpoint-only final receipts must not write status")

    async def _fake_materialize_api_call_outcome(**kwargs: object) -> object:
        with api_invocation_trace_phase("api_call_outcome.fake_child"):
            pass
        outcome_id = uuid4()
        return SimpleNamespace(
            binding=SimpleNamespace(
                api_call_outcome_id=outcome_id,
                api_call_id=dispatch_plan.envelope.api_call_id,
                response_model_id=None,
                commit_id=uuid4(),
                head_commit_id=uuid4(),
                branch_id=kwargs["target_lane"].branch_id,
                projection_hash=kwargs["target_lane"].projection_hash,
            ),
            api_call=SimpleNamespace(id=dispatch_plan.envelope.api_call_id),
            api_call_outcome=SimpleNamespace(
                id=outcome_id,
                status=kwargs["status"],
                error=kwargs.get("error"),
            ),
            last_commit_id=uuid4(),
            last_head_commit_id=uuid4(),
        )

    monkeypatch.setattr(
        execution_mod,
        "materialize_service_operation",
        _fake_materialize_service_operation,
    )
    monkeypatch.setattr(
        execution_mod,
        "materialize_service_operation_status",
        _fail_materialize_service_operation_status,
    )
    monkeypatch.setattr(
        execution_mod,
        "materialize_api_call_outcome",
        _fake_materialize_api_call_outcome,
    )

    with collect_service_api_trace_timings() as service_timings:
        executed = await execute_service_api_dispatch_plan(
            runtime=object(),
            index=object(),
            session=session,
            actor_id=None,
            target_lane=target_lane,
            dispatch_plan=dispatch_plan,
            service_id=service_id,
            operation_key="api_ingress:openai.door.open:final-only",
            handler=object(),
        )

    assert materialized_statuses == [ServiceOperationStatus.succeeded]
    assert hydrate_flags == [False]
    assert executed.materialized_operation is not None
    assert executed.updated_operation is not None
    assert (
        executed.materialized_operation.binding.service_operation_id
        == service_operation_id
    )
    assert executed.materialized_operation.service_operation.status == (
        ServiceOperationStatus.succeeded
    )
    assert executed.updated_operation.binding is executed.materialized_operation.binding
    assert executed.updated_operation.service_operation is (
        executed.materialized_operation.service_operation
    )
    assert "dispatch.materialize_api_call_outcome_s" in service_timings
    assert (
        "dispatch.materialize_api_call_outcome.api_call_outcome.fake_child_s"
        in service_timings
    )
    assert "dispatch.execute.resolve_service_api_dispatch_s" in service_timings
    assert "dispatch.execute.validate_service_api_preflight_s" in service_timings
    assert "dispatch.execute.final_receipt_dispatch_s" in service_timings
    assert "dispatch.execute.child_tracked_s" in service_timings
    assert "dispatch.execute.unattributed_s" in service_timings
    assert "dispatch.final_receipt.validate_fulfillment_contract_s" in service_timings
    assert "dispatch.final_receipt.host_context_s" in service_timings
    assert "dispatch.final_receipt.materialize_service_operation_s" in service_timings
    assert "dispatch.final_receipt.materialize_api_call_outcome_s" in service_timings
    assert "dispatch.final_receipt.child_tracked_s" in service_timings
    assert "dispatch.final_receipt.unattributed_s" in service_timings


def test_validate_service_api_fulfillment_contract_matches_allowed_endpoint_function() -> (
    None
):
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_config_api_id = uuid4()
    service_operation_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    endpoint_binding_id = uuid4()
    api_capability_endpoint_function_id = uuid4()
    endpoint_function_binding_id = uuid4()

    endpoint_binding = ServiceOperationConfigApiEndpoint(
        id=endpoint_binding_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        description="Public endpoint",
    )
    endpoint_function_binding = ServiceOperationConfigApiEndpointFunction(
        id=endpoint_function_binding_id,
        service_operation_config_api_endpoint_id=endpoint_binding_id,
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
        description="Allowed API fulfillment",
    )
    endpoint_binding.endpoint_functions.append(endpoint_function_binding)
    session.imap_add(
        ServiceConfigApi(
            id=service_config_api_id,
            service_config_id=service_config_id,
            api_id=uuid4(),
            description="Shared API bridge",
        )
    )
    session.imap_add(
        ServiceOperationConfig(
            id=service_operation_config_id,
            service_config_id=service_config_id,
            name="open_door",
            description="Open one door",
        )
    )
    session.imap_add(endpoint_binding)
    session.imap_add(endpoint_function_binding)

    dispatch_plan = _dispatch_plan(
        api_capability_endpoint_id=api_capability_endpoint_id,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        fulfillment_name="open",
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )
    validated = validate_service_api_fulfillment_contract(
        session=session,
        resolved_dispatch=resolved,
    )

    assert (
        validated.candidate.service_operation_config_api_endpoint_id
        == endpoint_binding_id
    )
    assert len(validated.bindings) == 1
    assert (
        validated.bindings[0].service_operation_config_api_endpoint_function_id
        == endpoint_function_binding_id
    )
    assert (
        validated.bindings[0].api_capability_endpoint_function_id
        == api_capability_endpoint_function_id
    )


def test_build_service_api_graph_execution_plan_carries_validated_ids_and_graph_metadata() -> (
    None
):
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_config_api_id = uuid4()
    service_operation_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    endpoint_binding_id = uuid4()
    api_capability_endpoint_function_id = uuid4()
    endpoint_function_binding_id = uuid4()
    service_operation_id = uuid4()
    service_id = uuid4()

    endpoint_binding = ServiceOperationConfigApiEndpoint(
        id=endpoint_binding_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        description="Public endpoint",
    )
    endpoint_function_binding = ServiceOperationConfigApiEndpointFunction(
        id=endpoint_function_binding_id,
        service_operation_config_api_endpoint_id=endpoint_binding_id,
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
        description="Allowed API fulfillment",
    )
    endpoint_binding.endpoint_functions.append(endpoint_function_binding)
    session.imap_add(
        ServiceConfigApi(
            id=service_config_api_id,
            service_config_id=service_config_id,
            api_id=uuid4(),
            description="Shared API bridge",
        )
    )
    session.imap_add(
        ServiceOperationConfig(
            id=service_operation_config_id,
            service_config_id=service_config_id,
            name="open_door",
            description="Open one door",
        )
    )
    session.imap_add(endpoint_binding)
    session.imap_add(endpoint_function_binding)

    dispatch_plan = _dispatch_plan(
        api_capability_endpoint_id=api_capability_endpoint_id,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        fulfillment_name="open",
        api_capability_endpoint_function_id=api_capability_endpoint_function_id,
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )
    validated = validate_service_api_fulfillment_contract(
        session=session,
        resolved_dispatch=resolved,
    )
    execution_plan = build_service_api_graph_execution_plan(
        dispatch_plan=dispatch_plan,
        materialized_operation_binding=MaterializedServiceOperationBinding(
            service_operation_id=service_operation_id,
            service_operation_config_id=service_operation_config_id,
            service_id=service_id,
            api_call_id=dispatch_plan.envelope.api_call_id,
            api_endpoint_id=endpoint_binding_id,
            operation_key="turn-graph-001",
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="service-proof-projection",
        ),
        validated_fulfillment=validated,
    )

    assert execution_plan.service_operation_id == service_operation_id
    assert execution_plan.service_id == service_id
    assert execution_plan.service_operation_config_id == service_operation_config_id
    assert (
        execution_plan.service_operation_config_api_endpoint_id == endpoint_binding_id
    )
    assert execution_plan.api_call_id == dispatch_plan.envelope.api_call_id
    assert execution_plan.endpoint_ref == dispatch_plan.endpoint_ref
    assert execution_plan.request_object is dispatch_plan.request_object
    assert len(execution_plan.bindings) == 1
    assert (
        execution_plan.bindings[0].service_operation_config_api_endpoint_function_id
        == endpoint_function_binding_id
    )
    assert (
        execution_plan.bindings[0].api_capability_endpoint_function_id
        == api_capability_endpoint_function_id
    )
    assert execution_plan.bindings[0].graph_target == "aware_home"
    assert execution_plan.bindings[0].graph_capability_function_name == "open"
    assert (
        execution_plan.bindings[0].graph_function_python_ref
        == "aware_home.home.Door.open"
    )
    assert (
        execution_plan.bindings[0].graph_function_runtime_target
        == "aware_home_ontology.home.home.Door.open"
    )
    assert execution_plan.bindings[0].call_target_kind == "instance"
    assert execution_plan.bindings[0].exact_output_field_name is None


def test_resolve_service_api_dispatch_ignores_missing_function_binding_during_selection() -> (
    None
):
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_config_api_id = uuid4()
    service_operation_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    endpoint_binding_id = uuid4()

    endpoint_binding = ServiceOperationConfigApiEndpoint(
        id=endpoint_binding_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        description="Public endpoint",
    )
    session.imap_add(
        ServiceConfigApi(
            id=service_config_api_id,
            service_config_id=service_config_id,
            api_id=uuid4(),
            description="Shared API bridge",
        )
    )
    session.imap_add(
        ServiceOperationConfig(
            id=service_operation_config_id,
            service_config_id=service_config_id,
            name="open_door",
            description="Open one door",
        )
    )
    session.imap_add(endpoint_binding)

    dispatch_plan = _dispatch_plan(
        api_capability_endpoint_id=api_capability_endpoint_id,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        fulfillment_name="open",
    )
    resolved = resolve_service_api_dispatch(
        session=session, dispatch_plan=dispatch_plan
    )
    candidate = require_single_service_api_dispatch_candidate(
        resolved_dispatch=resolved
    )

    assert candidate.service_config_api_id == service_config_api_id
    assert candidate.service_operation_config_id == service_operation_config_id
    assert candidate.service_operation_config_api_endpoint_id == endpoint_binding_id


def _service_api_dispatch_preflight_session(
    *,
    with_role_requirement: bool = False,
    admission_mode: str = "public_read",
    include_fulfillment: bool = True,
    fulfillment_kind: ServiceOperationFulfillmentKind = (
        ServiceOperationFulfillmentKind.coordination
    ),
) -> tuple[Session, ApiServiceDispatchPlan, UUID, UUID, UUID]:
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_id = uuid4()
    service_config_api_id = uuid4()
    service_operation_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    endpoint_binding_id = uuid4()
    role_config_id = uuid4()

    operation_config = ServiceOperationConfig(
        id=service_operation_config_id,
        service_config_id=service_config_id,
        name="open_door",
        description="Open one door",
        fulfillment_kind=fulfillment_kind,
    )
    object.__setattr__(operation_config, "admission_mode", admission_mode)
    if with_role_requirement:
        operation_config.role_requirements.append(
            ServiceOperationConfigRoleRequirement(
                id=uuid4(),
                service_operation_config_id=service_operation_config_id,
                role_config_id=role_config_id,
                access_scope="operation",
                scope_kind="operation",
                scope_ref="default",
                class_instance_identity_required=False,
                role_assignment_binding_required=True,
                description=None,
            )
        )

    for obj in (
        ServiceConfigApi(
            id=service_config_api_id,
            service_config_id=service_config_id,
            api_id=uuid4(),
            description="Shared API bridge",
        ),
        operation_config,
        ServiceOperationConfigApiEndpoint(
            id=endpoint_binding_id,
            service_operation_config_id=service_operation_config_id,
            service_config_api_id=service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            description="Public endpoint",
        ),
    ):
        session.imap_add(obj)

    return (
        session,
        _dispatch_plan(
            api_capability_endpoint_id=api_capability_endpoint_id,
            request_model_id=uuid4(),
            request_class_config_id=uuid4(),
            fulfillment_name="open",
            include_fulfillment=include_fulfillment,
        ),
        service_id,
        service_operation_config_id,
        role_config_id,
    )


def _subscription(
    *,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    now: datetime,
) -> ServiceSubscription:
    return ServiceSubscription.model_construct(
        id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_id=service_id,
        plan_id=uuid4(),
        contract_id=smart_contract_id,
        external_subscription_handle="sub_test",
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
        cancel_at_period_end=False,
        metadata_json={},
    )


def _service_contract(
    *,
    service_id: UUID,
    service_contract_config_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    now: datetime,
) -> ServiceContract:
    return ServiceContract.model_construct(
        id=uuid4(),
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        commercial_profile_id=uuid4(),
        producer_finance_entity_id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        kind=ServiceContractKind.subscription,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
        status=ServiceContractStatus.active,
        metadata_json={},
    )


def _contract_config(
    *,
    service_contract_config_id: UUID,
    operation_grants: tuple[ServiceContractConfigOperationGrant, ...],
) -> ServiceContractConfig:
    return ServiceContractConfig.model_construct(
        id=service_contract_config_id,
        service_config_id=uuid4(),
        name="Default contract",
        default_kind=ServiceContractKind.subscription,
        projection_experience_id=None,
        description=None,
        metadata_json={},
        operation_grants=list(operation_grants),
        actor_role_grants=[],
    )


def _operation_grant(
    *,
    service_contract_config_id: UUID,
    service_operation_config_id: UUID,
    include_typed_policies: bool = False,
) -> ServiceContractConfigOperationGrant:
    operation_grant_id = uuid4()
    quota_policy = None
    permit_policy = None
    price_policy = None
    if include_typed_policies:
        quota_policy = ServiceContractOperationQuotaPolicy.model_construct(
            id=uuid4(),
            service_contract_config_operation_grant_id=operation_grant_id,
            unit=ServiceContractOperationQuotaUnit.request,
            limit_amount=42,
            window=ServiceContractOperationQuotaWindow.hour,
            burst_limit=7,
            over_limit_behavior=ServiceContractOperationQuotaOverLimitBehavior.throttle,
            fail_closed=True,
        )
        permit_policy = ServiceContractOperationPermitPolicy.model_construct(
            id=uuid4(),
            service_contract_config_operation_grant_id=operation_grant_id,
            requires_active_contract=True,
            requires_smart_contract_permit=True,
            requires_reservation_before_execute=True,
            permit_scope=ServiceContractOperationPermitScope.session,
            idempotency_scope=(
                ServiceContractOperationPermitIdempotencyScope.operation_nonce
            ),
            fail_closed=True,
        )
        price_policy = ServiceContractOperationPricePolicy.model_construct(
            id=uuid4(),
            service_contract_config_operation_grant_id=operation_grant_id,
            price_source=ServiceContractOperationPriceSource.contract_override,
            price_id=uuid4(),
            price_ref="price://workspace/session",
            pricing_policy_id=uuid4(),
            pricing_policy_ref="pricing://agent",
            settlement_policy_override=(
                ServiceOperationSettlementPolicy.reserve_before_execute
            ),
            max_cost_required=True,
            quote_ttl_s=300,
            fail_closed=True,
        )
    return ServiceContractConfigOperationGrant.model_construct(
        id=operation_grant_id,
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        quota_policy=quota_policy,
        permit_policy=permit_policy,
        price_policy=price_policy,
        access_scope="operation",
        quota_policy_json={},
        permit_policy_json={},
        price_policy_json={},
        description=None,
    )
