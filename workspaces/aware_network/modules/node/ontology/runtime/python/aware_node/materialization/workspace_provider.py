from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_node.deployment_closure import (
    NODE_RUNTIME_CLOSURE_CONTEXT_KEY,
    build_node_runtime_closure_payload,
)
from aware_node.materialization import materialize_node_package_from_manifest
from aware_node.semantic_contract import (
    NODE_RUNTIME_CLOSURE_ARTIFACT_FAMILY,
    NODE_RUNTIME_CLOSURE_ARTIFACT_ROLE,
    NODE_RUNTIME_CLOSURE_CONTRACT_VERSION,
    NODE_RUNTIME_CLOSURE_OUTPUT_KEY,
    NODE_RUNTIME_CLOSURE_PRODUCER_KEY,
)

NODE_READ_MODEL_REPO_ROOT_CONTEXT_KEY = "node_read_model_repo_root"

_FULL_REBUILD_FALLBACK_REASON = (
    "Node provider has not implemented delta materialization yet; "
    "replayed the full Node package manifest while preserving CodePackageDelta "
    "affected/applied semantic evidence."
)


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    affected_semantic_keys = _semantic_keys_from_request(request)
    result = await materialize_node_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        node_toml_path=request.manifest_path,
        repo_root=_node_read_model_repo_root(request=request),
        semantic_ontology_package_catalog=_semantic_ontology_package_catalog(
            request=request,
        ),
        source_code_package_id=request.source_code_package_id,
    )
    node_runtime_closure = build_node_runtime_closure_payload(
        result=result,
        workspace_semantic_package_selection_intents=(
            _workspace_semantic_package_selection_intents(request=request)
        ),
    )
    node_runtime_closure_receipt = _write_node_runtime_closure_artifact(
        workspace_root=request.workspace_root,
        node_package_name=result.node_package.name,
        node_runtime_closure=node_runtime_closure,
        source_object_instance_graph_commit_id=(
            result.package_object_instance_graph_commit_id
        ),
        manifest_path=result.node_toml_path,
    )
    return SemanticPackageMaterializationResult(
        details={
            "artifact_ownership_receipts": (node_runtime_closure_receipt,),
            "node_runtime_closure": node_runtime_closure,
            "node_toml_path": result.node_toml_path.as_posix(),
            "node_config_name": result.node_config.name,
            "node_config_id": str(result.node_config.id),
            "node_package_name": result.node_package.name,
            "node_package_id": str(result.node_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id)
                if result.source_code_package_id is not None
                else None
            ),
            "source_code_package_object_instance_graph_commit_id": (
                str(result.source_code_package_object_instance_graph_commit_id)
                if result.source_code_package_object_instance_graph_commit_id
                is not None
                else None
            ),
            "source_files": list(result.source_files),
            "node_phase_timings_s": dict(result.phase_timings_s),
            "node_config_commit_id": (
                str(result.node_config_commit_id)
                if result.node_config_commit_id is not None
                else None
            ),
            "node_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "node_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "node_package_object_instance_graph_commit_id": (
                str(result.package_object_instance_graph_commit_id)
                if result.package_object_instance_graph_commit_id is not None
                else None
            ),
            "node_config_projection_hash": result.node_config_projection_hash,
            "node_package_projection_hash": result.node_package_projection_hash,
            "node_config_object_instance_graph_commit_id": (
                str(result.node_config_object_instance_graph_commit_id)
                if result.node_config_object_instance_graph_commit_id is not None
                else None
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.node_package.name,
                manifest_toml_path=result.node_toml_path,
                semantic_package_id=result.node_package.id,
                semantic_root_id=result.node_config.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    result.package_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    result.node_config_object_instance_graph_commit_id
                ),
                semantic_root_kind="node_config",
                semantic_projection_name="NodePackage",
                semantic_projection_hash=result.node_package_projection_hash,
                source_code_package_id=result.source_code_package_id,
                source_object_instance_graph_commit_id=(
                    result.source_code_package_object_instance_graph_commit_id
                ),
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=affected_semantic_keys,
        applied_semantic_keys=affected_semantic_keys,
        fallback_reason=_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
    )


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    return tuple(sorted({str(key).strip() for key in raw_keys if str(key).strip()}))


def _semantic_ontology_package_catalog(
    *,
    request: SemanticPackageMaterializationRequest,
) -> Mapping[str, object] | None:
    value = request.context.get(SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY)
    if isinstance(value, Mapping):
        return value
    return None


def _node_read_model_repo_root(
    *,
    request: SemanticPackageMaterializationRequest,
) -> Path | None:
    value = request.context.get(NODE_READ_MODEL_REPO_ROOT_CONTEXT_KEY)
    if value is None:
        return None
    return Path(str(value)).expanduser().resolve()


def _workspace_semantic_package_selection_intents(
    *,
    request: SemanticPackageMaterializationRequest,
) -> tuple[Mapping[str, object], ...]:
    value = request.context.get(NODE_RUNTIME_CLOSURE_CONTEXT_KEY)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _write_node_runtime_closure_artifact(
    *,
    workspace_root: Path,
    node_package_name: str,
    node_runtime_closure: Mapping[str, object],
    source_object_instance_graph_commit_id: object | None,
    manifest_path: Path,
) -> dict[str, object]:
    relative_path = (
        ".aware" f"/node/runtime_closure/{_safe_artifact_name(node_package_name)}.json"
    )
    artifact_path = workspace_root / relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        json.dumps(
            node_runtime_closure,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    artifact_path.write_text(content, encoding="utf-8")
    encoded = content.encode("utf-8")
    return {
        "producer_provider_key": "aware_node",
        "producer_key": NODE_RUNTIME_CLOSURE_PRODUCER_KEY,
        "producer_kind": "semantic_materialization",
        "semantic_owner": "aware_node.provider",
        "output_key": NODE_RUNTIME_CLOSURE_OUTPUT_KEY,
        "artifact_family": NODE_RUNTIME_CLOSURE_ARTIFACT_FAMILY,
        "artifact_key": node_package_name,
        "artifact_role": NODE_RUNTIME_CLOSURE_ARTIFACT_ROLE,
        "path": relative_path,
        "manifest_path": _manifest_path_relative_to_workspace(
            workspace_root=workspace_root,
            manifest_path=manifest_path,
        ),
        "runtime_contract_version": NODE_RUNTIME_CLOSURE_CONTRACT_VERSION,
        "media_type": "application/json",
        "digest": hashlib.sha256(encoded).hexdigest(),
        "digest_algorithm": "sha256",
        "size_bytes": len(encoded),
        "status": "available",
        "required_for": (
            "workspace_revision",
            "deployment",
            "node_run_manifest",
        ),
        "source_object_instance_graph_commit_id": (
            str(source_object_instance_graph_commit_id)
            if source_object_instance_graph_commit_id is not None
            else None
        ),
        "provider_payload": {
            "schema": node_runtime_closure.get("schema"),
            "node_package_name": node_package_name,
        },
    }


def _manifest_path_relative_to_workspace(
    *,
    workspace_root: Path,
    manifest_path: Path,
) -> str:
    try:
        return manifest_path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return manifest_path.as_posix()


def _safe_artifact_name(value: str) -> str:
    token = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "-"
        for char in value.strip()
    ).strip(".-_")
    return token or "node"


__all__ = ["NODE_READ_MODEL_REPO_ROOT_CONTEXT_KEY", "materialize"]
