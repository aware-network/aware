from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_service_runtime.contracts import ServiceGraphGateway
from aware_utils.logging import logger

from aware_service_service.activation.registry import (
    ActivatedServiceImplementationPackage,
    ontology_package_requirements_for_activated_package,
)
from aware_service_service.ontology.replica.worker import ServiceOntologyReplicaWorker
from aware_service_service.ontology.replica.state import (
    ServiceOntologyReplicaCommitReceipt,
)


@dataclass(frozen=True, slots=True)
class OntologyReplicaMirroringGraphGateway(ServiceGraphGateway):
    inner: ServiceGraphGateway
    worker: ServiceOntologyReplicaWorker
    service_package_id: UUID | None
    service_name: str | None
    ontology_fqn_prefixes: frozenset[str]

    async def mirror_committed_lane(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        actor_id: UUID | None = None,
    ) -> None:
        normalized_projection_hash = str(projection_hash or "").strip()
        if not normalized_projection_hash:
            raise ValueError("projection_hash must be non-empty")
        commit_store = FSCommitStore()
        head = await commit_store.head(
            branch_id=branch_id,
            projection_hash=normalized_projection_hash,
        )
        if head is None or not head.get("commit_id"):
            raise RuntimeError(
                "ServiceHost cannot mirror a committed ontology lane without a head: "
                f"branch_id={branch_id} projection_hash={normalized_projection_hash!r}"
            )
        commits = await _unprojected_commit_ancestry(
            commit_store=commit_store,
            worker=self.worker,
            branch_id=branch_id,
            projection_hash=normalized_projection_hash,
            head_commit_id=UUID(str(head["commit_id"])),
        )
        outcomes = []
        for commit in commits:
            receipt = _receipt_from_local_commit(
                commit=commit,
                branch_id=branch_id,
                projection_hash=normalized_projection_hash,
                actor_id=actor_id,
            )
            outcomes.extend(
                await self.worker.handle_local_commit_receipt(
                    receipt=receipt,
                    service_package_id=self.service_package_id,
                    service_name=self.service_name,
                )
            )
        failed = tuple(outcome for outcome in outcomes if outcome.status != "applied")
        if failed:
            raise RuntimeError(
                "ServiceHost local ontology replica mirror failed for committed lane: "
                f"service_name={self.service_name!r} branch_id={branch_id} "
                f"projection_hash={normalized_projection_hash!r} "
                f"statuses={[outcome.status for outcome in failed]!r}"
            )

    async def invoke_function(
        self,
        *,
        request: MetaGraphInvokeFunctionRequest,
        graph_context: object | None = None,
    ) -> MetaGraphInvokeFunctionResponse:
        response = await self.inner.invoke_function(
            request=request,
            graph_context=graph_context,
        )
        skip_reason = ontology_replica_mirror_skip_reason(
            response=response,
            request=request,
            ontology_fqn_prefixes=self.ontology_fqn_prefixes,
        )
        if skip_reason is None:
            outcomes = await self.worker.handle_local_invoke_response(
                request=request,
                response=response,
                service_package_id=self.service_package_id,
                service_name=self.service_name,
            )
            failed = tuple(
                outcome for outcome in outcomes if outcome.status != "applied"
            )
            if failed:
                raise RuntimeError(
                    "ServiceHost local ontology replica mirror failed for committed "
                    "invoke response: "
                    f"service_name={self.service_name!r} "
                    f"branch_id={response.domain_branch_id} "
                    f"projection_hash={response.domain_projection_hash!r} "
                    f"commit_id={response.domain_commit_id} "
                    f"statuses={[outcome.status for outcome in failed]!r}"
                )
        else:
            logger.info(
                "ServiceHost local ontology replica mirror skipped "
                "service_name=%s reason=%s status=%s branch_id=%s "
                "projection_hash=%s commit_id=%s oig_commit_id=%s",
                self.service_name,
                skip_reason,
                response.status,
                response.domain_branch_id or request.domain_branch_id,
                response.domain_projection_hash or request.domain_projection_hash,
                response.domain_commit_id,
                response.object_instance_graph_commit_id,
            )
        return response


def graph_gateway_for_activated_package(
    *,
    base_graph_gateway: ServiceGraphGateway,
    ontology_replica_worker: ServiceOntologyReplicaWorker | None,
    activated_package: ActivatedServiceImplementationPackage,
    service_name: str,
) -> ServiceGraphGateway:
    ontology_replica_prefixes = required_ontology_replica_fqn_prefixes(
        requirements=ontology_package_requirements_for_activated_package(
            activated_package
        )
    )
    if ontology_replica_worker is None or not ontology_replica_prefixes:
        return base_graph_gateway
    logger.info(
        "ServiceHost local ontology replica mirror enabled "
        "service_name=%s prefixes=%s",
        service_name,
        sorted(ontology_replica_prefixes),
    )
    return OntologyReplicaMirroringGraphGateway(
        inner=base_graph_gateway,
        worker=ontology_replica_worker,
        service_package_id=activated_package.service_package_id,
        service_name=service_name,
        ontology_fqn_prefixes=ontology_replica_prefixes,
    )


def invoke_response_targets_required_ontology_replica(
    *,
    response: MetaGraphInvokeFunctionResponse,
    request: MetaGraphInvokeFunctionRequest,
    ontology_fqn_prefixes: frozenset[str],
) -> bool:
    return (
        ontology_replica_mirror_skip_reason(
            response=response,
            request=request,
            ontology_fqn_prefixes=ontology_fqn_prefixes,
        )
        is None
    )


def ontology_replica_mirror_skip_reason(
    *,
    response: MetaGraphInvokeFunctionResponse,
    request: MetaGraphInvokeFunctionRequest,
    ontology_fqn_prefixes: frozenset[str],
) -> str | None:
    if not ontology_fqn_prefixes:
        return "no_required_ontology_replica_prefix"
    status = _enum_or_token_value(response.status)
    if (
        status not in {"succeeded", "success", "ok"}
        or response.domain_commit_id is None
    ):
        return "not_successfully_committed"
    if response.object_instance_graph_commit_id is None:
        return "missing_object_instance_graph_commit_id"
    projection_hash = str(
        response.domain_projection_hash or request.domain_projection_hash or ""
    ).strip()
    if not projection_hash:
        return "missing_projection_hash"
    return None


def required_ontology_replica_fqn_prefixes(
    *,
    requirements: tuple[object, ...],
) -> frozenset[str]:
    prefixes: set[str] = set()
    for requirement in requirements:
        role = _enum_or_token_value(getattr(requirement, "role", None))
        mode = _enum_or_token_value(getattr(requirement, "requirement_mode", None))
        prefix = str(getattr(requirement, "fqn_prefix", "") or "").strip()
        if role == "replica" and mode == "required" and prefix:
            prefixes.add(prefix)
    return frozenset(prefixes)


def _enum_or_token_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    token = str(raw_value or "").strip().casefold()
    if "." in token:
        token = token.rsplit(".", 1)[-1]
    return token


async def _unprojected_commit_ancestry(
    *,
    commit_store: FSCommitStore,
    worker: ServiceOntologyReplicaWorker,
    branch_id: UUID,
    projection_hash: str,
    head_commit_id: UUID,
) -> tuple[object, ...]:
    ordered: list[object] = []
    visited: set[UUID] = set()

    async def visit(commit_id: UUID) -> None:
        if commit_id in visited:
            return
        visited.add(commit_id)
        if worker.projection_store is not None and worker.projection_store.has_commit(
            commit_id=commit_id
        ):
            return
        commit = await commit_store.get_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
        )
        if commit is None:
            raise RuntimeError(
                "ServiceHost cannot replay local ontology lane ancestry because a "
                f"commit is missing: branch_id={branch_id} "
                f"projection_hash={projection_hash!r} commit_id={commit_id}"
            )
        commit_metadata = _value(commit, "commit")
        for parent in tuple(_value(commit_metadata, "commit_parents") or ()):
            parent_commit_id = _uuid_or_none(_value(parent, "parent_commit_id"))
            if parent_commit_id is not None:
                await visit(parent_commit_id)
        ordered.append(commit)

    await visit(head_commit_id)
    return tuple(ordered)


def _receipt_from_local_commit(
    *,
    commit: object,
    branch_id: UUID,
    projection_hash: str,
    actor_id: UUID | None,
) -> ServiceOntologyReplicaCommitReceipt:
    commit_metadata = _value(commit, "commit")
    commit_id = _uuid_or_none(_value(commit_metadata, "id"))
    object_instance_graph_commit_id = _uuid_or_none(_value(commit, "id"))
    if commit_id is None or object_instance_graph_commit_id is None:
        raise RuntimeError(
            "ServiceHost local ontology commit is missing canonical commit identity: "
            f"branch_id={branch_id} projection_hash={projection_hash!r}"
        )
    return ServiceOntologyReplicaCommitReceipt(
        actor_id=actor_id or _uuid_or_none(_value(commit_metadata, "author_id")),
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        graph_hash_post=_text_or_none(_value(commit, "graph_hash_post")),
        object_instance_graph_id=_uuid_or_none(
            _value(commit, "object_instance_graph_id")
        ),
        root_object_id=_uuid_or_none(_value(commit, "root_source_object_id")),
        operation_label="service_host.local_committed_lane",
    )


def _value(value: object, key: str) -> object:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _text_or_none(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


__all__ = [
    "OntologyReplicaMirroringGraphGateway",
    "graph_gateway_for_activated_package",
    "invoke_response_targets_required_ontology_replica",
    "ontology_replica_mirror_skip_reason",
    "required_ontology_replica_fqn_prefixes",
]
