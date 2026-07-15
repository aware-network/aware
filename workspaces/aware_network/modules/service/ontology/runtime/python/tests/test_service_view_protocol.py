from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_actor_role_grant import (
    ServiceContractConfigActorRoleGrant,
)
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_view import (
    ServiceOperationConfigApiView,
)
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_runtime.api_ingress.execution import (
    ServiceActorRoleEvidence,
    ServiceOperationAccessContext,
)
from aware_service_runtime.api_ingress.view_protocol import (
    ServiceViewProtocolBinding,
    build_service_view_protocol_bindings,
    require_service_view_protocol_binding,
    resolve_service_view_protocol_fulfillment,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
)
from aware_service_runtime.view_provider_routes import (
    build_service_view_provider_routes,
    require_service_view_provider_route,
)


def test_service_view_protocol_bindings_compile_from_service_plan() -> None:
    bindings = build_service_view_protocol_bindings(
        compile_plan_payloads=(_service_compile_plan_payload(),)
    )

    binding = require_service_view_protocol_binding(
        bindings=bindings,
        service_name="compiler",
        operation_name="projection_resolution",
        view_ref="actor_identity.roles",
    )

    assert binding.service_name == "compiler"
    assert binding.operation_name == "projection_resolution"
    assert binding.endpoint_refs == (
        "api_anchor.projection_resolution.projection_resolution",
    )
    assert binding.role_refs == ("identity.actor_reader",)
    assert binding.contract_refs == ("actor_subscription",)


def test_service_view_provider_routes_join_view_binding_to_api_route(tmp_path) -> None:
    api_route = ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware_experience_service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware_code_service",
        api_package_id=uuid4(),
        api_package_name="code-service-api",
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id="local-code-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=tmp_path / "aware-code.sock",
        request_timeout_s=30.0,
        service_names=("aware_code",),
        endpoint_refs_by_service={
            "aware_code": ("code.view_state.resolve_package_selector",)
        },
        stream_endpoint_refs_by_service={},
    )
    binding = ServiceViewProtocolBinding(
        service_name="aware_code",
        operation_name="view_state_resolve_package_selector",
        view_ref="aware_code_package.codes.selector.v1",
        endpoint_refs=("code.view_state.resolve_package_selector",),
        role_refs=(),
        contract_refs=(),
        source_path="bindings/code.services.aware",
    )

    routes = build_service_view_provider_routes(
        bindings=(binding,),
        api_dependency_routes=(api_route,),
    )
    route = require_service_view_provider_route(
        routes=routes,
        view_ref="aware_code_package.codes.selector.v1",
    )

    assert route.api_route == api_route
    assert route.api_package_name == "code-service-api"
    assert route.endpoint_ref == "code.view_state.resolve_package_selector"
    assert route.provider_context()["host_id"] == "local-code-host"


def test_service_view_provider_routes_accept_view_only_binding(tmp_path) -> None:
    api_route = ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware_experience_service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware_code_service",
        api_package_id=uuid4(),
        api_package_name="code-service-api",
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id="local-code-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=tmp_path / "aware-code.sock",
        request_timeout_s=30.0,
        service_names=("aware_code",),
        endpoint_refs_by_service={},
        stream_endpoint_refs_by_service={},
    )
    binding = ServiceViewProtocolBinding(
        service_name="aware_code",
        operation_name="package_selector_view",
        view_ref="aware_code_package.codes.selector.v1",
        endpoint_refs=(),
        role_refs=(),
        contract_refs=(),
        source_path="bindings/code.services.aware",
    )

    routes = build_service_view_provider_routes(
        bindings=(binding,),
        api_dependency_routes=(api_route,),
    )
    route = require_service_view_provider_route(
        routes=routes,
        view_ref="aware_code_package.codes.selector.v1",
    )

    assert route.api_route == api_route
    assert route.endpoint_ref is None
    provider_context = route.provider_context()
    assert provider_context["api_view_ref"] == "aware_code_package.codes.selector.v1"
    assert "endpoint_ref" not in provider_context


def test_service_view_protocol_resolves_runtime_fulfillment() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    role_config_id = uuid4()
    actor_id = uuid4()
    role_assignment_binding_id = uuid4()
    context = _service_view_protocol_context(
        role_config_id=role_config_id,
        now=now,
    )

    fulfillment = resolve_service_view_protocol_fulfillment(
        session=context.session,
        service_id=context.service_id,
        binding=context.binding,
        actor_id=actor_id,
        operation_access_context=context.operation_access_context,
        actor_role_evidence=(
            _actor_role_evidence(
                actor_id=actor_id,
                role_config_id=role_config_id,
                role_assignment_binding_id=role_assignment_binding_id,
            ),
        ),
    )

    assert fulfillment.binding == context.binding
    assert fulfillment.plan.service_operation_config_id == context.operation_config_id
    assert (
        fulfillment.plan.service_operation_config_api_view_id == context.view_binding_id
    )
    assert (
        fulfillment.plan.preflight.access_evidence is not None
        and fulfillment.plan.preflight.access_evidence.service_contract_config_operation_grant_id
        == context.operation_grant_id
    )
    assert (
        fulfillment.plan.preflight.actor_role_evidence[0].role_config_id
        == role_config_id
    )
    assert fulfillment.service_contract_config_actor_role_grant_ids == (
        context.actor_role_grant_id,
    )


def test_service_view_protocol_fails_closed_without_operation_grant() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    role_config_id = uuid4()
    actor_id = uuid4()
    context = _service_view_protocol_context(
        role_config_id=role_config_id,
        now=now,
        include_operation_grant=False,
    )

    with pytest.raises(PermissionError, match="operation grant"):
        resolve_service_view_protocol_fulfillment(
            session=context.session,
            service_id=context.service_id,
            binding=context.binding,
            actor_id=actor_id,
            operation_access_context=context.operation_access_context,
            actor_role_evidence=(
                _actor_role_evidence(
                    actor_id=actor_id,
                    role_config_id=role_config_id,
                    role_assignment_binding_id=uuid4(),
                ),
            ),
        )


def test_service_view_protocol_fails_closed_without_actor_role_evidence() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    role_config_id = uuid4()
    context = _service_view_protocol_context(
        role_config_id=role_config_id,
        now=now,
    )

    with pytest.raises(PermissionError, match="ActorRole"):
        resolve_service_view_protocol_fulfillment(
            session=context.session,
            service_id=context.service_id,
            binding=context.binding,
            actor_id=uuid4(),
            operation_access_context=context.operation_access_context,
        )


def test_service_view_protocol_fails_closed_without_contract_actor_role_grant() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    role_config_id = uuid4()
    actor_id = uuid4()
    context = _service_view_protocol_context(
        role_config_id=role_config_id,
        now=now,
        include_actor_role_grant=False,
    )

    with pytest.raises(PermissionError, match="ActorRole grant"):
        resolve_service_view_protocol_fulfillment(
            session=context.session,
            service_id=context.service_id,
            binding=context.binding,
            actor_id=actor_id,
            operation_access_context=context.operation_access_context,
            actor_role_evidence=(
                _actor_role_evidence(
                    actor_id=actor_id,
                    role_config_id=role_config_id,
                    role_assignment_binding_id=uuid4(),
                ),
            ),
        )


class _ServiceViewProtocolContext:
    def __init__(
        self,
        *,
        session: Session,
        binding: ServiceViewProtocolBinding,
        service_id: UUID,
        operation_config_id: UUID,
        view_binding_id: UUID,
        operation_grant_id: UUID,
        actor_role_grant_id: UUID,
        operation_access_context: ServiceOperationAccessContext,
    ) -> None:
        self.session = session
        self.binding = binding
        self.service_id = service_id
        self.operation_config_id = operation_config_id
        self.view_binding_id = view_binding_id
        self.operation_grant_id = operation_grant_id
        self.actor_role_grant_id = actor_role_grant_id
        self.operation_access_context = operation_access_context


def _service_view_protocol_context(
    *,
    role_config_id: UUID,
    now: datetime,
    include_operation_grant: bool = True,
    include_actor_role_grant: bool = True,
) -> _ServiceViewProtocolContext:
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_id = uuid4()
    operation_config_id = uuid4()
    service_config_api_id = uuid4()
    api_view_id = uuid4()
    view_binding_id = uuid4()
    service_contract_config_id = uuid4()
    operation_grant_id = uuid4()
    actor_role_grant_id = uuid4()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()

    operation_config = ServiceOperationConfig(
        id=operation_config_id,
        service_config_id=service_config_id,
        name="projection_resolution",
        description=None,
    )
    operation_config.role_requirements.append(
        ServiceOperationConfigRoleRequirement(
            id=uuid4(),
            service_operation_config_id=operation_config_id,
            role_config_id=role_config_id,
            access_scope="operation",
            scope_kind="operation",
            scope_ref="projection_resolution",
            class_instance_identity_required=True,
            role_assignment_binding_required=True,
            description=None,
        )
    )
    view_binding = ServiceOperationConfigApiView(
        id=view_binding_id,
        service_operation_config_id=operation_config_id,
        service_config_api_id=service_config_api_id,
        api_view_id=api_view_id,
        description=None,
    )
    for obj in (
        Service(
            id=service_id,
            service_config_id=service_config_id,
            name="compiler",
            description=None,
        ),
        operation_config,
        view_binding,
    ):
        session.imap_add(obj)

    operation_grants = (
        [
            ServiceContractConfigOperationGrant.model_construct(
                id=operation_grant_id,
                service_contract_config_id=service_contract_config_id,
                service_operation_config_id=operation_config_id,
                access_scope="operation",
                quota_policy_json={},
                permit_policy_json={},
                price_policy_json={},
                description=None,
            )
        ]
        if include_operation_grant
        else []
    )
    actor_role_grants = (
        [
            ServiceContractConfigActorRoleGrant.model_construct(
                id=actor_role_grant_id,
                service_contract_config_id=service_contract_config_id,
                role_config_id=role_config_id,
                access_scope="service",
                scope_kind="service",
                scope_ref="default",
                class_instance_identity_required=False,
                role_assignment_binding_required=True,
                grant_policy_json={},
                description=None,
            )
        ]
        if include_actor_role_grant
        else []
    )
    contract_config = ServiceContractConfig.model_construct(
        id=service_contract_config_id,
        service_config_id=service_config_id,
        name="actor_subscription",
        default_kind=ServiceContractKind.subscription,
        projection_experience_id=uuid4(),
        description=None,
        metadata_json={},
        operation_grants=operation_grants,
        actor_role_grants=actor_role_grants,
    )
    return _ServiceViewProtocolContext(
        session=session,
        binding=ServiceViewProtocolBinding(
            service_name="compiler",
            operation_name="projection_resolution",
            view_ref="actor_identity.roles",
            endpoint_refs=("api_anchor.projection_resolution.projection_resolution",),
            role_refs=("identity.actor_reader",),
            contract_refs=("actor_subscription",),
            source_path="services/bindings/compiler.services.aware",
        ),
        service_id=service_id,
        operation_config_id=operation_config_id,
        view_binding_id=view_binding_id,
        operation_grant_id=operation_grant_id,
        actor_role_grant_id=actor_role_grant_id,
        operation_access_context=ServiceOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(
                ServiceSubscription.model_construct(
                    id=uuid4(),
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    service_id=service_id,
                    plan_id=uuid4(),
                    contract_id=smart_contract_id,
                    external_subscription_handle="sub_actor_subscription",
                    status=ServiceSubscriptionStatus.active,
                    current_period_start=now - timedelta(days=1),
                    current_period_end=now + timedelta(days=29),
                    cancel_at_period_end=False,
                    metadata_json={},
                ),
            ),
            service_contracts_by_smart_contract_id={
                smart_contract_id: ServiceContract.model_construct(
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
            },
            service_contract_configs_by_id={
                service_contract_config_id: contract_config,
            },
            now=now,
        ),
    )


def _actor_role_evidence(
    *,
    actor_id: UUID,
    role_config_id: UUID,
    role_assignment_binding_id: UUID,
) -> ServiceActorRoleEvidence:
    return ServiceActorRoleEvidence(
        actor_id=actor_id,
        role_config_id=role_config_id,
        access_scope="operation",
        scope_kind="operation",
        scope_ref="projection_resolution",
        class_instance_identity_id=uuid4(),
        role_assignment_binding_id=role_assignment_binding_id,
    )


def _service_compile_plan_payload() -> dict[str, object]:
    return {
        "package_name": "compiler-service",
        "fqn_prefix": "aware_compiler_service",
        "service_configs": [
            {
                "name": "compiler",
                "source_path": "services/bindings/compiler.services.aware",
                "apis": [],
                "experiences": [
                    {
                        "experience_ref": "actor_identity",
                        "source_path": "services/bindings/compiler.services.aware",
                    }
                ],
                "service_operation_configs": [
                    {
                        "name": "projection_resolution",
                        "source_path": "services/bindings/compiler.services.aware",
                        "settlement_policy": "none",
                        "price": None,
                        "price_ref": None,
                        "api_endpoints": [
                            {
                                "endpoint_ref": (
                                    "api_anchor.projection_resolution.projection_resolution"
                                ),
                                "api_ref": "api_anchor",
                                "source_path": "services/bindings/compiler.services.aware",
                            }
                        ],
                        "api_views": [
                            {
                                "view_ref": "actor_identity.roles",
                                "source_path": "services/bindings/compiler.services.aware",
                            }
                        ],
                        "role_requirements": [
                            {
                                "role_ref": "identity.actor_reader",
                                "access_scope": "operation",
                                "scope_kind": "operation",
                                "scope_ref": "projection_resolution",
                                "class_instance_identity_required": True,
                                "role_assignment_binding_required": True,
                                "source_path": "services/bindings/compiler.services.aware",
                            }
                        ],
                    }
                ],
                "contract_configs": [
                    {
                        "name": "actor_subscription",
                        "source_path": "services/bindings/compiler.services.aware",
                        "default_kind": "subscription",
                        "projection_experience_ref": "actor_identity",
                        "operation_grants": [
                            {
                                "operation_ref": "projection_resolution",
                                "access_scope": "operation",
                                "source_path": "services/bindings/compiler.services.aware",
                            }
                        ],
                        "actor_role_grants": [
                            {
                                "role_ref": "identity.actor_reader",
                                "access_scope": "service",
                                "scope_kind": "service",
                                "scope_ref": "default",
                                "class_instance_identity_required": False,
                                "role_assignment_binding_required": True,
                                "source_path": "services/bindings/compiler.services.aware",
                            }
                        ],
                    }
                ],
            }
        ],
    }
