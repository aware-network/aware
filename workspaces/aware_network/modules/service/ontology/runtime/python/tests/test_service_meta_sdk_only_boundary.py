from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest
from _service_runtime_test_paths import REPO_ROOT
from aware_service_runtime.api_ingress.execution_context import (
    ServiceApiExecutionBackendMode,
    build_service_api_execution_backend,
)
from aware_service_runtime.api_ingress.graph_execution import (
    ServiceApiGraphExecutionPlan,
)
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceOperationContext,
)


_REPO_ROOT = REPO_ROOT
_SERVICE_RUNTIME_ROOT = (
    _REPO_ROOT
    / "workspaces"
    / "aware_network"
    / "modules"
    / "service"
    / "ontology"
    / "runtime"
    / "python"
    / "aware_service_runtime"
)


def _read(relative_path: str) -> str:
    return (_SERVICE_RUNTIME_ROOT / relative_path).read_text(encoding="utf-8")


def test_latest_service_api_execution_boundary_has_no_runtime_index_rail() -> None:
    checked_paths = (
        "api_ingress/__init__.py",
        "api_ingress/execution_context.py",
        "api_ingress/execution.py",
        "api_ingress/gateway_execution.py",
        "api_ingress/host_context.py",
        "api_ingress/target_resolution.py",
    )
    prohibited_terms = (
        "AwareRuntimeIndex",
        "runtime_index",
        "invoke_function_with_index",
        "ontology_facade",
        "resolve_graph_context",
        "from aware_runtime",
        "import aware_runtime",
    )

    for relative_path in checked_paths:
        source = _read(relative_path)
        for term in prohibited_terms:
            assert term not in source, f"{term!r} leaked through {relative_path}"


def test_service_graph_gateway_contract_is_structural_graph_context() -> None:
    contracts_source = _read("contracts.py")
    host_context_source = _read("api_ingress/host_context.py")
    resolver_source = _read("api_ingress/target_resolution.py")
    gateway_contract_source = contracts_source[
        contracts_source.index("class ServiceGraphGateway") : contracts_source.index(
            "class MetaTemporalGraphRoute"
        )
    ]

    assert "class ServiceGraphCatalog(Protocol)" in contracts_source
    assert "class ServiceGraphContext(Protocol)" in contracts_source
    assert "class ServiceGraphContextProvider(Protocol)" in contracts_source
    assert "class MetaTemporalGraphRoute(Protocol)" in contracts_source
    assert "ServiceGraphContextLike: TypeAlias" in contracts_source
    assert "resolve_graph_context" not in gateway_contract_source
    assert "invoke_temporal_function" not in gateway_contract_source
    assert "invoke_temporal_instance" not in gateway_contract_source
    assert "aware_environment_service_dto" not in gateway_contract_source
    assert "graph_context: ServiceGraphContextLike" in host_context_source
    assert "meta_temporal_graph_route: MetaTemporalGraphRoute" in host_context_source
    assert "def service_graph_catalog(" in resolver_source


def test_legacy_ontology_facade_module_is_not_part_of_latest_ingress() -> None:
    assert not (
        _SERVICE_RUNTIME_ROOT / "api_ingress" / "ontology_execution.py"
    ).exists()


def test_graph_gateway_backend_selection_requires_graph_context() -> None:
    with pytest.raises(RuntimeError, match="requires graph_context"):
        build_service_api_execution_backend(
            execution_plan=ServiceApiGraphExecutionPlan(
                service_operation_id=uuid4(),
                service_id=uuid4(),
                service_operation_config_id=uuid4(),
                service_operation_config_api_endpoint_id=uuid4(),
                api_call_id=uuid4(),
                endpoint_ref="proof.endpoint",
                request_object={},
                bindings=(),
            ),
            backend_mode=ServiceApiExecutionBackendMode.graph_gateway,
            graph_gateway=cast(ServiceGraphGateway, object()),
            operation_context=ServiceOperationContext(
                actor_id=None,
                branch_id=uuid4(),
                projection_hash="proof",
            ),
        )
