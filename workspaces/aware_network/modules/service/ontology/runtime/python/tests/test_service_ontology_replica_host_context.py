from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_service_runtime import implementation_package
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
    service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    current_service_ontology_replica_query,
    require_service_ontology_replica_query,
)
from aware_service_runtime.contracts import ServiceOperationContext


def test_service_api_host_context_carries_ontology_replica_query() -> None:
    query = _ReplicaQuery()
    operation_context = _operation_context()

    assert current_service_ontology_replica_query() is None
    with pytest.raises(RuntimeError, match="ontology replica projection configured"):
        require_service_ontology_replica_query()

    with service_api_host_context(
        operation_context=operation_context,
        graph_gateway=None,
        ontology_replica_query=cast(Any, query),
    ) as host_context:
        assert host_context.ontology_replica_query is query
        assert current_service_api_host_context() is host_context
        assert current_service_ontology_replica_query() is query
        assert require_service_ontology_replica_query() is query

    assert current_service_ontology_replica_query() is None


@pytest.mark.asyncio
async def test_execute_activated_dispatch_forwards_ontology_replica_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = _ReplicaQuery()
    captured: dict[str, object] = {}
    service_id = uuid4()
    handler = object()

    async def _fake_execute_service_api_dispatch_plan(**kwargs: object) -> object:
        captured.update(kwargs)
        return _ExecutionResult()

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        implementation_package,
        "execute_service_api_dispatch_plan",
        _fake_execute_service_api_dispatch_plan,
    )

    result = await implementation_package.execute_activated_service_api_dispatch(
        activated=cast(
            Any,
            SimpleNamespace(
                prepared=SimpleNamespace(service_bindings={"aware_test": handler}),
                service_ids_by_name={"aware_test": service_id},
                service_subscriptions_by_name={},
                experience_reference_branch_ids_by_experience_name={},
            ),
        ),
        runtime=object(),
        index=object(),
        session=object(),
        actor_id=None,
        target_lane=_lane_context(),
        service_package_name="test-service-package",
        service_name="aware_test",
        operation_key="test.operation",
        dispatch_plan=cast(
            Any,
            SimpleNamespace(endpoint_ref="test.endpoint", build_execution=None),
        ),
        ontology_replica_query=cast(Any, query),
    )

    assert isinstance(result, _ExecutionResult)
    assert captured["service_id"] == service_id
    assert captured["handler"] is handler
    assert captured["ontology_replica_query"] is query


@pytest.mark.asyncio
async def test_execute_activated_dispatch_request_forwards_ontology_replica_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = _ReplicaQuery()
    dispatch_plan = SimpleNamespace(endpoint_ref="test.endpoint")
    captured: dict[str, object] = {}

    def _fake_rebuild_activated_service_api_dispatch_plan(**kwargs: object) -> object:
        return dispatch_plan

    async def _fake_execute_activated_service_api_dispatch(**kwargs: object) -> object:
        captured.update(kwargs)
        return _ExecutionResult()

    monkeypatch.setattr(
        implementation_package,
        "_rebuild_activated_service_api_dispatch_plan",
        _fake_rebuild_activated_service_api_dispatch_plan,
    )
    monkeypatch.setattr(
        implementation_package,
        "execute_activated_service_api_dispatch",
        _fake_execute_activated_service_api_dispatch,
    )

    result = (
        await implementation_package.execute_activated_service_api_dispatch_request(
            activated=cast(Any, object()),
            runtime=object(),
            index=object(),
            session=object(),
            actor_id=None,
            target_lane=_lane_context(),
            service_name="aware_test",
            dispatch_request=cast(Any, SimpleNamespace(operation_key="test.operation")),
            ontology_replica_query=cast(Any, query),
        )
    )

    assert isinstance(result, _ExecutionResult)
    assert captured["dispatch_plan"] is dispatch_plan
    assert captured["operation_key"] == "test.operation"
    assert captured["ontology_replica_query"] is query


class _ReplicaQuery:
    pass


class _ExecutionResult:
    pass


def _operation_context() -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:test",
    )


def _lane_context() -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:test",
    )
