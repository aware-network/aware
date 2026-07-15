from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from _service_runtime_test_paths import REPO_ROOT


_SERVICE_META_HANDLERS_ANY: Any = service_meta_handlers
_SERVICE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SERVICE_META_HANDLERS_ANY,
)
_SERVICE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SERVICE_META_HANDLERS_ANY,
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
        _ = exc_type, exc, tb
        for key, previous in self._env_overrides.items():
            if previous is None:
                _ = os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _service_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_meta_runtime(repo_root: Path, *, workspace_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=workspace_root,
        handler_modules=(_SERVICE_META_HANDLER_MODULE,),
        bootstrap_modules=(_SERVICE_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _has_meta_handler(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in service_meta_handlers.AWARE_META_GRAPH_HANDLERS
    )


def _has_empty_lane_bootstrap(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in service_meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
    )


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
async def test_service_contract_operation_policy_meta_runtime_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401
    from aware_service_ontology.service.service_config import ServiceConfig
    from aware_service_ontology.service.service_enums import (
        ServiceContractOperationPermitIdempotencyScope,
        ServiceContractOperationPermitScope,
        ServiceContractOperationPriceSource,
        ServiceContractOperationQuotaOverLimitBehavior,
        ServiceContractOperationQuotaUnit,
        ServiceContractOperationQuotaWindow,
    )
    from aware_service_ontology.stable_ids import (
        stable_service_config_id,
        stable_service_contract_config_id,
        stable_service_contract_config_operation_grant_id,
        stable_service_contract_operation_permit_policy_id,
        stable_service_contract_operation_price_policy_id,
        stable_service_contract_operation_quota_policy_id,
        stable_service_operation_config_id,
    )

    service_config_name = "compiler"
    operation_config_name = "compile_module"
    contract_config_name = "default"

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_operation_config_id = stable_service_operation_config_id(
        service_config_id=expected_service_config_id,
        name=operation_config_name,
    )
    expected_contract_config_id = stable_service_contract_config_id(
        service_config_id=expected_service_config_id,
        name=contract_config_name,
    )
    expected_operation_grant_id = stable_service_contract_config_operation_grant_id(
        service_contract_config_id=expected_contract_config_id,
        service_operation_config_id=expected_operation_config_id,
    )
    expected_quota_policy_id = stable_service_contract_operation_quota_policy_id(
        service_contract_config_operation_grant_id=expected_operation_grant_id,
    )
    expected_permit_policy_id = stable_service_contract_operation_permit_policy_id(
        service_contract_config_operation_grant_id=expected_operation_grant_id,
    )
    expected_price_policy_id = stable_service_contract_operation_price_policy_id(
        service_contract_config_operation_grant_id=expected_operation_grant_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ServiceConfig",
            branch_id=uuid5(NAMESPACE_URL, "service://tests/policy/branch"),
        )
        with lane.activate(commit=True, publish=False):
            service_config = await ServiceConfig.build(
                name=service_config_name,
                description="Compiler service catalog",
            )

        with lane.activate(commit=True, publish=False):
            operation_config = await service_config.create_service_operation_config(
                name=operation_config_name,
                description="Compile one module",
            )

        with lane.activate(commit=True, publish=False):
            contract_config = await service_config.create_contract_config(
                name=contract_config_name,
                description="Default commercial contract",
            )

        with lane.activate(commit=True, publish=False):
            operation_grant = await contract_config.grant_operation(
                service_operation_config_id=expected_operation_config_id,
                access_scope="operation",
                description="Compile operation access",
            )

        with lane.activate(commit=True, publish=False):
            quota_policy = await operation_grant.configure_quota_policy(
                unit=ServiceContractOperationQuotaUnit.request,
                limit_amount=100,
                window=ServiceContractOperationQuotaWindow.day,
                burst_limit=10,
                over_limit_behavior=(
                    ServiceContractOperationQuotaOverLimitBehavior.throttle
                ),
                fail_closed=True,
            )

        with lane.activate(commit=True, publish=False):
            permit_policy = await operation_grant.configure_permit_policy(
                requires_active_contract=True,
                requires_smart_contract_permit=False,
                requires_reservation_before_execute=True,
                permit_scope=ServiceContractOperationPermitScope.operation,
                idempotency_scope=(
                    ServiceContractOperationPermitIdempotencyScope.request_hash
                ),
                fail_closed=True,
            )

        with lane.activate(commit=True, publish=False):
            price_policy = await operation_grant.configure_price_policy(
                price_source=(ServiceContractOperationPriceSource.operation_default),
                price_ref="price:compile-module",
                pricing_policy_ref="pricing:standard",
                max_cost_required=True,
                quote_ttl_s=60,
                fail_closed=True,
            )

        assert service_config.id == expected_service_config_id
        assert operation_config.id == expected_operation_config_id
        assert contract_config.id == expected_contract_config_id
        assert operation_grant.id == expected_operation_grant_id
        assert quota_policy.id == expected_quota_policy_id
        assert permit_policy.id == expected_permit_policy_id
        assert price_policy.id == expected_price_policy_id
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(expected_service_config_id)
    assertions.expect_instance(expected_service_config_id)
    assertions.expect_instance(expected_operation_config_id)
    assertions.expect_instance(expected_contract_config_id)
    assertions.expect_instance(expected_operation_grant_id)
    assertions.expect_instance(expected_quota_policy_id)
    assertions.expect_instance(expected_permit_policy_id)
    assertions.expect_instance(expected_price_policy_id)
    assertions.expect_edge(
        source_id=expected_service_config_id,
        target_id=expected_operation_config_id,
        relationship_name="service_operation_configs",
    )
    assertions.expect_edge(
        source_id=expected_service_config_id,
        target_id=expected_contract_config_id,
        relationship_name="contract_configs",
    )
    assertions.expect_edge(
        source_id=expected_contract_config_id,
        target_id=expected_operation_grant_id,
        relationship_name="operation_grants",
    )
    assertions.expect_edge(
        source_id=expected_operation_grant_id,
        target_id=expected_quota_policy_id,
        relationship_name="quota_policy",
    )
    assertions.expect_edge(
        source_id=expected_operation_grant_id,
        target_id=expected_permit_policy_id,
        relationship_name="permit_policy",
    )
    assertions.expect_edge(
        source_id=expected_operation_grant_id,
        target_id=expected_price_policy_id,
        relationship_name="price_policy",
    )
    assertions.expect_primitive(
        instance_id=expected_quota_policy_id,
        field_name="limit_amount",
        expected=100,
    )
    assertions.expect_primitive(
        instance_id=expected_quota_policy_id,
        field_name="unit",
        expected=ServiceContractOperationQuotaUnit.request.value,
    )
    assertions.expect_primitive(
        instance_id=expected_permit_policy_id,
        field_name="requires_reservation_before_execute",
        expected=True,
    )
    assertions.expect_primitive(
        instance_id=expected_price_policy_id,
        field_name="price_ref",
        expected="price:compile-module",
    )
    assertions.expect_primitive(
        instance_id=expected_price_policy_id,
        field_name="max_cost_required",
        expected=True,
    )


@pytest.mark.asyncio
async def test_service_package_ontology_requirement_meta_runtime_proof(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_service_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import stable_api_package_id
    from aware_ontology_ontology.stable_ids import stable_ontology_package_id
    from aware_service_ontology.service.service_package import ServicePackage
    from aware_service_ontology.stable_ids import (
        stable_service_package_id,
        stable_service_package_ontology_package_id,
        stable_service_package_required_api_package_id,
    )

    service_package_name = "aware-environment-service"
    service_config_id = uuid5(
        NAMESPACE_URL,
        "service://tests/package-ontology/service-config",
    )
    ontology_package_id = stable_ontology_package_id(
        name="identity-ontology",
        fqn_prefix="aware_identity",
    )
    required_api_package_id = stable_api_package_id(
        name="meta-service-api",
    )
    expected_service_package_id = stable_service_package_id(
        name=service_package_name,
    )
    expected_ontology_bridge_id = stable_service_package_ontology_package_id(
        service_package_id=expected_service_package_id,
        ontology_package_id=ontology_package_id,
    )
    expected_required_api_bridge_id = stable_service_package_required_api_package_id(
        service_package_id=expected_service_package_id,
        api_package_id=required_api_package_id,
    )

    generated_source = Path(service_meta_handlers.__file__).read_text(
        encoding="utf-8",
    )
    assert "aware_runtime.testing" not in generated_source
    assert _has_meta_handler(
        owner_key="aware_service.service.ServicePackage",
        function_name="attach_ontology_package",
    )
    assert _has_meta_handler(
        owner_key="aware_service.service.ServicePackage",
        function_name="attach_provided_api_package",
    )
    assert _has_meta_handler(
        owner_key="aware_service.service.ServicePackage",
        function_name="attach_required_api_package",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_service.service.ServicePackageOntologyPackage",
        function_name="build_via_service_package",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_service.service.ServicePackageProvidedApiPackage",
        function_name="build_via_service_package",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_service.service.ServicePackageRequiredApiPackage",
        function_name="build_via_service_package",
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="ServicePackage",
            branch_id=uuid5(
                NAMESPACE_URL,
                "service://tests/package-ontology/branch",
            ),
        )
        with lane.activate(commit=True, publish=False):
            service_package = await ServicePackage.build(
                name=service_package_name,
                service_config_id=service_config_id,
                fqn_prefix="aware_environment_service",
                manifest_relative_path="services/environment/aware.service.toml",
                package_root="services/environment",
                sources_root="bindings",
                compilation_mode="service_ontology",
                service_surface="service",
                activation_mode="materialize_and_load_committed",
                materialize_on_start=False,
            )

        with lane.activate(commit=True, publish=False):
            required_api_package = await service_package.attach_required_api_package(
                api_package_id=required_api_package_id,
                description="Meta service API invocation dependency.",
            )

        with lane.activate(commit=True, publish=False):
            ontology_package = await service_package.attach_ontology_package(
                ontology_package_id=ontology_package_id,
                package_name="identity-ontology",
                fqn_prefix="aware_identity",
                role="replica",
                requirement_mode="required",
                expected_hash_sha256=(
                    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                ),
                description="Identity ontology replica required for service reads.",
            )

        assert service_package.id == expected_service_package_id
        assert required_api_package.id == expected_required_api_bridge_id
        assert ontology_package.id == expected_ontology_bridge_id
        assert lane.last_response is not None
        assert lane.last_response.root_object_id == expected_service_package_id
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(expected_service_package_id)
    assertions.expect_instance(expected_service_package_id)
    assertions.expect_instance(expected_required_api_bridge_id)
    assertions.expect_instance(expected_ontology_bridge_id)
    assertions.expect_edge(
        source_id=expected_service_package_id,
        target_id=expected_required_api_bridge_id,
        relationship_name="required_api_packages",
    )
    assertions.expect_edge(
        source_id=expected_service_package_id,
        target_id=expected_ontology_bridge_id,
        relationship_name="ontology_packages",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=expected_required_api_bridge_id,
        field_name="api_package_id",
        expected=required_api_package_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=expected_ontology_bridge_id,
        field_name="ontology_package_id",
        expected=ontology_package_id,
    )
    assertions.expect_primitive(
        instance_id=expected_ontology_bridge_id,
        field_name="package_name",
        expected="identity-ontology",
    )
    assertions.expect_primitive(
        instance_id=expected_ontology_bridge_id,
        field_name="fqn_prefix",
        expected="aware_identity",
    )
    assertions.expect_primitive(
        instance_id=expected_ontology_bridge_id,
        field_name="role",
        expected="replica",
    )
    assertions.expect_primitive(
        instance_id=expected_ontology_bridge_id,
        field_name="requirement_mode",
        expected="required",
    )
