from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from aware_service_service.activation.registry import (
    ActivatedServiceImplementationPackage,
    ontology_package_requirements_for_activated_package,
)
from aware_service_service.ontology.replica.gateway import (
    required_ontology_replica_fqn_prefixes,
)
from aware_service_service.ontology.replica.projector import (
    ServiceOntologyCommitSource,
    ServiceOntologyProjectionStore,
)
from aware_service_service.ontology.replica.state import (
    ServiceOntologyReplicaStateStore,
)
from aware_service_service.ontology.replica.worker import (
    EnvironmentCommitReceiptSdkClient,
    ServiceOntologyReplicaWorker,
    service_ontology_replica_subscription_specs_from_bindings,
)


class HostedRuntimeContextResolver(Protocol):
    async def __call__(self) -> Any: ...


CommitSourceFactory = Callable[[UUID], ServiceOntologyCommitSource]


async def start_service_ontology_replica_worker_if_needed(
    *,
    current_worker: ServiceOntologyReplicaWorker | None,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
    state_db_path: Path | None,
    projection_db_path: Path | None,
    resolve_runtime_context: HostedRuntimeContextResolver,
    commit_source_factory: CommitSourceFactory,
    environment_api_client: EnvironmentCommitReceiptSdkClient,
) -> ServiceOntologyReplicaWorker | None:
    if current_worker is not None:
        return current_worker
    if state_db_path is None:
        return None

    subscription_specs = service_ontology_replica_subscription_specs_from_bindings(
        packages=packages,
    )
    requires_ontology_replica = any(
        required_ontology_replica_fqn_prefixes(
            requirements=ontology_package_requirements_for_activated_package(activated)
        )
        for activated in packages
    )
    if not subscription_specs and not requires_ontology_replica:
        return None

    runtime_context = await resolve_runtime_context()
    environment_id = runtime_context.environment_config_id
    store = await ServiceOntologyReplicaStateStore.open(
        db_path=state_db_path,
        environment_id=environment_id,
    )
    projection_store = (
        ServiceOntologyProjectionStore.open(db_path=projection_db_path)
        if projection_db_path is not None
        else None
    )
    worker = ServiceOntologyReplicaWorker(
        store=store,
        subscriptions=subscription_specs,
        commit_source=(
            commit_source_factory(environment_id)
            if projection_store is not None
            else None
        ),
        projection_store=projection_store,
    )
    await worker.start(environment_api_client=environment_api_client)
    return worker


async def stop_service_ontology_replica_worker(
    *,
    worker: ServiceOntologyReplicaWorker | None,
) -> None:
    if worker is None:
        return
    await worker.stop()


__all__ = [
    "CommitSourceFactory",
    "HostedRuntimeContextResolver",
    "start_service_ontology_replica_worker_if_needed",
    "stop_service_ontology_replica_worker",
]
