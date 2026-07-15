from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID

from aware_attention_ontology.stable_ids import stable_attention_package_id
from aware_attention.compile import compile_attention_workspace
from aware_attention.materialization.service import (
    materialize_attention_compile_plan_ontology,
)
from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.materialization.receipts import encode_materialization_run_receipt
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta.runtime.graph_runtime import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    manifest_path = _workspace_manifest_path(request=request)
    compile_result = compile_attention_workspace(
        toml_path=manifest_path,
        repo_root=request.workspace_root,
        emit_compile_plan=True,
    )
    context_package_name = str(
        request.context.get("semantic_package_name") or ""
    ).strip()
    package_name = compile_result.package_name
    if context_package_name and context_package_name != package_name:
        raise RuntimeError(
            "Attention materialization package mismatch: "
            f"context={context_package_name!r} manifest={package_name!r}"
        )
    attention_package_id = stable_attention_package_id(name=package_name)
    source_code_package_id = _uuid_or_none(
        request.context.get("source_code_package_id")
    )
    artifact = compile_result.compile_plan_artifact
    if artifact is None:
        raise RuntimeError("Attention compile plan artifact was not emitted")

    projection_hash = _lane_projection_hash(request=request)
    runtime = _runtime_with_manifest(request=request)
    materialization_receipt = await materialize_attention_compile_plan_ontology(
        runtime=cast(Any, runtime),
        index=request.index,
        actor_id=request.actor_id,
        aware_root=request.workspace_root,
        lane=MaterializationLaneContext(
            branch_id=attention_package_id,
            projection_hash=projection_hash,
        ),
        package_name=package_name,
    )
    layout_keys = tuple(
        layout.layout_key for layout in compile_result.compile_plan.layout_ontology
    )
    section_keys_by_layout = {
        layout.layout_key: [section.section_key for section in layout.sections]
        for layout in compile_result.compile_plan.layout_ontology
    }
    return SemanticPackageMaterializationResult(
        details={
            "attention_toml_path": manifest_path.as_posix(),
            "attention_package_name": package_name,
            "attention_package_id": str(attention_package_id),
            "source_code_package_id": (
                str(source_code_package_id)
                if source_code_package_id is not None
                else None
            ),
            "compile_plan_artifact_relpath": artifact.relpath,
            "compile_plan_artifact_hash_sha256": artifact.hash_sha256,
            "layout_count": len(layout_keys),
            "layout_keys": list(layout_keys),
            "section_keys_by_layout": section_keys_by_layout,
            "attention_layout_materialization_receipt": (
                encode_materialization_run_receipt(receipt=materialization_receipt)
                if materialization_receipt is not None
                else None
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=package_name,
                manifest_toml_path=manifest_path,
                semantic_package_id=attention_package_id,
                semantic_root_id=attention_package_id,
                semantic_branch_id=attention_package_id,
                semantic_root_kind="attention_package",
                semantic_projection_name="AttentionPackage",
                semantic_projection_hash=projection_hash,
                source_code_package_id=source_code_package_id,
            ),
        ),
        commit_id=_last_commit_id(materialization_receipt),
        head_commit_id=_last_commit_id(materialization_receipt),
    )


@dataclass(frozen=True, slots=True)
class _RuntimeManifestAdapter:
    manifest_path: Path
    invoker: object


class _MetaGraphFunctionRuntime(Protocol):
    async def invoke_function(
        self, request: MetaGraphInvokeFunctionInput
    ) -> MetaGraphCommitReceipt: ...


@dataclass(frozen=True, slots=True)
class _MetaGraphFunctionRuntimeInvoker:
    meta_runtime: _MetaGraphFunctionRuntime

    async def invoke_function_with_index(
        self,
        *,
        index: object,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        receipt = await self.meta_runtime.invoke_function(
            MetaGraphInvokeFunctionInput(
                index=cast(Any, index),
                actor_id=request.actor_id,
                function_id=request.function_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                call_target=MetaGraphCallTarget(request.call_target.value),
                target_object_id=request.target_object_id,
                object_projection_graph_id=request.object_projection_graph_id,
                args=request.args,
                kwargs=request.kwargs,
                expected_graph_hash_pre=request.expected_graph_hash_pre,
                expected_head_commit_id=request.expected_head_commit_id,
                commit=request.commit,
                publish=request.publish,
            )
        )
        return MetaGraphInvokeFunctionResponse(
            actor_id=receipt.actor_id,
            domain_branch_id=receipt.domain_branch_id,
            domain_projection_hash=receipt.domain_projection_hash,
            status=receipt.status,
            payload=receipt.payload,
            error=receipt.error,
            logs=list(receipt.logs),
            execution_time_ms=receipt.execution_time_ms,
            root_object_id=receipt.root_object_id,
            graph_hash_pre=receipt.graph_hash_pre,
            graph_hash_post=receipt.graph_hash_post,
            function_call_id=receipt.function_call_id,
            function_call_response_id=receipt.function_call_response_id,
            changes=receipt.changes,
            domain_commit_id=receipt.commit_id,
            object_instance_graph_commit_id=receipt.object_instance_graph_commit_id,
        )


def _runtime_with_manifest(
    *,
    request: SemanticPackageMaterializationRequest,
) -> object:
    manifest_path = getattr(request.runtime, "manifest_path", None)
    if isinstance(manifest_path, Path):
        return request.runtime
    if isinstance(manifest_path, str) and manifest_path.strip():
        return _RuntimeManifestAdapter(
            manifest_path=Path(manifest_path).resolve(),
            invoker=_runtime_invoker(request=request),
        )
    return _RuntimeManifestAdapter(
        manifest_path=_workspace_runtime_manifest_path(request=request),
        invoker=_runtime_invoker(request=request),
    )


def _runtime_invoker(
    *,
    request: SemanticPackageMaterializationRequest,
) -> object:
    invoker = getattr(request.runtime, "invoker", None)
    if invoker is not None:
        return invoker
    invoke_function_with_index = getattr(
        request.runtime, "invoke_function_with_index", None
    )
    if callable(invoke_function_with_index):
        return request.runtime
    invoke_function = getattr(request.runtime, "invoke_function", None)
    if callable(invoke_function):
        return _MetaGraphFunctionRuntimeInvoker(meta_runtime=request.runtime)
    raise RuntimeError("Attention materialization runtime is missing invoker")


def _workspace_runtime_manifest_path(
    *,
    request: SemanticPackageMaterializationRequest,
) -> Path:
    raw = request.context.get("runtime_manifest_path")
    if isinstance(raw, str) and raw.strip():
        return (
            Path(raw).resolve()
            if Path(raw).is_absolute()
            else (request.workspace_root / raw).resolve()
        )
    workspace_toml = (request.workspace_root / "aware.workspace.toml").resolve()
    if workspace_toml.exists():
        return workspace_toml
    return request.workspace_root.resolve() / "aware.workspace.toml"


def _workspace_manifest_path(
    *,
    request: SemanticPackageMaterializationRequest,
) -> Path:
    return (
        request.manifest_path.resolve()
        if request.manifest_path.is_absolute()
        else (request.workspace_root / request.manifest_path).resolve()
    )


def _lane_projection_hash(
    *,
    request: SemanticPackageMaterializationRequest,
) -> str:
    raw = request.context.get("semantic_projection_hash")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "AttentionPackage"


def _last_commit_id(receipt: object | None) -> UUID | None:
    if receipt is None:
        return None
    steps = getattr(receipt, "steps", ())
    for step in reversed(tuple(steps)):
        commit_id = getattr(step, "head_commit_id", None) or getattr(
            step, "commit_id", None
        )
        if isinstance(commit_id, UUID):
            return commit_id
    return None


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value.strip())
    return None


__all__ = ["materialize"]
