from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetObjectInstanceGraphCommitRequest,
    OntologyGraphGetObjectInstanceGraphCommitResponse,
)
from aware_environment_service_dto.environment.environment import (
    MaterializeCommittedProjectionDtoRequest,
    MaterializeCommittedProjectionDtoResponse,
)
from aware_types import JsonObject

_MATERIALIZER_VERSION = "environment.committed_projection_dto.v0"
_DTO_REQUIRED_FOR = "committed_projection_dto"
_DTO_REQUIRED_ARTIFACT_ROLES = (
    "dependency_import_resolution",
    "package_bootstrap",
)
OntologyApiClientProvider = Callable[[], object | None]


class _OntologyGraphCommitClient(Protocol):
    async def get_object_instance_graph_commit(
        self,
        request: OntologyGraphGetObjectInstanceGraphCommitRequest,
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse: ...


async def materialize_committed_projection_dto(
    *,
    request: MaterializeCommittedProjectionDtoRequest,
    workspace_revision_materialized_root: str | Path | None,
    runtime_artifact_refs: Sequence[object],
    ontology_api_client_provider: OntologyApiClientProvider | None,
) -> MaterializeCommittedProjectionDtoResponse:
    if request.branch_id is None:
        return _response(
            request=request,
            status="refused",
            error="explicit_lane_required",
            refusal_code="branch_id_required",
            evidence_reason="branch_id_required",
        )
    if request.projection_hash is None:
        return _response(
            request=request,
            status="refused",
            error="explicit_lane_required",
            refusal_code="projection_hash_required",
            evidence_reason="projection_hash_required",
        )
    if not request.dto_class_ref and request.class_config_id is None:
        return _response(
            request=request,
            status="refused",
            error="dto_target_required",
            refusal_code="dto_class_ref_or_class_config_id_required",
            evidence_reason="dto_class_ref_or_class_config_id_required",
        )
    if request.root_object_id is None and not request.use_commit_root:
        return _response(
            request=request,
            status="refused",
            error="root_object_required",
            refusal_code="root_object_id_required_when_use_commit_root_false",
            evidence_reason="root_object_id_required_when_use_commit_root_false",
        )

    artifact_bundle, artifact_error = _resolve_dto_artifact_bundle(
        workspace_revision_materialized_root=workspace_revision_materialized_root,
        runtime_artifact_refs=runtime_artifact_refs,
        request=request,
    )
    if artifact_bundle is None or artifact_error is not None:
        return _response(
            request=request,
            status="refused",
            error="dto_runtime_artifact_unavailable",
            refusal_code="dto_runtime_artifact_unavailable",
            evidence_reason=artifact_error or "dto_runtime_artifact_unavailable",
            artifact_bundle=artifact_bundle,
        )
    if not cast(Any, artifact_bundle).deployment_ready:
        return _response(
            request=request,
            status="refused",
            error="dto_runtime_artifact_unavailable",
            refusal_code="dto_runtime_artifact_unavailable",
            evidence_reason="dto_runtime_artifact_missing_required_roles",
            artifact_bundle=artifact_bundle,
        )

    ontology_graph = _ontology_graph_commit_client(ontology_api_client_provider)
    if ontology_graph is None:
        return _response(
            request=request,
            status="refused",
            error="ontology_service_api_route_required",
            refusal_code="ontology_service_api_route_required",
            evidence_reason="ontology_service_api_route_required",
            artifact_bundle=artifact_bundle,
        )

    try:
        commit_response = await ontology_graph.get_object_instance_graph_commit(
            OntologyGraphGetObjectInstanceGraphCommitRequest(
                actor_id=request.actor_id,
                domain_branch_id=request.branch_id,
                domain_projection_hash=request.projection_hash,
                domain_commit_id=request.commit_id,
            )
        )
    except Exception as exc:
        return _response(
            request=request,
            status="refused",
            error="ontology_commit_unavailable",
            refusal_code="ontology_commit_unavailable",
            evidence_reason=f"ontology_commit_request_failed:{type(exc).__name__}",
            artifact_bundle=artifact_bundle,
        )
    if commit_response.status != "succeeded":
        return _response(
            request=request,
            status="refused",
            error="ontology_commit_unavailable",
            refusal_code="ontology_commit_unavailable",
            evidence_reason=f"ontology_commit_status:{commit_response.status}",
            artifact_bundle=artifact_bundle,
            commit_response=commit_response,
        )
    if (
        request.expected_graph_hash_post is not None
        and commit_response.graph_hash_post != request.expected_graph_hash_post
    ):
        return _response(
            request=request,
            status="refused",
            error="graph_hash_post_mismatch",
            refusal_code="graph_hash_post_mismatch",
            evidence_reason="graph_hash_post_mismatch",
            artifact_bundle=artifact_bundle,
            commit_response=commit_response,
        )

    return _response(
        request=request,
        status="refused",
        error="ontology_projection_snapshot_api_unavailable",
        refusal_code="ontology_projection_snapshot_api_unavailable",
        evidence_reason="ontology_projection_snapshot_api_unavailable",
        artifact_bundle=artifact_bundle,
        commit_response=commit_response,
    )


def _resolve_dto_artifact_bundle(
    *,
    workspace_revision_materialized_root: str | Path | None,
    runtime_artifact_refs: Sequence[object],
    request: MaterializeCommittedProjectionDtoRequest,
) -> tuple[object | None, str | None]:
    if workspace_revision_materialized_root is None:
        return None, "workspace_revision_materialized_root_unavailable"
    if not runtime_artifact_refs:
        return None, "runtime_artifact_refs_unavailable"
    try:
        from aware_environment.environment_config.package_ref_resolution import (  # noqa: WPS433
            resolve_committed_projection_dto_artifact_bundle,
        )

        bundle = resolve_committed_projection_dto_artifact_bundle(
            artifact_refs=runtime_artifact_refs,
            materialized_workspace_root=workspace_revision_materialized_root,
            dto_package_name=request.dto_package_name,
            dto_import_root=request.dto_import_root,
            dto_class_ref=request.dto_class_ref,
            class_config_id=request.class_config_id,
        )
    except Exception as exc:
        return None, f"dto_runtime_artifact_invalid:{type(exc).__name__}"
    return bundle, None


def _response(
    *,
    request: MaterializeCommittedProjectionDtoRequest,
    status: str,
    error: str | None,
    refusal_code: str | None,
    evidence_reason: str,
    artifact_bundle: object | None = None,
    commit_response: OntologyGraphGetObjectInstanceGraphCommitResponse | None = None,
) -> MaterializeCommittedProjectionDtoResponse:
    return MaterializeCommittedProjectionDtoResponse(
        operation="materialize_committed_projection_dto",
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status=status,
        error=error,
        refusal_code=refusal_code,
        dto_payload=None,
        dto_class_ref=request.dto_class_ref,
        class_config_id=request.class_config_id,
        dto_package_name=request.dto_package_name,
        dto_import_root=request.dto_import_root,
        dto_artifact_digest=_dto_artifact_digest(artifact_bundle),
        commit_id=(
            commit_response.domain_commit_id
            if commit_response is not None
            and commit_response.domain_commit_id is not None
            else request.commit_id
        ),
        object_instance_graph_commit_id=(
            commit_response.object_instance_graph_commit_id
            if commit_response is not None
            else None
        ),
        object_instance_graph_id=(
            commit_response.object_instance_graph_id
            if commit_response is not None
            else request.object_instance_graph_id
        ),
        root_object_id=(
            commit_response.root_object_id
            if commit_response is not None
            and commit_response.root_object_id is not None
            else request.root_object_id
        ),
        graph_hash_post=(
            commit_response.graph_hash_post
            if commit_response is not None
            else request.expected_graph_hash_post
        ),
        materializer_version=_MATERIALIZER_VERSION,
        evidence=_evidence(
            reason=evidence_reason,
            request=request,
            artifact_bundle=artifact_bundle,
            commit_response=commit_response,
        ),
    )


def _evidence(
    *,
    reason: str,
    request: MaterializeCommittedProjectionDtoRequest,
    artifact_bundle: object | None = None,
    commit_response: OntologyGraphGetObjectInstanceGraphCommitResponse | None = None,
) -> JsonObject:
    payload = {
        "reason": reason,
        "required_for": _DTO_REQUIRED_FOR,
        "required_artifact_roles": list(_DTO_REQUIRED_ARTIFACT_ROLES),
        "deploy_contract_required": True,
        "allow_repo_local_imports": False,
        "allow_caller_import_paths": False,
        "allow_local_commit_store_reads": False,
        "commit_truth_source": "ontology_service_api.get_object_instance_graph_commit",
        "snapshot_truth_source": "ontology_service_api.materialized_projection_snapshot",
        "snapshot_api_available": False,
        "artifact_selection_source": "runtime_artifact_refs",
        "commit_locator": {
            "environment_id": str(request.environment_id),
            "branch_id": str(request.branch_id) if request.branch_id else None,
            "projection_hash": request.projection_hash,
            "commit_id": str(request.commit_id),
            "expected_graph_hash_post": request.expected_graph_hash_post,
            "object_instance_graph_id": (
                str(request.object_instance_graph_id)
                if request.object_instance_graph_id
                else None
            ),
            "root_object_id": (
                str(request.root_object_id) if request.root_object_id else None
            ),
        },
        "dto_target": {
            "dto_class_ref": request.dto_class_ref,
            "class_config_id": (
                str(request.class_config_id) if request.class_config_id else None
            ),
            "dto_package_name": request.dto_package_name,
            "dto_import_root": request.dto_import_root,
        },
        "dto_artifacts": _dto_artifact_evidence(artifact_bundle),
        "ontology_commit": _ontology_commit_evidence(commit_response),
    }
    return JsonObject(cast(Any, payload))


def _ontology_graph_commit_client(
    provider: OntologyApiClientProvider | None,
) -> _OntologyGraphCommitClient | None:
    client = provider() if provider is not None else None
    if client is None:
        return None
    ontology = getattr(client, "ontology", None)
    graph = getattr(ontology, "graph", None)
    if graph is None:
        graph = getattr(client, "graph", None)
    get_commit = getattr(graph, "get_object_instance_graph_commit", None)
    if not callable(get_commit):
        return None
    return cast(_OntologyGraphCommitClient, graph)


def _dto_artifact_digest(artifact_bundle: object | None) -> str | None:
    if artifact_bundle is None:
        return None
    digest = getattr(artifact_bundle, "dto_artifact_digest", None)
    return str(digest) if digest else None


def _dto_artifact_evidence(artifact_bundle: object | None) -> JsonObject:
    if artifact_bundle is None:
        return JsonObject(
            {
                "status": "unavailable",
                "artifact_count": 0,
                "missing_requirements": list(_DTO_REQUIRED_ARTIFACT_ROLES),
                "artifacts": [],
            }
        )
    artifacts = tuple(getattr(artifact_bundle, "artifacts", ()) or ())
    missing = tuple(getattr(artifact_bundle, "missing_requirements", ()) or ())
    return JsonObject(
        {
            "status": "available" if not missing else "missing",
            "artifact_count": len(artifacts),
            "package_name": getattr(artifact_bundle, "package_name", None),
            "import_root": getattr(artifact_bundle, "import_root", None),
            "missing_requirements": list(missing),
            "artifacts": [
                _resolved_artifact_evidence(artifact) for artifact in artifacts
            ],
        }
    )


def _resolved_artifact_evidence(artifact: object) -> JsonObject:
    artifact_ref = getattr(artifact, "artifact_ref", None)
    return JsonObject(
        {
            "artifact_family": getattr(artifact_ref, "artifact_family", None),
            "artifact_key": getattr(artifact_ref, "artifact_key", None),
            "artifact_role": getattr(artifact_ref, "artifact_role", None),
            "package_name": getattr(artifact_ref, "package_name", None),
            "workspace_relative_path": getattr(
                artifact,
                "workspace_relative_path",
                None,
            ),
            "digest": (
                f"sha256:{getattr(artifact, 'sha256')}"
                if getattr(artifact, "sha256", None)
                else getattr(artifact_ref, "digest", None)
            ),
            "revision_code_package_id": _string_or_none(
                getattr(artifact_ref, "revision_code_package_id", None)
            ),
            "source_code_package_id": _string_or_none(
                getattr(artifact_ref, "source_code_package_id", None)
            ),
            "source_object_instance_graph_commit_id": _string_or_none(
                getattr(artifact_ref, "source_object_instance_graph_commit_id", None)
            ),
            "input_object_instance_graph_commit_id": _string_or_none(
                getattr(artifact_ref, "input_object_instance_graph_commit_id", None)
            ),
        }
    )


def _ontology_commit_evidence(
    commit_response: OntologyGraphGetObjectInstanceGraphCommitResponse | None,
) -> JsonObject:
    if commit_response is None:
        return JsonObject({"status": "unavailable"})
    return JsonObject(
        {
            "status": commit_response.status,
            "domain_commit_id": _string_or_none(commit_response.domain_commit_id),
            "object_instance_graph_commit_id": _string_or_none(
                commit_response.object_instance_graph_commit_id
            ),
            "object_instance_graph_id": _string_or_none(
                commit_response.object_instance_graph_id
            ),
            "root_object_id": _string_or_none(commit_response.root_object_id),
            "graph_hash_pre": commit_response.graph_hash_pre,
            "graph_hash_post": commit_response.graph_hash_post,
            "error": commit_response.error,
        }
    )


def _string_or_none(value: object | None) -> str | None:
    return str(value) if value is not None else None


__all__ = ["materialize_committed_projection_dto"]
