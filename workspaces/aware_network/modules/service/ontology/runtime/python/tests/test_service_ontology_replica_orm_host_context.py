from __future__ import annotations

from uuid import uuid4

from aware_orm.session.current_session_ctx import current_session
from aware_orm.session.session import Session
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    current_service_ontology_replica_orm_session,
    require_service_ontology_replica_orm_session,
)
from aware_service_runtime.contracts import ServiceOperationContext


def test_service_api_host_context_installs_ontology_replica_orm_session() -> None:
    session = Session(skip_db=True)
    operation_context = ServiceOperationContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:projection",
    )

    assert current_service_ontology_replica_orm_session() is None
    assert current_session() is None

    with service_api_host_context(
        operation_context=operation_context,
        graph_gateway=None,
        ontology_replica_orm_session=session,
    ):
        assert current_service_ontology_replica_orm_session() is session
        assert require_service_ontology_replica_orm_session() is session
        assert current_session() is session

    assert current_service_ontology_replica_orm_session() is None
    assert current_session() is None


def test_require_service_ontology_replica_orm_session_requires_context() -> None:
    try:
        require_service_ontology_replica_orm_session()
    except RuntimeError as exc:
        assert "ontology replica ORM projection" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("require_service_ontology_replica_orm_session must fail")
