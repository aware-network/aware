from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, cast
from uuid import UUID

from aware_code.semantic_action_policy import (
    build_semantic_function_call_plan_previews,
)
from aware_code.semantic_function_call_execution import (
    SemanticFunctionCallExecutionConfig,
)
from aware_code.semantic_graph_execution import (
    SemanticGraphFunctionInvocation,
)
from aware_code.semantic_materialization import (
    SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY,
    SemanticFunctionCallContext,
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
    build_semantic_provider_delta_head_move_plan,
)
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_code_ontology.code.code_plan import CodePackageDeltaAuthorityKind
from aware_code_ontology.code.code_plan import CodePackageDeltaKind
from aware_code_ontology.code.code_plan import CodePackageDeltaPath
from aware_code_ontology.code.code_plan import CodePackagePathRole

from aware_code_ontology.stable_ids import stable_code_package_id
from aware_api_runtime.compile_materialization import (
    build_generated_api_compile_plan_accessible_graphs,
    materialize_api_package_from_compile_plan_input,
    materialize_api_package_from_manifest,
)
from aware_api_runtime.manifest import (
    AwareApiTomlError,
    load_aware_api_toml_spec,
)
from aware_api_runtime.workspace_provider.deltas.transport import (
    api_delta_unsupported_reason as _api_delta_unsupported_reason,
    top_changed_path_payloads as _top_changed_path_payloads,
)
from aware_api_runtime.workspace_provider.deltas.semantic_analysis import (
    analyze_provider_delta_current_semantics as _analyze_provider_delta_current_semantics,
)
from aware_api_runtime.workspace_provider.deltas.baseline import (
    api_delta_baseline_hydration_preflight as _api_delta_baseline_hydration_preflight,
    api_delta_baseline_ref_payload as _api_delta_baseline_ref_payload,
    api_delta_durable_execution_inputs_preflight as _api_delta_durable_execution_inputs_preflight,
    api_delta_operation_execution_context as _api_delta_operation_execution_context,
    api_delta_previous_evidence_current_object_count as _api_delta_previous_evidence_current_object_count,
)
from aware_api_runtime.workspace_provider.deltas.dirty_diff import (
    api_delta_semantic_dirty_diff_from_analysis as _api_delta_semantic_dirty_diff_from_analysis,
)
from aware_api_runtime.workspace_provider.deltas.typed_operations import (
    api_delta_typed_operation_plan as _api_delta_typed_operation_plan,
)
from aware_api_runtime.workspace_provider.deltas.execution import (
    API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON as _API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON,
    api_delta_execute_typed_operation_plan as _api_delta_execute_typed_operation_plan,
    api_delta_typed_operation_execution_block as _api_delta_typed_operation_execution_block,
    api_delta_typed_operation_execution_preflight as _api_delta_typed_operation_execution_preflight,
)
from aware_api_runtime.workspace_provider.deltas.source_package import (
    api_delta_source_package_payload as _api_delta_source_package_payload,
)
from aware_api_runtime.workspace_provider.deltas.artifact_patch import (
    api_delta_api_client_service_protocol_patch_receipt as _api_delta_api_client_service_protocol_patch_receipt,
)
from aware_api_runtime.workspace_provider.deltas.artifact_plan import (
    api_product_runtime_delta_plan as _api_product_runtime_delta_plan,
)
from aware_api_runtime.workspace_provider.deltas.events import (
    api_delta_materialization_event_report as _api_delta_materialization_event_report,
    api_delta_materialization_event_report_with_workspace_aggregate_evidence,
)
from aware_api_ontology.api.api_package import ApiPackage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id
from aware_code_ontology.package.code_package import CodePackage
from aware_api_runtime.workspace import APIWorkspace
from aware_api_runtime.semantic_functions.resolution import (
    ApiSemanticFunctionCallResolution,
    resolve_api_semantic_function_call_plan_previews,
)
from aware_api_runtime.semantic_functions.execution import (
    api_semantic_function_call_execution_backend_from_context,
    execute_api_semantic_function_call_resolutions,
)
from aware_meta.materialization.function_refs import meta_ontology_function_ref


_FULL_REBUILD_FALLBACK_REASON = (
    "API provider has not implemented delta materialization yet; "
    "replayed the full API package manifest."
)
_DELTA_RESULT_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-result.v1"
)
_DELTA_COMMIT_REF_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-commit-ref.v1"
)
_SUPPORTED_DELTA_PROVIDER_KEY = "aware_api"
_DELTA_OPERATION_EXECUTION_FLAG = "execute_provider_delta_materialization"
_API_PACKAGE_BUILD_FUNCTION_REF = meta_ontology_function_ref(ApiPackage.build).ref
_DELTA_COMMIT_REF_REQUIRED_FIELDS = (
    "source_code_package_id",
    "source_object_instance_graph_commit_id",
    "semantic_package_id",
    "semantic_branch_id",
    "semantic_object_instance_graph_commit_id",
)
_DELTA_PACKAGE_SOURCE_COMMIT_REF_FIELDS = (
    "source_code_package_id",
    "source_object_instance_graph_commit_id",
    "semantic_package_id",
    "semantic_branch_id",
    "semantic_head_commit_id",
    "semantic_object_instance_graph_commit_id",
)
_API_COMPILE_PARITY_RECEIPT_SCHEMA = (
    "aware.api.workspace_materialize.compile_parity_receipt.v1"
)
_API_COMPILE_PARITY_RECEIPT_KIND = "api_workspace_materialize_compile_parity"
_API_COMPILE_PARITY_REQUIRED_EVIDENCE = (
    "runtime_manifest",
    "compile_plan",
    "api_client",
    "service_protocol",
)
_API_COMPILE_PARITY_AVAILABLE_STATUSES = frozenset(("available", "succeeded"))
_WORKSPACE_DEPENDENCY_ROOTS_CONTEXT_KEY = "workspace_dependency_roots"


def _code_package_build_function_ref() -> str:
    build_fn = getattr(CodePackage, "build_via_code_package_config", None)
    if build_fn is None:
        build_fn = getattr(CodePackage, "build")
    return meta_ontology_function_ref(build_fn).ref


def _code_package_apply_delta_function_ref() -> str:
    return meta_ontology_function_ref(CodePackage.apply_delta).ref


def build_api_provider_delta_function_call_context(
    request: object,
) -> dict[str, object]:
    manifest_path = _api_provider_delta_context_manifest_path(request=request)
    if manifest_path is None:
        return SemanticFunctionCallContext().evidence_payload()
    workspace_root = Path(getattr(request, "workspace_root", manifest_path.parent))
    return SemanticFunctionCallContext(
        resolved_argument_ref_object_ids=(
            _api_provider_delta_resolved_argument_refs(
                manifest_path=manifest_path,
                workspace_root=workspace_root,
            )
        ),
    ).evidence_payload()


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    if request.materialization_input is not None:
        return await _materialize_compile_plan_input(request=request)
    if _workspace_manifest_kind_from_request(request=request) == "api_dto":
        return await _materialize_api_dto_export(request=request)

    function_call_plans = build_semantic_function_call_plan_previews(
        semantic_events=_tuple_evidence(request.change_preview.get("semantic_events")),
        action_bindings=_tuple_evidence(request.change_preview.get("action_bindings")),
    )
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        request.context,
        provider_key="aware_api",
    )
    function_call_resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=function_call_plans,
        current_semantic_object_ids=(function_call_context.current_semantic_object_ids),
        resolved_argument_ref_object_ids=(
            function_call_context.resolved_argument_ref_object_ids
        ),
    )
    function_call_execution = await _function_call_execution_detail(
        context=request.context,
        function_call_resolutions=function_call_resolutions,
    )
    result = await materialize_api_package_from_manifest(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        api_toml_path=request.manifest_path,
        accessible_graphs=_semantic_object_config_graphs_from_context(request.context),
        dependency_repo_roots=_workspace_dependency_roots_from_context(request.context),
        post_step_tool_env_by_tool_id=(
            _language_materialization_post_step_tool_mapping_by_tool_id(
                context=request.context,
                mapping_key="state_env",
            )
        ),
        post_step_executable_overrides_by_tool_id=(
            _language_materialization_post_step_tool_mapping_by_tool_id(
                context=request.context,
                mapping_key="executable_overrides",
            )
        ),
        progress_callback=request.progress_callback,
    )
    source_object_instance_graph_commit_id = getattr(
        result,
        "source_object_instance_graph_commit_id",
        None,
    )
    artifact_ownership_receipts = (
        _api_product_runtime_artifact_ownership_receipts_for_materialization(
            request=request,
            package_name=result.api_package.name,
            runtime_compile_plan_hash=getattr(
                result,
                "runtime_compile_plan_hash",
                None,
            ),
            source_files=result.source_files,
            source_code_package_id=result.source_code_package_id,
            source_object_instance_graph_commit_id=(
                source_object_instance_graph_commit_id
            ),
            dependency_repo_roots=_workspace_dependency_roots_from_context(
                request.context
            ),
            product_runtime_compile_result=getattr(
                result,
                "product_runtime_compile_result",
                None,
            ),
            dart_public_package_compile_result=getattr(
                result,
                "dart_public_package_compile_result",
                None,
            ),
        )
    )
    language_post_step_receipts = tuple(
        dict(receipt)
        for receipt in getattr(result, "language_post_step_receipts", ()) or ()
    )
    compile_parity_receipts = _api_client_service_protocol_compile_parity_receipts(
        request=request,
        result=result,
        artifact_ownership_receipts=artifact_ownership_receipts,
        language_post_step_receipts=language_post_step_receipts,
    )
    language_code_package_ids = tuple(
        cast(tuple[object, ...], getattr(result, "language_code_package_ids", ()) or ())
    )
    language_code_package_refs = tuple(
        dict(item)
        for item in cast(
            tuple[Mapping[str, object], ...],
            getattr(result, "language_code_package_refs", ()) or (),
        )
    )
    return SemanticPackageMaterializationResult(
        details={
            "api_toml_path": result.api_toml_path.as_posix(),
            "api_name": result.api.name,
            "api_id": str(result.api.id),
            "api_package_name": result.api_package.name,
            "api_package_id": str(result.api_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_code_package_id": (
                str(result.source_code_package_id)
                if result.source_code_package_id is not None
                else None
            ),
            "source_object_instance_graph_commit_id": _optional_text(
                source_object_instance_graph_commit_id
            ),
            "api_source_path": result.api_source_path,
            "source_files": list(result.source_files),
            "api_phase_timings_s": dict(sorted(result.phase_timings_s.items())),
            "api_endpoint_catalog": _encode_api_endpoint_catalog_detail(
                result.api_endpoint_catalog
            ),
            "generated_dto_graph_count": result.generated_dto_graph_count,
            "generated_dto_class_config_count": (
                result.generated_dto_class_config_count
            ),
            "api_commit_id": (
                str(result.api_commit_id) if result.api_commit_id is not None else None
            ),
            "api_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "api_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
            "language_code_package_ids": [
                str(item) for item in language_code_package_ids
            ],
            "language_code_packages": [
                {
                    key: str(value) if _is_uuid(value) else value
                    for key, value in item.items()
                }
                for item in language_code_package_refs
            ],
            "semantic_function_call_plan_count": len(function_call_plans),
            "semantic_function_call_plans": tuple(
                plan.evidence_payload() for plan in function_call_plans
            ),
            "semantic_function_call_resolution_count": len(function_call_resolutions),
            "semantic_function_call_resolution_status_counts": (
                _resolution_status_counts(function_call_resolutions)
            ),
            "semantic_function_call_resolutions": tuple(
                resolution.evidence_payload()
                for resolution in function_call_resolutions
            ),
            "semantic_function_call_resolution_context": {
                "current_semantic_object_id_count": len(
                    function_call_context.current_semantic_object_ids
                ),
                "resolved_argument_ref_object_id_count": len(
                    function_call_context.resolved_argument_ref_object_ids
                ),
                "schema": "semantic_function_call_context",
            },
            "semantic_function_call_execution": function_call_execution,
            "artifact_ownership_receipts": artifact_ownership_receipts,
            "language_post_step_receipts": language_post_step_receipts,
            "compile_parity_receipts": compile_parity_receipts,
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.api_package.name,
                manifest_toml_path=result.api_toml_path,
                semantic_package_id=result.api_package.id,
                semantic_root_id=result.api.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=result.package_head_commit_id,
                semantic_root_object_instance_graph_commit_id=(
                    result.api_object_instance_graph_commit_id
                ),
                source_code_package_id=result.source_code_package_id,
                source_object_instance_graph_commit_id=(
                    source_object_instance_graph_commit_id
                ),
                runtime_code_package_refs=_runtime_code_package_refs(
                    language_code_package_refs
                ),
                implementation_code_packages=language_code_package_refs,
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=_semantic_keys_from_request(request),
        applied_semantic_keys=_semantic_keys_from_request(request),
        semantic_function_call_plans=function_call_plans,
        fallback_reason=_FULL_REBUILD_FALLBACK_REASON,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
        api_reference_branch_ids_by_api_name={result.api.name: request.branch_id},
        api_endpoint_catalog=result.api_endpoint_catalog,
    )


async def _materialize_api_dto_export(
    *,
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    from aware_api_runtime.compile import (  # noqa: WPS433
        resolve_api_runtime_package_dir,
    )
    from aware_api_runtime.compile_materialization.service import (  # noqa: WPS433
        resolve_source_owned_api_dto_export_accessible_graphs,
    )
    from aware_api_runtime.packages.materialization import (  # noqa: WPS433
        materialize_api_dto_packages,
    )

    api_toml_path = _api_dto_declaring_api_toml_path(request=request)
    workspace = APIWorkspace.from_toml(
        toml_path=api_toml_path,
        repo_root=request.workspace_root,
    )
    snapshot = workspace.build_snapshot()
    export = _api_dto_export_for_manifest(
        snapshot=snapshot,
        dto_manifest_path=request.manifest_path,
    )
    runtime_package_dir = resolve_api_runtime_package_dir(snapshot=snapshot)
    phase_timings_s: dict[str, float] = {}
    accessible_graphs = await resolve_source_owned_api_dto_export_accessible_graphs(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        api_toml_path=api_toml_path,
        accessible_graphs=_semantic_object_config_graphs_from_context(request.context),
        dependency_repo_roots=_workspace_dependency_roots_from_context(request.context),
        phase_timings_s=phase_timings_s,
    )
    dto_materializations = materialize_api_dto_packages(
        snapshot=snapshot,
        runtime_package_dir=runtime_package_dir,
        repo_root=request.workspace_root,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=_workspace_dependency_roots_from_context(request.context),
    )
    dto_materialization = _api_dto_materialization_for_export(
        dto_materializations=dto_materializations,
        package_name=export.package_name,
    )
    graph = dto_materialization.dependency_package.graph
    source_code_package_id = _api_dto_source_code_package_id(
        request=request,
        package_name=export.package_name,
    )
    artifact_ownership_receipts = _api_dto_artifact_ownership_receipts(
        api_package_name=snapshot.spec.api.package_name,
        workspace_root=request.workspace_root,
        dto_materializations=(dto_materialization,),
    )
    generated_code_package_deltas = _api_dto_generated_code_package_deltas(
        workspace_root=request.workspace_root,
        dto_materializations=(dto_materialization,),
    )
    materialized_files = tuple(
        _workspace_relative_path(workspace_root=request.workspace_root, path=path)
        for path in dto_materialization.materialization_result.files
    )
    package_root = _workspace_relative_path(
        workspace_root=request.workspace_root,
        path=dto_materialization.package_root,
    )
    semantic_keys = (
        f"api_dto:{export.package_name}",
        f"api:{snapshot.spec.api.package_name}",
    )
    return SemanticPackageMaterializationResult(
        details={
            "provider_key": "aware_api",
            "workspace_manifest_kind": "api_dto",
            "api_toml_path": api_toml_path.as_posix(),
            "api_package_name": snapshot.spec.api.package_name,
            "api_dto_package_name": export.package_name,
            "api_dto_manifest_path": request.manifest_path.as_posix(),
            "api_dto_package_root": package_root,
            "api_dto_import_root": dto_materialization.import_root,
            "api_dto_graph_id": str(graph.id),
            "api_dto_graph_name": graph.name,
            "api_dto_graph_fqn_prefix": graph.fqn_prefix,
            "api_dto_graph_node_count": len(graph.object_config_graph_nodes),
            "api_dto_phase_timings_s": dict(sorted(phase_timings_s.items())),
            "api_dto_materialized_file_count": len(materialized_files),
            "api_dto_materialized_files": list(materialized_files),
            "source_code_package_id": str(source_code_package_id),
            "artifact_ownership_receipts": artifact_ownership_receipts,
            "generated_code_package_deltas": [
                delta.model_dump(mode="json") for delta in generated_code_package_deltas
            ],
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=export.package_name,
                manifest_toml_path=request.manifest_path,
                semantic_package_id=stable_object_config_graph_package_id(
                    package_name=export.package_name,
                    fqn_prefix=graph.fqn_prefix or "",
                ),
                semantic_root_id=graph.id,
                semantic_branch_id=request.branch_id,
                semantic_root_kind="api_dto",
                semantic_projection_name="ApiPackage",
                source_code_package_id=source_code_package_id,
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=semantic_keys,
        applied_semantic_keys=semantic_keys,
        semantic_object_config_graphs=(graph,),
    )


def _api_dto_generated_code_package_deltas(
    *,
    workspace_root: Path,
    dto_materializations: tuple[object, ...],
) -> tuple[CodePackageDelta, ...]:
    deltas: list[CodePackageDelta] = []
    for dto_materialization in dto_materializations:
        delta = _api_dto_generated_code_package_delta(
            workspace_root=workspace_root,
            dto_materialization=dto_materialization,
        )
        if delta is not None:
            deltas.append(delta)
    return tuple(deltas)


def _api_dto_generated_code_package_delta(
    *,
    workspace_root: Path,
    dto_materialization: object,
) -> CodePackageDelta | None:
    package_root = Path(getattr(dto_materialization, "package_root")).resolve()
    import_root = str(getattr(dto_materialization, "import_root")).strip()
    materialization_result = getattr(dto_materialization, "materialization_result")
    paths: list[CodePackageDeltaPath] = []
    for materialized_file in sorted(
        (Path(path).resolve() for path in getattr(materialization_result, "files", ())),
        key=lambda path: path.as_posix(),
    ):
        if not materialized_file.is_file() or materialized_file.is_symlink():
            continue
        try:
            relative_path = materialized_file.relative_to(package_root)
        except ValueError:
            continue
        package_relative_path = PurePosixPath(relative_path.as_posix())
        if "_aware" in package_relative_path.parts:
            continue
        try:
            content_text = materialized_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                "API DTO generated code package contains non-text output: "
                f"{materialized_file.as_posix()}"
            ) from exc
        paths.append(
            CodePackageDeltaPath(
                relative_path=package_relative_path.as_posix(),
                kind=CodePackageDeltaKind.update,
                content_text=content_text,
                language=CodeLanguage.python,
                is_structural=False,
                path_role=_api_dto_generated_code_package_path_role(
                    relative_path=package_relative_path,
                ),
            )
        )
    if not paths:
        return None
    package_root_text = _workspace_relative_path(
        workspace_root=workspace_root,
        path=package_root,
    )
    return CodePackageDelta(
        package_name=import_root,
        package_root=package_root_text,
        sources_root=import_root,
        manifest_relative_path=f"{package_root_text}/pyproject.toml",
        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
        authority_kind=CodePackageDeltaAuthorityKind.semantic_materialization.value,
        paths=paths,
    )


def _api_dto_generated_code_package_path_role(
    *,
    relative_path: PurePosixPath,
) -> CodePackagePathRole:
    if relative_path.name == "pyproject.toml":
        return CodePackagePathRole.generated_manifest
    if relative_path.suffix == ".py":
        return CodePackagePathRole.generated_code
    return CodePackagePathRole.generated_metadata


def _workspace_manifest_kind_from_request(
    *,
    request: SemanticPackageMaterializationRequest,
) -> str:
    value = request.context.get("workspace_manifest_kind")
    return str(value or "").strip()


def _api_dto_declaring_api_toml_path(
    *,
    request: SemanticPackageMaterializationRequest,
) -> Path:
    metadata = request.context.get("semantic_package_metadata")
    if isinstance(metadata, Mapping):
        declaring_manifest_path = _optional_text(
            metadata.get("declaring_manifest_path")
        )
        if declaring_manifest_path is not None:
            candidate = Path(declaring_manifest_path)
            return (
                candidate.resolve()
                if candidate.is_absolute()
                else (request.workspace_root / candidate).resolve()
            )
    return _discover_api_toml_declaring_dto_export(
        workspace_root=request.workspace_root,
        dto_manifest_path=request.manifest_path,
    )


def _discover_api_toml_declaring_dto_export(
    *,
    workspace_root: Path,
    dto_manifest_path: Path,
) -> Path:
    workspace_root = workspace_root.resolve()
    dto_manifest_path = dto_manifest_path.resolve()
    matches: list[Path] = []
    for api_toml_path in sorted(
        workspace_root.rglob("aware.api.toml"),
        key=lambda item: item.as_posix(),
    ):
        if any(part in {".aware", "_aware", ".venv"} for part in api_toml_path.parts):
            continue
        try:
            snapshot = APIWorkspace.from_toml(
                toml_path=api_toml_path,
                repo_root=workspace_root,
            ).build_snapshot()
        except Exception:
            continue
        try:
            _ = _api_dto_export_for_manifest(
                snapshot=snapshot,
                dto_manifest_path=dto_manifest_path,
            )
        except RuntimeError:
            continue
        matches.append(api_toml_path.resolve())
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise RuntimeError(
            "API DTO materialization could not find an owning aware.api.toml "
            f"for DTO manifest {dto_manifest_path}"
        )
    raise RuntimeError(
        "API DTO materialization found multiple owning aware.api.toml files "
        f"for DTO manifest {dto_manifest_path}: "
        + ", ".join(path.as_posix() for path in matches)
    )


def _api_dto_export_for_manifest(
    *,
    snapshot: object,
    dto_manifest_path: Path,
):
    dto_manifest_path = dto_manifest_path.resolve()
    for export in snapshot.spec.semantic_package_exports:
        if getattr(getattr(export, "kind", None), "value", None) != "api_dto":
            continue
        export_manifest_path = (snapshot.package_root / export.manifest_path).resolve()
        if export_manifest_path == dto_manifest_path:
            return export
    raise RuntimeError(
        "API DTO materialization request does not match a declared api_dto "
        f"export: api_toml={snapshot.spec_path} dto_manifest={dto_manifest_path}"
    )


def _api_dto_materialization_for_export(
    *,
    dto_materializations: tuple[object, ...],
    package_name: str,
):
    matches = tuple(
        materialization
        for materialization in dto_materializations
        if getattr(materialization.semantic_package_export, "package_name", None)
        == package_name
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise RuntimeError(
            "API DTO materialization did not produce the requested DTO package: "
            f"{package_name!r}"
        )
    raise RuntimeError(
        "API DTO materialization produced multiple DTO packages for "
        f"{package_name!r}"
    )


def _api_dto_source_code_package_id(
    *,
    request: SemanticPackageMaterializationRequest,
    package_name: str,
) -> UUID:
    raw_source_code_package_id = _optional_text(
        request.context.get("source_code_package_id")
    )
    if raw_source_code_package_id is not None:
        return UUID(raw_source_code_package_id)
    config_ref = source_code_package_config_ref(
        manifest_kind="aware_toml",
        surface="api",
    )
    return stable_code_package_id(
        code_package_config_id=config_ref.config_id,
        package_name=package_name,
        language=CodeLanguage.aware.value,
    )


def _api_dto_artifact_ownership_receipts(
    *,
    api_package_name: str,
    workspace_root: Path,
    dto_materializations: tuple[object, ...],
) -> tuple[dict[str, object], ...]:
    from aware_api_runtime.build import (  # noqa: WPS433
        api_dto_package_artifact_ownership_receipts,
    )

    return api_dto_package_artifact_ownership_receipts(
        api_package_name=api_package_name,
        workspace_root=workspace_root,
        api_dto_package_materializations=dto_materializations,
    )


async def _materialize_compile_plan_input(
    *,
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    materialization_input = request.materialization_input
    if materialization_input is None:
        raise RuntimeError("API generated materialization input missing")
    if materialization_input.target_input_key != "aware_api.compile_plan":
        raise RuntimeError(
            "Unsupported API materialization input: "
            f"{materialization_input.target_input_key!r}"
        )
    compile_plan_payload = _compile_plan_payload_from_input(
        input_payload=materialization_input.input_artifact_payload,
        input_artifact_path=materialization_input.input_artifact_path,
    )
    product_runtime_accessible_graphs = (
        build_generated_api_compile_plan_accessible_graphs(
            compile_plan_payload=compile_plan_payload,
            accessible_graphs=_semantic_object_config_graphs_from_context(
                request.context,
            ),
        )
    )
    result = await materialize_api_package_from_compile_plan_input(
        runtime=request.runtime,
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        workspace_root=request.workspace_root,
        compile_plan_payload=compile_plan_payload,
        compile_plan_path=materialization_input.input_artifact_path,
        provider_payload=materialization_input.provider_payload,
        accessible_graphs=product_runtime_accessible_graphs,
        progress_callback=request.progress_callback,
    )
    artifact_ownership_receipts = (
        _api_product_runtime_artifact_ownership_receipts_for_compile_plan_input(
            request=request,
            package_name=result.api_package.name,
            compile_plan_payload=compile_plan_payload,
            compile_plan_path=materialization_input.input_artifact_path,
            accessible_graphs=product_runtime_accessible_graphs,
            dependency_repo_roots=_workspace_dependency_roots_from_context(
                request.context
            ),
        )
    )
    compile_parity_receipts = _api_client_service_protocol_compile_parity_receipts(
        request=request,
        result=result,
        artifact_ownership_receipts=artifact_ownership_receipts,
    )
    input_evidence = materialization_input.evidence_payload()
    compile_plan_path = result.compile_plan_path or request.manifest_path
    semantic_keys = (
        f"api:{result.api.name}",
        f"api_package:{result.api_package.name}",
    )
    return SemanticPackageMaterializationResult(
        details={
            "materialization_input": input_evidence,
            "api_compile_plan_path": (
                result.compile_plan_path.as_posix()
                if result.compile_plan_path is not None
                else None
            ),
            "api_name": result.api.name,
            "api_id": str(result.api.id),
            "api_package_name": result.api_package.name,
            "api_package_id": str(result.api_package.id),
            "semantic_branch_id": str(request.branch_id),
            "source_package_key": materialization_input.source_package_key,
            "source_manifest_path": materialization_input.source_manifest_path,
            "api_source_path": result.api_source_path,
            "source_files": list(result.source_files),
            "api_phase_timings_s": dict(sorted(result.phase_timings_s.items())),
            "api_endpoint_catalog": _encode_api_endpoint_catalog_detail(
                result.api_endpoint_catalog
            ),
            "artifact_ownership_receipts": artifact_ownership_receipts,
            "compile_parity_receipts": compile_parity_receipts,
            "generated_dto_graph_count": result.generated_dto_graph_count,
            "generated_dto_class_config_count": (
                result.generated_dto_class_config_count
            ),
            "api_commit_id": (
                str(result.api_commit_id) if result.api_commit_id is not None else None
            ),
            "api_package_commit_id": (
                str(result.package_commit_id)
                if result.package_commit_id is not None
                else None
            ),
            "api_package_head_commit_id": (
                str(result.package_head_commit_id)
                if result.package_head_commit_id is not None
                else None
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=result.api_package.name,
                manifest_toml_path=compile_plan_path,
                semantic_package_id=result.api_package.id,
                semantic_root_id=result.api.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=result.package_head_commit_id,
                semantic_object_instance_graph_commit_id=result.package_head_commit_id,
                semantic_root_object_instance_graph_commit_id=(
                    result.api_object_instance_graph_commit_id
                ),
                source_code_package_id=None,
            ),
        ),
        mode="full_rebuild",
        affected_semantic_keys=semantic_keys,
        applied_semantic_keys=semantic_keys,
        commit_id=result.package_commit_id,
        head_commit_id=result.package_head_commit_id,
        api_reference_branch_ids_by_api_name={result.api.name: request.branch_id},
        api_endpoint_catalog=result.api_endpoint_catalog,
    )


def _compile_plan_payload_from_input(
    *,
    input_payload: Mapping[str, object],
    input_artifact_path: Path | None,
) -> Mapping[str, object]:
    if input_payload:
        return dict(input_payload)
    artifact_hint = (
        f" path={input_artifact_path.as_posix()}"
        if input_artifact_path is not None
        else ""
    )
    raise RuntimeError(
        "Generated API compile-plan materialization input requires durable "
        "input_artifact_payload; input_artifact_path is local cache evidence only."
        + artifact_hint
    )


async def materialize_delta(request: object) -> dict[str, object]:
    from aware_api_runtime.workspace_provider.deltas.service import (  # noqa: WPS433
        materialize_delta as _materialize_delta,
    )

    return await _materialize_delta(request=request)


async def _materialize_delta_impl(request: object) -> dict[str, object]:
    package = getattr(request, "package")
    semantic_contract = getattr(request, "semantic_contract")
    current_delta_fingerprint = str(getattr(request, "current_delta_fingerprint"))
    package_payload = _model_payload(package)
    semantic_contract_payload = _model_payload(semantic_contract)
    provider_key = str(semantic_contract_payload.get("provider_key") or "")
    if provider_key != _SUPPORTED_DELTA_PROVIDER_KEY:
        return _provider_delta_fallback_result(
            request=request,
            fallback_reason="api_delta_semantic_contract_unsupported",
            details={"provider_key": provider_key},
        )

    manifest_path = _resolve_delta_manifest_path(package_payload.get("manifest_path"))
    if manifest_path is None:
        return _provider_delta_fallback_result(
            request=request,
            fallback_reason="api_delta_manifest_unavailable",
            details={"manifest_path": package_payload.get("manifest_path")},
        )

    unsupported_reason = _api_delta_unsupported_reason(request=request)
    if unsupported_reason is not None:
        return _provider_delta_fallback_result(
            request=request,
            fallback_reason=unsupported_reason,
            details=_api_delta_request_detail(request=request),
        )

    durable_execution_inputs_preflight = _api_delta_durable_execution_inputs_preflight(
        request=request
    )
    baseline_preflight = _api_delta_baseline_hydration_preflight(request=request)
    baseline_block = _api_delta_operation_execution_baseline_block(
        request=request,
        baseline_preflight=baseline_preflight,
    )
    if (
        _api_delta_operation_execution_requested(request=request)
        and baseline_block is not None
        and baseline_block.get("baseline_evidence_status") == "semantic_context_missing"
    ):
        return _provider_delta_baseline_context_missing_result(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            manifest_path=manifest_path,
            baseline_block=baseline_block,
        )

    try:
        current_semantic_analysis = _analyze_provider_delta_current_semantics(
            request=request,
            manifest_path=manifest_path,
        )
        snapshot = current_semantic_analysis.snapshot
        analysis = current_semantic_analysis.analysis
    except Exception as exc:
        return _provider_delta_fallback_result(
            request=request,
            fallback_reason="api_delta_semantic_analysis_failed",
            details={
                "manifest_path": manifest_path.as_posix(),
                "error": f"{type(exc).__name__}: {exc}",
            },
        )

    diagnostic_payloads = current_semantic_analysis.diagnostic_payloads
    if diagnostic_payloads:
        return _provider_delta_fallback_result(
            request=request,
            fallback_reason="api_delta_semantic_analysis_diagnostics_present",
            details={
                "manifest_path": manifest_path.as_posix(),
                "diagnostics": diagnostic_payloads,
            },
        )

    applied_semantic_keys = current_semantic_analysis.applied_semantic_keys
    if not applied_semantic_keys:
        return _provider_delta_fallback_result(
            request=request,
            fallback_reason="api_delta_semantic_keys_unavailable",
            details={
                "manifest_path": manifest_path.as_posix(),
                "changed_source_files": analysis.change_preview.changed_source_files,
            },
        )

    function_call_plans = _api_delta_function_call_plans_from_analysis(
        analysis=analysis
    )
    api_semantic_dirty_diff = _api_delta_semantic_dirty_diff_from_analysis(
        analysis=analysis,
        request=request,
        current_delta_fingerprint=current_delta_fingerprint,
        baseline_hydration_preflight=baseline_preflight,
    )
    provider_delta_head_move_plan = _api_delta_provider_head_move_plan(
        request=request,
        semantic_dirty_diff=api_semantic_dirty_diff,
    )
    provider_delta_typed_operation_plan = _api_delta_typed_operation_plan(
        analysis=analysis,
        semantic_dirty_diff=api_semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        function_call_plans=function_call_plans,
    )
    provider_delta_typed_operation_execution_preflight = (
        _api_delta_typed_operation_execution_preflight(
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        )
    )
    operation_plan = _api_delta_operation_plan_from_analysis(
        analysis=analysis,
        current_delta_fingerprint=current_delta_fingerprint,
        function_call_plans=function_call_plans,
        baseline_hydration_preflight=baseline_preflight,
        durable_execution_inputs_preflight=durable_execution_inputs_preflight,
        api_semantic_dirty_diff=api_semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        provider_delta_typed_operation_execution_preflight=(
            provider_delta_typed_operation_execution_preflight
        ),
    )
    operation_execution = await _api_delta_operation_execution_detail(
        request=request,
        function_call_plans=function_call_plans,
        baseline_hydration_preflight=baseline_preflight,
        durable_execution_inputs_preflight=durable_execution_inputs_preflight,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        provider_delta_typed_operation_execution_preflight=(
            provider_delta_typed_operation_execution_preflight
        ),
    )
    package_source_execution = await _api_delta_package_source_execution_detail(
        request=request,
        snapshot=snapshot,
        manifest_path=manifest_path,
        package_payload=package_payload,
        operation_execution=operation_execution,
    )
    commit_ref_payload, commit_ref_probe_details = (
        await _api_delta_commit_ref_payload_for_succeeded_delta(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            manifest_path=manifest_path,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
        )
    )
    semantic_context_accessible_graphs = (
        _api_delta_semantic_object_config_graphs_from_request(request=request)
    )
    api_product_runtime_delta_plan = _api_product_runtime_delta_plan(
        manifest_path=manifest_path,
        package_name=str(
            package_payload.get("package_name") or snapshot.spec.api.package_name or ""
        ),
        current_delta_fingerprint=current_delta_fingerprint,
        snapshot=snapshot,
        analysis=analysis,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        operation_execution=operation_execution,
        package_source_execution=package_source_execution,
        commit_ref_payload=commit_ref_payload,
        semantic_dirty_diff=api_semantic_dirty_diff,
        workspace_root=_api_delta_workspace_root_from_manifest_path(
            manifest_path=manifest_path,
        ),
        accessible_graphs=semantic_context_accessible_graphs,
    )
    api_materialization_event_report = _api_delta_materialization_event_report(
        semantic_dirty_diff=api_semantic_dirty_diff,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        runtime_artifact_delta_plan=api_product_runtime_delta_plan,
    )
    api_client_service_protocol_delta_patch = (
        _api_delta_api_client_service_protocol_patch_receipt(
            manifest_path=manifest_path,
            package_name=str(
                package_payload.get("package_name")
                or snapshot.spec.api.package_name
                or ""
            ),
            current_delta_fingerprint=current_delta_fingerprint,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
            commit_ref_payload=commit_ref_payload,
            runtime_artifact_delta_plan=api_product_runtime_delta_plan,
            materialization_event_report=api_materialization_event_report,
            workspace_root=_api_delta_workspace_root_from_manifest_path(
                manifest_path=manifest_path,
            ),
        )
    )
    api_materialization_event_report = (
        api_delta_materialization_event_report_with_workspace_aggregate_evidence(
            materialization_event_report=api_materialization_event_report,
            api_client_service_protocol_delta_patch=(
                api_client_service_protocol_delta_patch
            ),
        )
    )
    raw_artifact_ownership_receipts = api_client_service_protocol_delta_patch.get(
        "artifact_ownership_receipts",
    )
    artifact_ownership_receipts = (
        tuple(
            receipt
            for receipt in raw_artifact_ownership_receipts
            if isinstance(receipt, dict)
        )
        if isinstance(raw_artifact_ownership_receipts, (list, tuple))
        else ()
    )
    details = {
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "mode": _api_delta_result_mode(
            commit_ref_probe_details=commit_ref_probe_details,
            operation_execution=operation_execution,
        ),
        "manifest_path": manifest_path.as_posix(),
        "source_files": analysis.source_files,
        "changed_source_files": analysis.change_preview.changed_source_files,
        "semantic_delta_count": len(analysis.change_preview.semantic_deltas),
        "semantic_event_count": len(analysis.change_preview.semantic_events),
        "action_binding_count": len(analysis.change_preview.action_bindings),
        "current_delta_fingerprint": current_delta_fingerprint,
        "provider_delta_durable_execution_inputs_preflight": (
            durable_execution_inputs_preflight
        ),
        "provider_delta_durable_execution_inputs_status": (
            durable_execution_inputs_preflight["status"]
        ),
        "provider_delta_durable_execution_inputs_reason": (
            durable_execution_inputs_preflight["reason"]
        ),
        "api_current_semantic_analysis": (current_semantic_analysis.evidence_payload()),
        "semantic_dirty_diff": api_semantic_dirty_diff,
        "api_semantic_dirty_diff": api_semantic_dirty_diff,
        "provider_delta_head_move_plan": provider_delta_head_move_plan,
        "provider_delta_typed_operation_plan": provider_delta_typed_operation_plan,
        "provider_delta_typed_operation_status": (
            provider_delta_typed_operation_plan["status"]
        ),
        "provider_delta_typed_operation_reason": (
            provider_delta_typed_operation_plan["reason"]
        ),
        "provider_delta_typed_operation_count": (
            provider_delta_typed_operation_plan["typed_operation_count"]
        ),
        "provider_delta_blocked_typed_operation_count": (
            provider_delta_typed_operation_plan["blocked_operation_count"]
        ),
        "provider_delta_typed_operation_execution_preflight": (
            provider_delta_typed_operation_execution_preflight
        ),
        "provider_delta_typed_operation_execution_status": (
            provider_delta_typed_operation_execution_preflight["status"]
        ),
        "provider_delta_typed_operation_execution_reason": (
            provider_delta_typed_operation_execution_preflight["reason"]
        ),
        "delta_operation_plan": operation_plan,
        "provider_delta_operation_execution": operation_execution,
        "provider_delta_package_source_operation_execution": (package_source_execution),
        "api_product_runtime_delta_plan": api_product_runtime_delta_plan,
        "provider_delta_semantic_dirty_event_report": api_materialization_event_report,
        "api_materialization_event_report": api_materialization_event_report,
        "api_client_service_protocol_delta_patch": (
            api_client_service_protocol_delta_patch
        ),
        "artifact_ownership_receipts": artifact_ownership_receipts,
        "production_execution_wired": bool(operation_execution.get("did_execute")),
        **_api_delta_request_detail(request=request),
    }
    details.update(commit_ref_probe_details)
    details["mode"] = _api_delta_result_mode(
        commit_ref_probe_details=commit_ref_probe_details,
        operation_execution=operation_execution,
    )

    return {
        "contract_version": _DELTA_RESULT_CONTRACT_VERSION,
        "status": "succeeded",
        "package": package_payload,
        "semantic_contract": semantic_contract_payload,
        "current_delta_fingerprint": current_delta_fingerprint,
        "applied_semantic_keys": applied_semantic_keys,
        "skipped_semantic_keys": (),
        "stale_semantic_keys": (),
        "implementation_required": False,
        "implementation_work_items": (),
        "fallback_reason": None,
        "commit_ref_contract": commit_ref_payload["commit_ref_contract"],
        "bundle_package": commit_ref_payload["bundle_package"],
        "bundle_packages": (commit_ref_payload["bundle_package"],),
        "details": details,
        "error": None,
    }


def _api_delta_operation_plan_from_analysis(
    *,
    analysis: object,
    current_delta_fingerprint: str,
    function_call_plans: tuple[object, ...] | None = None,
    baseline_hydration_preflight: Mapping[str, object] | None = None,
    durable_execution_inputs_preflight: Mapping[str, object] | None = None,
    api_semantic_dirty_diff: Mapping[str, object] | None = None,
    provider_delta_head_move_plan: Mapping[str, object] | None = None,
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None,
    provider_delta_typed_operation_execution_preflight: (
        Mapping[str, object] | None
    ) = None,
) -> dict[str, object]:
    preview = getattr(analysis, "change_preview")
    semantic_deltas = tuple(getattr(preview, "semantic_deltas"))
    semantic_events = tuple(getattr(preview, "semantic_events"))
    action_bindings = tuple(getattr(preview, "action_bindings"))
    resolved_function_call_plans = (
        function_call_plans
        if function_call_plans is not None
        else _api_delta_function_call_plans_from_analysis(analysis=analysis)
    )
    semantic_delta_payloads = tuple(
        delta.evidence_payload() for delta in semantic_deltas
    )
    semantic_event_payloads = tuple(
        event.evidence_payload() for event in semantic_events
    )
    action_binding_payloads = tuple(
        action_binding.evidence_payload() for action_binding in action_bindings
    )
    function_call_plan_payloads = tuple(
        plan.evidence_payload() for plan in resolved_function_call_plans
    )
    return {
        "plan_kind": "api_provider_delta_operation_plan",
        "contract_version": "aware.api.provider-delta-operation-plan.v1",
        "status": "ready_non_executing",
        "reason": "api_provider_delta_operation_plan_ready",
        "source": "aware_api.semantic_analysis",
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": tuple(getattr(preview, "changed_source_files")),
        "affected_api_names": tuple(getattr(preview, "affected_api_names")),
        "affected_capability_names": tuple(
            getattr(preview, "affected_capability_names")
        ),
        "required_materializations": tuple(
            getattr(preview, "required_materializations")
        ),
        "semantic_delta_count": len(semantic_delta_payloads),
        "semantic_event_count": len(semantic_event_payloads),
        "action_binding_count": len(action_binding_payloads),
        "semantic_function_call_plan_count": len(function_call_plan_payloads),
        "operation_count": len(semantic_delta_payloads),
        "api_semantic_dirty_diff_status": (
            api_semantic_dirty_diff.get("status")
            if api_semantic_dirty_diff is not None
            else None
        ),
        "api_semantic_dirty_diff_entry_count": (
            api_semantic_dirty_diff.get("dirty_entry_count")
            if api_semantic_dirty_diff is not None
            else 0
        ),
        "api_baseline_index_compare_status": (
            api_semantic_dirty_diff.get("baseline_index_compare_status")
            if api_semantic_dirty_diff is not None
            else None
        ),
        "provider_delta_head_move_status": (
            provider_delta_head_move_plan.get("status")
            if provider_delta_head_move_plan is not None
            else None
        ),
        "provider_delta_head_move_planned_operation_count": (
            provider_delta_head_move_plan.get("planned_operation_count")
            if provider_delta_head_move_plan is not None
            else 0
        ),
        "provider_delta_typed_operation_status": (
            provider_delta_typed_operation_plan.get("status")
            if provider_delta_typed_operation_plan is not None
            else None
        ),
        "provider_delta_typed_operation_reason": (
            provider_delta_typed_operation_plan.get("reason")
            if provider_delta_typed_operation_plan is not None
            else None
        ),
        "provider_delta_typed_operation_count": (
            provider_delta_typed_operation_plan.get("typed_operation_count")
            if provider_delta_typed_operation_plan is not None
            else 0
        ),
        "provider_delta_blocked_typed_operation_count": (
            provider_delta_typed_operation_plan.get("blocked_operation_count")
            if provider_delta_typed_operation_plan is not None
            else 0
        ),
        "provider_delta_typed_operation_execution_status": (
            provider_delta_typed_operation_execution_preflight.get("status")
            if provider_delta_typed_operation_execution_preflight is not None
            else None
        ),
        "provider_delta_typed_operation_execution_reason": (
            provider_delta_typed_operation_execution_preflight.get("reason")
            if provider_delta_typed_operation_execution_preflight is not None
            else None
        ),
        "provider_delta_typed_operation_execution_blocked": (
            provider_delta_typed_operation_execution_preflight.get("blocked")
            if provider_delta_typed_operation_execution_preflight is not None
            else True
        ),
        "semantic_deltas": semantic_delta_payloads,
        "semantic_events": semantic_event_payloads,
        "action_bindings": action_binding_payloads,
        "semantic_function_call_plans": function_call_plan_payloads,
        "api_semantic_dirty_diff": (
            dict(api_semantic_dirty_diff)
            if api_semantic_dirty_diff is not None
            else None
        ),
        "provider_delta_head_move_plan": (
            dict(provider_delta_head_move_plan)
            if provider_delta_head_move_plan is not None
            else None
        ),
        "provider_delta_typed_operation_plan": (
            dict(provider_delta_typed_operation_plan)
            if provider_delta_typed_operation_plan is not None
            else None
        ),
        "provider_delta_typed_operation_execution_preflight": (
            dict(provider_delta_typed_operation_execution_preflight)
            if provider_delta_typed_operation_execution_preflight is not None
            else None
        ),
        "baseline_hydration_preflight": (
            dict(baseline_hydration_preflight)
            if baseline_hydration_preflight is not None
            else None
        ),
        "durable_execution_inputs_preflight": (
            dict(durable_execution_inputs_preflight)
            if durable_execution_inputs_preflight is not None
            else None
        ),
        "durable_execution_inputs_status": (
            durable_execution_inputs_preflight.get("status")
            if durable_execution_inputs_preflight is not None
            else None
        ),
        "durable_execution_inputs_shared_contract_available": (
            durable_execution_inputs_preflight.get(
                "shared_execution_inputs_contract_available"
            )
            if durable_execution_inputs_preflight is not None
            else False
        ),
        "apply_wired": False,
        "production_execution_wired": False,
        "would_execute": False,
        "would_persist": False,
    }


def _api_delta_provider_head_move_plan(
    *,
    request: object,
    semantic_dirty_diff: Mapping[str, object],
) -> dict[str, object]:
    return build_semantic_provider_delta_head_move_plan(
        request=_api_delta_workspace_provider_delta_request_payload(request=request),
        semantic_dirty_diff=semantic_dirty_diff,
    ).model_dump(mode="json")


def _api_delta_workspace_provider_delta_request_payload(
    *,
    request: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "package": _model_payload(getattr(request, "package", None)),
        "semantic_contract": _model_payload(
            getattr(request, "semantic_contract", None)
        ),
        "current_delta_fingerprint": str(getattr(request, "current_delta_fingerprint")),
        "delta_cause_hints": _model_payload(
            getattr(request, "delta_cause_hints", None)
        ),
        "previous_materialization_evidence": _model_payload(
            getattr(request, "previous_materialization_evidence", None)
        ),
        "baseline_ref": _api_delta_baseline_ref_payload(request=request),
        "baseline_source_object_instance_graph_commit_id": getattr(
            request,
            "baseline_source_object_instance_graph_commit_id",
            None,
        ),
        "baseline_semantic_object_instance_graph_commit_id": getattr(
            request,
            "baseline_semantic_object_instance_graph_commit_id",
            None,
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": getattr(
            request,
            "baseline_semantic_root_object_instance_graph_commit_id",
            None,
        ),
    }
    request_key = _optional_text(getattr(request, "provider_delta_request_key", None))
    if request_key is not None:
        payload["provider_delta_request_key"] = request_key
    return payload


def _api_delta_function_call_plans_from_analysis(
    *,
    analysis: object,
) -> tuple[object, ...]:
    preview = getattr(analysis, "change_preview")
    return build_semantic_function_call_plan_previews(
        semantic_events=tuple(getattr(preview, "semantic_events")),
        action_bindings=tuple(getattr(preview, "action_bindings")),
    )


async def _api_delta_operation_execution_detail(
    *,
    request: object,
    function_call_plans: tuple[object, ...],
    baseline_hydration_preflight: Mapping[str, object] | None = None,
    durable_execution_inputs_preflight: Mapping[str, object] | None = None,
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None,
    provider_delta_typed_operation_execution_preflight: (
        Mapping[str, object] | None
    ) = None,
) -> dict[str, object]:
    flag_requested = _api_delta_operation_execution_requested(request=request)
    durable_preflight = (
        dict(durable_execution_inputs_preflight)
        if durable_execution_inputs_preflight is not None
        else _api_delta_durable_execution_inputs_preflight(request=request)
    )
    payload: dict[str, object] = {
        "execution_kind": "api_provider_delta_operation_execution",
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": flag_requested,
        "operation_count": len(function_call_plans),
        "semantic_function_call_plan_count": len(function_call_plans),
        "durable_execution_inputs_preflight": durable_preflight,
        "durable_execution_inputs_status": durable_preflight["status"],
        "durable_execution_inputs_shared_contract_available": (
            durable_preflight["shared_execution_inputs_contract_available"]
        ),
        "would_execute": flag_requested,
        "did_execute": False,
        "would_persist": False,
        "receipt_persistence_contract_ready": False,
    }
    if not flag_requested:
        payload.update(
            {
                "status": "flag_required",
                "reason": (
                    "api_provider_delta_operation_execution_requires_explicit_flag"
                ),
                "execution_wired": False,
                "semantic_function_call_resolution_count": 0,
                "semantic_function_call_resolution_status_counts": {},
            }
        )
        return payload
    if (
        provider_delta_typed_operation_plan is not None
        and provider_delta_typed_operation_execution_preflight is not None
        and provider_delta_typed_operation_execution_preflight.get("status")
        == "typed_operation_execution_ready"
    ):
        context = _api_delta_operation_execution_context(request=request)
        typed_execution = await _api_delta_execute_typed_operation_plan(
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            provider_delta_typed_operation_execution_preflight=(
                provider_delta_typed_operation_execution_preflight
            ),
            context=context,
        )
        payload.update(
            {
                "status": typed_execution["status"],
                "reason": typed_execution["reason"],
                "operation_count": typed_execution["typed_operation_count"],
                "typed_operation_execution": typed_execution,
                "execution_wired": typed_execution.get("execution_wired") is True,
                "did_execute": typed_execution.get("did_execute") is True,
                "would_execute": True,
                "semantic_function_call_resolution_count": 0,
                "semantic_function_call_resolution_status_counts": {},
                "semantic_function_call_execution": typed_execution,
                "semantic_function_call_resolution_context": {
                    "current_semantic_object_id_count": typed_execution.get(
                        "current_semantic_object_id_count",
                        0,
                    ),
                    "resolved_argument_ref_object_id_count": typed_execution.get(
                        "resolved_argument_ref_object_id_count",
                        0,
                    ),
                    "schema": "typed_operation_execution_context",
                },
            }
        )
        return payload
    if not function_call_plans:
        payload.update(
            {
                "status": "no_operations",
                "reason": "api_provider_delta_operation_plan_empty",
                "execution_wired": True,
                "semantic_function_call_resolution_count": 0,
                "semantic_function_call_resolution_status_counts": {},
                "semantic_function_call_execution": {
                    "enabled": True,
                    "continue_on_failure": False,
                    "status": "no_operations",
                },
            }
        )
        return payload

    typed_execution_block = _api_delta_typed_operation_execution_block(
        provider_delta_typed_operation_execution_preflight=(
            provider_delta_typed_operation_execution_preflight
        ),
    )
    if typed_execution_block is not None:
        blocked_status = (
            _optional_text(typed_execution_block.get("operation_execution_status"))
            or "typed_operation_execution_blocked"
        )
        blocked_reason = (
            _optional_text(typed_execution_block.get("operation_execution_reason"))
            or _API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON
        )
        payload.update(
            {
                "status": blocked_status,
                "reason": blocked_reason,
                "execution_wired": False,
                "would_execute": False,
                "semantic_function_call_resolution_count": 0,
                "semantic_function_call_resolution_status_counts": {},
                "semantic_function_call_execution": {
                    "enabled": False,
                    "continue_on_failure": False,
                    "status": blocked_status,
                    "reason": blocked_reason,
                    **typed_execution_block,
                },
                **typed_execution_block,
            }
        )
        return payload

    baseline_block = _api_delta_operation_execution_baseline_block(
        request=request,
        baseline_preflight=baseline_hydration_preflight,
    )
    if baseline_block is not None:
        blocked_status = (
            _optional_text(baseline_block.get("operation_execution_status"))
            or "baseline_context_missing"
        )
        blocked_reason = (
            _optional_text(baseline_block.get("operation_execution_reason"))
            or "api_provider_delta_operation_execution_requires_semantic_baseline_context"
        )
        payload.update(
            {
                "status": blocked_status,
                "reason": blocked_reason,
                "execution_wired": False,
                "would_execute": False,
                "semantic_function_call_resolution_count": 0,
                "semantic_function_call_resolution_status_counts": {},
                "semantic_function_call_execution": {
                    "enabled": False,
                    "continue_on_failure": False,
                    "status": blocked_status,
                    "reason": blocked_reason,
                    **baseline_block,
                },
                **baseline_block,
            }
        )
        return payload

    context = _api_delta_operation_execution_context(request=request)
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=_SUPPORTED_DELTA_PROVIDER_KEY,
    )
    function_call_resolutions = resolve_api_semantic_function_call_plan_previews(
        plans=function_call_plans,
        current_semantic_object_ids=(function_call_context.current_semantic_object_ids),
        resolved_argument_ref_object_ids=(
            function_call_context.resolved_argument_ref_object_ids
        ),
    )
    function_call_execution = await _function_call_execution_detail(
        context=context,
        function_call_resolutions=function_call_resolutions,
    )
    status_counts = function_call_execution.get("status_counts")
    invoked_count = (
        int(status_counts.get("invoked", 0))
        if isinstance(status_counts, Mapping)
        else 0
    )
    blocked_count = (
        int(status_counts.get("blocked", 0))
        if isinstance(status_counts, Mapping)
        else 0
    )
    failed_count = (
        int(status_counts.get("failed", 0)) if isinstance(status_counts, Mapping) else 0
    )
    execution_status = _api_delta_operation_execution_status(
        function_call_execution=function_call_execution,
        invoked_count=invoked_count,
        blocked_count=blocked_count,
        failed_count=failed_count,
    )
    payload.update(
        {
            "status": execution_status,
            "reason": _api_delta_operation_execution_reason(
                execution_status=execution_status
            ),
            "execution_wired": execution_status
            not in {"disabled", "backend_unavailable"},
            "did_execute": invoked_count > 0,
            "semantic_function_call_resolution_count": len(function_call_resolutions),
            "semantic_function_call_resolution_status_counts": (
                _resolution_status_counts(function_call_resolutions)
            ),
            "semantic_function_call_resolutions": tuple(
                resolution.evidence_payload()
                for resolution in function_call_resolutions
            ),
            "semantic_function_call_resolution_context": {
                "current_semantic_object_id_count": len(
                    function_call_context.current_semantic_object_ids
                ),
                "resolved_argument_ref_object_id_count": len(
                    function_call_context.resolved_argument_ref_object_ids
                ),
                "schema": "semantic_function_call_context",
            },
            "semantic_function_call_execution": function_call_execution,
        }
    )
    return payload


def _api_delta_baseline_context_missing_execution_detail(
    *,
    request: object,
    baseline_block: Mapping[str, object],
) -> dict[str, object]:
    reason = "api_provider_delta_operation_execution_requires_semantic_baseline_context"
    return {
        "execution_kind": "api_provider_delta_operation_execution",
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": _api_delta_operation_execution_requested(request=request),
        "operation_count": 0,
        "semantic_function_call_plan_count": 0,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "receipt_persistence_contract_ready": False,
        "status": "baseline_context_missing",
        "reason": reason,
        "execution_wired": False,
        "semantic_function_call_resolution_count": 0,
        "semantic_function_call_resolution_status_counts": {},
        "semantic_function_call_execution": {
            "enabled": False,
            "continue_on_failure": False,
            "status": "baseline_context_missing",
            "reason": reason,
            **dict(baseline_block),
        },
        **dict(baseline_block),
    }


def _api_delta_package_source_operation_not_ready_execution_detail(
    *,
    request: object,
    operation_execution: Mapping[str, object],
) -> dict[str, object]:
    return {
        "execution_kind": "api_provider_delta_package_source_operation_execution",
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": _api_delta_operation_execution_requested(request=request),
        "would_execute": bool(operation_execution.get("did_execute")),
        "did_execute": False,
        "would_persist": False,
        "receipt_persistence_contract_ready": False,
        "step_count": 0,
        "steps": (),
        "status": "operation_not_ready",
        "reason": "api_provider_delta_operation_execution_not_complete",
    }


async def _api_delta_commit_ref_payload_for_succeeded_delta(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: Path,
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    operation_bundle_refs = _api_delta_bundle_refs_from_operation_execution(
        operation_execution=operation_execution,
    )
    package_source_bundle_refs = _api_delta_bundle_refs_from_package_source_execution(
        package_source_execution=package_source_execution,
    )
    combined_bundle_refs = {
        **operation_bundle_refs,
        **package_source_bundle_refs,
    }
    operation_commit_ref_details = _api_delta_operation_commit_ref_details(
        operation_execution=operation_execution,
        operation_bundle_refs=operation_bundle_refs,
        package_source_bundle_refs=package_source_bundle_refs,
        package_payload=package_payload,
    )
    if not _api_delta_commit_ref_probe_enabled(request=request):
        return (
            _api_delta_commit_ref_payload(
                package_payload=package_payload,
                semantic_contract_payload=semantic_contract_payload,
                manifest_path=manifest_path.as_posix(),
                result_status="succeeded",
                bundle_refs=combined_bundle_refs,
                reason_override=_api_delta_operation_commit_ref_reason_override(
                    combined_bundle_refs=combined_bundle_refs,
                    package_source_execution=package_source_execution,
                    package_payload=package_payload,
                ),
            ),
            {
                "commit_ref_probe_enabled": False,
                "commit_ref_probe_status": "not_requested",
                **operation_commit_ref_details,
            },
        )

    probe_context, missing_context_fields = _api_delta_commit_ref_probe_context(
        request=request
    )
    if missing_context_fields:
        return (
            _api_delta_commit_ref_payload(
                package_payload=package_payload,
                semantic_contract_payload=semantic_contract_payload,
                manifest_path=manifest_path.as_posix(),
                result_status="succeeded",
                bundle_refs=combined_bundle_refs,
                status_override="probe_context_missing",
                reason_override=("api_provider_delta_commit_ref_probe_context_missing"),
            ),
            {
                "commit_ref_probe_enabled": True,
                "commit_ref_probe_status": "context_missing",
                "commit_ref_probe_missing_context_fields": missing_context_fields,
                **operation_commit_ref_details,
            },
        )

    try:
        result = await materialize_api_package_from_manifest(
            runtime=probe_context["runtime"],
            index=probe_context["index"],
            actor_id=probe_context.get("actor_id"),
            branch_id=probe_context["branch_id"],
            workspace_root=probe_context["workspace_root"],
            api_toml_path=manifest_path,
            accessible_graphs=_api_delta_semantic_object_config_graphs_from_request(
                request=request,
            ),
            dependency_repo_roots=_workspace_dependency_roots_from_context(
                getattr(request, "context", {})
            ),
            post_step_tool_env_by_tool_id=(
                _language_materialization_post_step_tool_mapping_by_tool_id(
                    context=getattr(request, "context", {}),
                    mapping_key="state_env",
                )
            ),
            post_step_executable_overrides_by_tool_id=(
                _language_materialization_post_step_tool_mapping_by_tool_id(
                    context=getattr(request, "context", {}),
                    mapping_key="executable_overrides",
                )
            ),
        )
    except Exception as exc:
        return (
            _api_delta_commit_ref_payload(
                package_payload=package_payload,
                semantic_contract_payload=semantic_contract_payload,
                manifest_path=manifest_path.as_posix(),
                result_status="succeeded",
                bundle_refs=combined_bundle_refs,
                status_override="probe_failed",
                reason_override="api_provider_delta_commit_ref_probe_failed",
            ),
            {
                "commit_ref_probe_enabled": True,
                "commit_ref_probe_status": "failed",
                "commit_ref_probe_error": f"{type(exc).__name__}: {exc}",
                **operation_commit_ref_details,
            },
        )

    commit_ref_payload = _api_delta_commit_ref_payload(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path.as_posix(),
        result_status="succeeded",
        bundle_refs=_api_delta_bundle_refs_from_materialization_result(
            result=result,
            branch_id=probe_context["branch_id"],
        ),
        reason_override="api_provider_delta_commit_ref_probe_materialized_refs",
    )
    return (
        commit_ref_payload,
        {
            "mode": "api_provider_delta_commit_ref_probe",
            "commit_ref_probe_enabled": True,
            "commit_ref_probe_status": "executed",
            "commit_ref_probe_executed": True,
            "commit_ref_probe_api_phase_timings_s": dict(
                sorted(result.phase_timings_s.items())
            ),
            **operation_commit_ref_details,
        },
    )


async def _api_delta_package_source_execution_detail(
    *,
    request: object,
    snapshot: object,
    manifest_path: Path,
    package_payload: Mapping[str, object],
    operation_execution: Mapping[str, object],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "execution_kind": "api_provider_delta_package_source_operation_execution",
        "required_flag": _DELTA_OPERATION_EXECUTION_FLAG,
        "flag_requested": _api_delta_operation_execution_requested(request=request),
        "would_execute": bool(operation_execution.get("did_execute")),
        "did_execute": False,
        "would_persist": False,
        "receipt_persistence_contract_ready": False,
        "step_count": 0,
        "steps": (),
    }
    if operation_execution.get("status") != "executed":
        payload.update(
            {
                "status": "operation_not_ready",
                "reason": "api_provider_delta_operation_execution_not_complete",
            }
        )
        return payload

    operation_refs = _api_delta_bundle_refs_from_operation_execution(
        operation_execution=operation_execution,
    )
    api_id = _optional_text(operation_refs.get("semantic_root_id"))
    api_object_instance_graph_commit_id = _optional_text(
        operation_refs.get("semantic_root_object_instance_graph_commit_id")
    )
    if api_id is None or api_object_instance_graph_commit_id is None:
        payload.update(
            {
                "status": "operation_refs_missing",
                "reason": (
                    "api_provider_delta_package_source_requires_api_root_commit_ref"
                ),
            }
        )
        return payload

    context = _api_delta_operation_execution_context(request=request)
    backend = api_semantic_function_call_execution_backend_from_context(context)
    if backend is None:
        payload.update(
            {
                "status": "backend_unavailable",
                "reason": (
                    "api_provider_delta_package_source_execution_backend_unavailable"
                ),
            }
        )
        return payload

    steps: list[dict[str, object]] = []
    try:
        source_payload = _api_delta_source_package_payload(
            request=request,
            snapshot=snapshot,
            manifest_path=manifest_path,
            package_payload=package_payload,
        )
        code_package_build = await _api_delta_invoke_graph_operation(
            backend=backend,
            operation_name="code_package_build",
            provider_key="aware_code",
            call_target="constructor",
            function_ref=_code_package_build_function_ref(),
            arguments=source_payload["code_package_build_arguments"],
        )
        steps.append(code_package_build)
        code_package_id = _optional_text(code_package_build.get("result_object_id"))
        if code_package_id is None:
            raise RuntimeError(
                "CodePackage build did not return a source code package id."
            )
        code_package_apply_delta = await _api_delta_invoke_graph_operation(
            backend=backend,
            operation_name="code_package_apply_delta",
            provider_key="aware_code",
            call_target="instance",
            function_ref=_code_package_apply_delta_function_ref(),
            receiver_object_id=code_package_id,
            arguments=source_payload["code_package_apply_delta_arguments"],
        )
        steps.append(code_package_apply_delta)
        api_product_build = await _api_delta_invoke_graph_operation(
            backend=backend,
            operation_name="api_product_build",
            provider_key=_SUPPORTED_DELTA_PROVIDER_KEY,
            call_target="constructor",
            function_ref=_API_PACKAGE_BUILD_FUNCTION_REF,
            arguments=_api_delta_api_product_build_arguments(
                snapshot=snapshot,
                manifest_path=manifest_path,
                package_payload=package_payload,
                api_id=api_id,
                api_object_instance_graph_commit_id=(
                    api_object_instance_graph_commit_id
                ),
                source_code_package_id=code_package_id,
            ),
        )
        steps.append(api_product_build)
    except Exception as exc:
        payload.update(
            {
                "status": "failed",
                "reason": "api_provider_delta_package_source_execution_failed",
                "error": f"{type(exc).__name__}: {exc}",
                "steps": tuple(steps),
                "step_count": len(steps),
            }
        )
        return payload

    payload.update(
        {
            "status": "executed",
            "reason": "api_provider_delta_package_source_execution_invoked",
            "did_execute": True,
            "step_count": len(steps),
            "steps": tuple(steps),
            "source_update_strategy": source_payload["source_update_strategy"],
            "source_file_count": source_payload["source_file_count"],
            "source_delta_path_count": source_payload["source_delta_path_count"],
            "source_delta_kind_counts": source_payload["source_delta_kind_counts"],
        }
    )
    return payload


async def _api_delta_invoke_graph_operation(
    *,
    backend: object,
    operation_name: str,
    provider_key: str,
    call_target: str,
    function_ref: str,
    arguments: Mapping[str, object],
    receiver_object_id: str | None = None,
) -> dict[str, object]:
    result = await backend.invoke(
        SemanticGraphFunctionInvocation(
            call_target=call_target,  # type: ignore[arg-type]
            function_ref=function_ref,
            receiver_object_id=receiver_object_id,
            arguments=dict(arguments),
            provider_key=provider_key,
            evidence={"operation_name": operation_name},
        )
    )
    result_payload = result.evidence_payload()
    return {
        "operation_name": operation_name,
        "status": "invoked",
        "provider_key": provider_key,
        "call_target": call_target,
        "function_ref": function_ref,
        "receiver_object_id": receiver_object_id,
        "result_object_id": result.object_id,
        "commit_id": result_payload.get("commit_id"),
        "head_commit_id": result_payload.get("head_commit_id"),
        "branch_id": result_payload.get("branch_id"),
        "projection_hash": result_payload.get("projection_hash"),
        "evidence": {"result": result_payload},
    }


def _api_delta_api_product_build_arguments(
    *,
    snapshot: object,
    manifest_path: Path,
    package_payload: Mapping[str, object],
    api_id: str,
    api_object_instance_graph_commit_id: str,
    source_code_package_id: str,
) -> dict[str, object]:
    spec = getattr(snapshot, "spec")
    package_root = getattr(snapshot, "package_root")
    workspace_root = _api_delta_snapshot_repo_root(snapshot=snapshot)
    sources_root = (package_root / spec.build.sources_dir).resolve()
    return {
        "name": _api_delta_package_name(
            snapshot=snapshot,
            package_payload=package_payload,
        ),
        "api_id": api_id,
        "api_object_instance_graph_commit_id": api_object_instance_graph_commit_id,
        "source_code_package_id": source_code_package_id,
        "fqn_prefix": _optional_text(getattr(spec.api, "fqn_prefix", None)),
        "version_number": int(getattr(spec.api, "version_number", 1)),
        "title": _optional_text(getattr(spec.api, "title", None)),
        "description": _optional_text(getattr(spec.api, "description", None)),
        "aware_api_version": int(getattr(spec, "aware_api", 1)),
        "manifest_relative_path": _api_delta_relative_to(
            path=manifest_path,
            root=workspace_root,
        ),
        "package_root": _api_delta_relative_to(
            path=package_root,
            root=workspace_root,
        ),
        "sources_root": _api_delta_relative_to(
            path=sources_root,
            root=workspace_root,
        ),
        "include_paths": list(getattr(spec.build, "include_paths", ())),
        "exclude_paths": list(getattr(spec.build, "exclude_paths", ())),
        "force_fresh_scan": bool(getattr(spec.build, "force_fresh_scan", True)),
        "compilation_mode": _api_delta_enum_value(
            getattr(spec.build, "compilation_mode", "raw_xor")
        ),
        "dependencies": _api_delta_api_package_dependencies_payload(spec=spec),
        "targets": _api_delta_api_package_targets_payload(spec=spec),
    }


def _api_delta_package_name(
    *,
    snapshot: object,
    package_payload: Mapping[str, object],
) -> str:
    package_name = _optional_text(package_payload.get("package_name"))
    if package_name is not None:
        return package_name
    spec = getattr(snapshot, "spec")
    package_name = _optional_text(getattr(spec.api, "package_name", None))
    if package_name is None:
        raise RuntimeError(
            "API provider-delta package operation requires package_name."
        )
    return package_name


def _api_delta_snapshot_repo_root(*, snapshot: object) -> Path:
    repo_root = getattr(snapshot, "repo_root", None)
    if isinstance(repo_root, Path):
        return repo_root.resolve()
    return Path(str(repo_root)).resolve()


def _api_delta_relative_to(*, path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _api_delta_enum_value(value: object) -> object:
    enum_value = getattr(value, "value", None)
    return enum_value if enum_value is not None else value


def _api_delta_api_package_dependencies_payload(*, spec: object) -> list[object]:
    return [
        {
            "package_name": dependency.package_name,
            "version_number": dependency.version_number,
        }
        for dependency in getattr(spec, "dependencies", ())
    ]


def _api_delta_api_package_targets_payload(*, spec: object) -> dict[str, object]:
    targets = getattr(spec, "targets", None)
    payload: dict[str, object] = {}
    python = getattr(targets, "python", None)
    if python is not None:
        payload["python"] = {
            "root_dir": python.root_dir,
            "public_package": {
                "package_dir": python.public_package.package_dir,
                "root_dir": python.public_package.root_dir,
            },
            "service_protocol": {
                "package_dir": python.service_protocol.package_dir,
                "root_dir": python.service_protocol.root_dir,
            },
        }
    dart = getattr(targets, "dart", None)
    if dart is not None:
        payload["dart"] = {
            "root_dir": dart.root_dir,
            "public_package": {
                "package_dir": dart.public_package.package_dir,
                "root_dir": dart.public_package.root_dir,
            },
        }
    return payload


def _encode_api_endpoint_catalog_detail(
    api_endpoint_catalog: dict[str, dict[str, tuple[str, ...]]],
) -> dict[str, dict[str, list[str]]]:
    return {
        api_name: {
            capability_name: list(endpoint_names)
            for capability_name, endpoint_names in sorted(capability_catalog.items())
        }
        for api_name, capability_catalog in sorted(api_endpoint_catalog.items())
    }


def _semantic_keys_from_request(
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    raw_keys = request.change_preview.get("affected_semantic_keys")
    if not isinstance(raw_keys, (list, tuple, set)):
        return ()
    return tuple(sorted({str(key).strip() for key in raw_keys if str(key).strip()}))


def _provider_delta_fallback_result(
    *,
    request: object,
    fallback_reason: str,
    details: Mapping[str, object] | None = None,
) -> dict[str, object]:
    package = getattr(request, "package")
    semantic_contract = getattr(request, "semantic_contract")
    current_delta_fingerprint = str(getattr(request, "current_delta_fingerprint"))
    package_payload = _model_payload(package)
    semantic_contract_payload = _model_payload(semantic_contract)
    manifest_path = _optional_text(
        (details or {}).get("manifest_path")
        if details is not None
        else package_payload.get("manifest_path")
    )
    if manifest_path is None:
        manifest_path = _optional_text(package_payload.get("manifest_path"))
    commit_ref_payload = _api_delta_commit_ref_payload(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path,
        result_status="fallback_required",
    )
    payload_details = {
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "mode": "api_provider_delta_result_dry_run",
        "production_execution_wired": False,
    }
    if details:
        payload_details.update(dict(details))
    return {
        "contract_version": _DELTA_RESULT_CONTRACT_VERSION,
        "status": "fallback_required",
        "package": package_payload,
        "semantic_contract": semantic_contract_payload,
        "current_delta_fingerprint": current_delta_fingerprint,
        "applied_semantic_keys": (),
        "skipped_semantic_keys": (),
        "stale_semantic_keys": (),
        "implementation_required": False,
        "implementation_work_items": (),
        "fallback_reason": fallback_reason,
        "commit_ref_contract": commit_ref_payload["commit_ref_contract"],
        "bundle_package": commit_ref_payload["bundle_package"],
        "bundle_packages": (commit_ref_payload["bundle_package"],),
        "details": payload_details,
        "error": None,
    }


def _provider_delta_baseline_context_missing_result(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: Path,
    baseline_block: Mapping[str, object],
) -> dict[str, object]:
    operation_execution = _api_delta_baseline_context_missing_execution_detail(
        request=request,
        baseline_block=baseline_block,
    )
    package_source_execution = (
        _api_delta_package_source_operation_not_ready_execution_detail(
            request=request,
            operation_execution=operation_execution,
        )
    )
    commit_ref_details = _api_delta_operation_commit_ref_details(
        operation_execution=operation_execution,
        operation_bundle_refs={},
        package_source_bundle_refs={},
        package_payload=package_payload,
    )
    commit_ref_payload = _api_delta_commit_ref_payload(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path.as_posix(),
        result_status="succeeded",
        status_override="missing_durable_refs",
        reason_override="api_provider_delta_operation_execution_not_complete",
    )
    details = {
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "mode": _api_delta_result_mode(
            commit_ref_probe_details={},
            operation_execution=operation_execution,
        ),
        "manifest_path": manifest_path.as_posix(),
        "source_files": (),
        "changed_source_files": (),
        "semantic_delta_count": 0,
        "semantic_event_count": 0,
        "action_binding_count": 0,
        "current_delta_fingerprint": str(getattr(request, "current_delta_fingerprint")),
        "delta_operation_plan": {
            "plan_kind": "api_provider_delta_operation_plan",
            "contract_version": "aware.api.provider-delta-operation-plan.v1",
            "status": "blocked",
            "reason": (
                "api_provider_delta_operation_execution_requires_semantic_baseline_context"
            ),
            "source": "aware_api.provider_delta_request_preflight",
            "current_delta_fingerprint": str(
                getattr(request, "current_delta_fingerprint")
            ),
            "semantic_delta_count": 0,
            "semantic_event_count": 0,
            "action_binding_count": 0,
            "semantic_function_call_plan_count": 0,
            "operation_count": 0,
            "apply_wired": False,
            "production_execution_wired": False,
            "would_execute": False,
            "would_persist": False,
        },
        "provider_delta_operation_execution": operation_execution,
        "provider_delta_package_source_operation_execution": package_source_execution,
        "artifact_ownership_receipts": (),
        "production_execution_wired": False,
        "commit_ref_probe_enabled": False,
        "commit_ref_probe_status": "not_requested",
        **commit_ref_details,
        **_api_delta_request_detail(request=request),
    }
    return {
        "contract_version": _DELTA_RESULT_CONTRACT_VERSION,
        "status": "succeeded",
        "package": package_payload,
        "semantic_contract": semantic_contract_payload,
        "current_delta_fingerprint": str(getattr(request, "current_delta_fingerprint")),
        "applied_semantic_keys": (),
        "skipped_semantic_keys": (),
        "stale_semantic_keys": (),
        "implementation_required": False,
        "implementation_work_items": (),
        "fallback_reason": None,
        "commit_ref_contract": commit_ref_payload["commit_ref_contract"],
        "bundle_package": commit_ref_payload["bundle_package"],
        "bundle_packages": (commit_ref_payload["bundle_package"],),
        "details": details,
        "error": None,
    }


def _api_delta_commit_ref_payload(
    *,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: str | None,
    result_status: str,
    bundle_refs: Mapping[str, object] | None = None,
    status_override: str | None = None,
    reason_override: str | None = None,
) -> dict[str, dict[str, object]]:
    bundle_package = _api_delta_bundle_package_contract(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path,
    )
    if bundle_refs:
        for key, value in bundle_refs.items():
            bundle_package[key] = _optional_text(value)
    missing_required_fields = [
        field_name
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
        if not bundle_package.get(field_name)
    ]
    available_fields = [
        field_name
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
        if bundle_package.get(field_name)
    ]
    receipt_persistence_contract_ready = (
        result_status == "succeeded" and not missing_required_fields
    )
    if status_override is not None:
        status = status_override
    elif result_status == "succeeded":
        status = (
            "ready" if receipt_persistence_contract_ready else "missing_durable_refs"
        )
    else:
        status = "not_applicable_fallback_required"
    if reason_override is not None:
        reason = reason_override
    elif status == "ready":
        reason = "api_provider_delta_commit_refs_complete"
    elif result_status == "succeeded":
        reason = "api_provider_delta_dry_run_does_not_materialize_commits"
    else:
        reason = "api_provider_delta_result_requires_full_rebuild"
    contract = {
        "contract_version": _DELTA_COMMIT_REF_CONTRACT_VERSION,
        "contract_kind": "provider_delta_semantic_package_commit_ref_contract",
        "status": status,
        "reason": reason,
        "required_fields": list(_DELTA_COMMIT_REF_REQUIRED_FIELDS),
        "available_fields": available_fields,
        "missing_required_fields": missing_required_fields,
        "receipt_persistence_contract_ready": receipt_persistence_contract_ready,
        "production_execution_wired": False,
        "would_persist": False,
    }
    bundle_package["commit_ref_contract_version"] = _DELTA_COMMIT_REF_CONTRACT_VERSION
    bundle_package["commit_ref_contract_status"] = status
    bundle_package["commit_ref_contract_reason"] = reason
    bundle_package["receipt_persistence_contract_ready"] = (
        receipt_persistence_contract_ready
    )
    return {
        "commit_ref_contract": contract,
        "bundle_package": bundle_package,
    }


def _api_delta_bundle_package_contract(
    *,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: str | None,
) -> dict[str, object]:
    package_name = _optional_text(package_payload.get("package_name"))
    return {
        "package_key": package_name,
        "package_kind": "api",
        "manifest_toml_path": manifest_path,
        "semantic_owner_module": "aware_api",
        "semantic_package_kind": "api",
        "semantic_contract_provider_key": semantic_contract_payload.get("provider_key"),
        "semantic_contract_role": semantic_contract_payload.get("role"),
        "semantic_contract_name": semantic_contract_payload.get("name"),
        "semantic_root_kind": "api",
        "source_code_package_id": package_payload.get("source_code_package_id"),
        "source_object_instance_graph_commit_id": None,
        "semantic_package_id": None,
        "semantic_branch_id": None,
        "semantic_head_commit_id": None,
        "semantic_object_instance_graph_commit_id": None,
        "semantic_root_id": None,
        "semantic_root_object_instance_graph_commit_id": None,
    }


def _api_delta_bundle_refs_from_materialization_result(
    *,
    result: object,
    branch_id: object,
) -> dict[str, object]:
    api = getattr(result, "api")
    api_package = getattr(result, "api_package")
    package_head_commit_id = getattr(result, "package_head_commit_id", None)
    return {
        "source_code_package_id": getattr(result, "source_code_package_id", None),
        "source_object_instance_graph_commit_id": getattr(
            result,
            "source_object_instance_graph_commit_id",
            None,
        ),
        "semantic_package_id": getattr(api_package, "id", None),
        "semantic_branch_id": branch_id,
        "semantic_head_commit_id": package_head_commit_id,
        "semantic_object_instance_graph_commit_id": package_head_commit_id,
        "semantic_root_id": getattr(api, "id", None),
        "semantic_root_object_instance_graph_commit_id": getattr(
            result,
            "api_object_instance_graph_commit_id",
            None,
        ),
    }


def _api_delta_bundle_refs_from_operation_execution(
    *,
    operation_execution: Mapping[str, object],
) -> dict[str, object]:
    if operation_execution.get("status") != "executed":
        return {}
    function_execution = operation_execution.get("semantic_function_call_execution")
    if not isinstance(function_execution, Mapping):
        return {}
    raw_steps = function_execution.get("steps")
    if not isinstance(raw_steps, (list, tuple)):
        return {}
    invoked_steps = tuple(
        step
        for step in raw_steps
        if isinstance(step, Mapping) and step.get("status") == "invoked"
    )
    if not invoked_steps:
        return {}

    root_step = next(
        (
            step
            for step in invoked_steps
            if step.get("resolution_status") == "create_root"
        ),
        invoked_steps[0],
    )
    root_result = _api_delta_operation_step_result_payload(step=root_step)
    branch_result = _api_delta_last_operation_result_with_branch(
        invoked_steps=invoked_steps,
    )
    root_object_id = _optional_text(
        root_step.get("result_object_id")
    ) or _optional_text(root_result.get("object_id"))
    root_commit_id = _api_delta_operation_result_commit_id(result=root_result)
    branch_id = _optional_text(branch_result.get("branch_id"))

    bundle_refs: dict[str, object] = {}
    if branch_id is not None:
        bundle_refs["semantic_branch_id"] = branch_id
    if root_object_id is not None:
        bundle_refs["semantic_root_id"] = root_object_id
    if root_commit_id is not None:
        bundle_refs["semantic_root_object_instance_graph_commit_id"] = root_commit_id
    return bundle_refs


def _api_delta_bundle_refs_from_package_source_execution(
    *,
    package_source_execution: Mapping[str, object],
) -> dict[str, object]:
    if package_source_execution.get("status") != "executed":
        return {}
    raw_steps = package_source_execution.get("steps")
    if not isinstance(raw_steps, (list, tuple)):
        return {}
    steps = tuple(step for step in raw_steps if isinstance(step, Mapping))
    code_package_step = _api_delta_operation_step_by_name(
        steps=steps,
        operation_name="code_package_build",
    )
    source_delta_step = _api_delta_operation_step_by_name(
        steps=steps,
        operation_name="code_package_apply_delta",
    )
    if not source_delta_step:
        source_delta_step = _api_delta_operation_step_by_name(
            steps=steps,
            operation_name="code_package_upsert_sources",
        )
    source_upsert_step = source_delta_step
    api_package_step = _api_delta_operation_step_by_name(
        steps=steps,
        operation_name="api_product_build",
    )
    source_code_package_id = _optional_text(code_package_step.get("result_object_id"))
    source_commit_id = _api_delta_operation_result_commit_id(
        result=_api_delta_operation_step_result_payload(step=source_upsert_step),
    )
    api_package_id = _optional_text(api_package_step.get("result_object_id"))
    api_package_commit_id = _api_delta_operation_result_commit_id(
        result=_api_delta_operation_step_result_payload(step=api_package_step),
    )
    api_package_branch_id = _optional_text(
        _api_delta_operation_step_result_payload(step=api_package_step).get("branch_id")
    )
    bundle_refs: dict[str, object] = {}
    if source_code_package_id is not None:
        bundle_refs["source_code_package_id"] = source_code_package_id
    if source_commit_id is not None:
        bundle_refs["source_object_instance_graph_commit_id"] = source_commit_id
    if api_package_id is not None:
        bundle_refs["semantic_package_id"] = api_package_id
    if api_package_branch_id is not None:
        bundle_refs["semantic_branch_id"] = api_package_branch_id
    if api_package_commit_id is not None:
        bundle_refs["semantic_head_commit_id"] = api_package_commit_id
        bundle_refs["semantic_object_instance_graph_commit_id"] = api_package_commit_id
    return bundle_refs


def _api_delta_operation_commit_ref_details(
    *,
    operation_execution: Mapping[str, object],
    operation_bundle_refs: Mapping[str, object],
    package_source_bundle_refs: Mapping[str, object],
    package_payload: Mapping[str, object],
) -> dict[str, object]:
    merged_refs: dict[str, object] = {
        **operation_bundle_refs,
        **package_source_bundle_refs,
    }
    source_code_package_id = package_payload.get("source_code_package_id")
    if source_code_package_id and not merged_refs.get("source_code_package_id"):
        merged_refs["source_code_package_id"] = source_code_package_id
    available_fields = [
        field_name
        for field_name in (
            "semantic_branch_id",
            "semantic_head_commit_id",
            "semantic_object_instance_graph_commit_id",
            "semantic_root_id",
            "semantic_root_object_instance_graph_commit_id",
            "source_code_package_id",
            "source_object_instance_graph_commit_id",
            "semantic_package_id",
        )
        if merged_refs.get(field_name)
    ]
    available_required_fields = [
        field_name
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
        if merged_refs.get(field_name)
    ]
    missing_required_fields = [
        field_name
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
        if not merged_refs.get(field_name)
    ]
    status = _api_delta_operation_commit_ref_status(
        operation_execution=operation_execution,
        operation_bundle_refs=operation_bundle_refs,
    )
    return {
        "operation_commit_ref_status": status,
        "operation_commit_ref_reason": _api_delta_operation_commit_ref_reason(
            status=status,
        ),
        "operation_commit_ref_source": "provider_delta_operation_execution",
        "operation_commit_ref_available_fields": available_fields,
        "operation_commit_ref_available_required_fields": available_required_fields,
        "operation_commit_ref_missing_required_fields_after_operation": (
            missing_required_fields
        ),
        "package_source_commit_ref_status": (
            _api_delta_package_source_commit_ref_status(
                package_source_bundle_refs=package_source_bundle_refs,
            )
        ),
        "package_source_commit_ref_available_fields": [
            field_name
            for field_name in _DELTA_PACKAGE_SOURCE_COMMIT_REF_FIELDS
            if package_source_bundle_refs.get(field_name)
        ],
        "package_source_commit_ref_missing_fields": [
            field_name
            for field_name in _DELTA_PACKAGE_SOURCE_COMMIT_REF_FIELDS
            if not package_source_bundle_refs.get(field_name)
        ],
    }


def _api_delta_package_source_commit_ref_status(
    *,
    package_source_bundle_refs: Mapping[str, object],
) -> str:
    if not package_source_bundle_refs:
        return "not_available"
    if all(
        package_source_bundle_refs.get(field_name)
        for field_name in _DELTA_PACKAGE_SOURCE_COMMIT_REF_FIELDS
    ):
        return "ready"
    return "partial_refs"


def _api_delta_operation_commit_ref_status(
    *,
    operation_execution: Mapping[str, object],
    operation_bundle_refs: Mapping[str, object],
) -> str:
    if _api_delta_operation_commit_refs_available(
        operation_bundle_refs=operation_bundle_refs,
    ):
        return "partial_refs"
    if operation_execution.get("flag_requested") is not True:
        return "not_requested"
    if operation_execution.get("status") == "executed":
        return "not_available"
    return "operation_not_complete"


def _api_delta_operation_commit_ref_reason(*, status: str) -> str:
    reasons = {
        "not_available": "api_provider_delta_operation_execution_missing_commit_refs",
        "not_requested": (
            "api_provider_delta_operation_execution_requires_explicit_flag"
        ),
        "operation_not_complete": (
            "api_provider_delta_operation_execution_not_complete"
        ),
        "partial_refs": "api_provider_delta_operation_execution_partial_refs",
    }
    return reasons.get(
        status,
        "api_provider_delta_operation_commit_ref_status_unknown",
    )


def _api_delta_operation_commit_ref_reason_override(
    *,
    combined_bundle_refs: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    package_payload: Mapping[str, object],
) -> str | None:
    bundle_package = _api_delta_bundle_package_contract(
        package_payload=package_payload,
        semantic_contract_payload={},
        manifest_path=None,
    )
    for key, value in combined_bundle_refs.items():
        bundle_package[key] = _optional_text(value)
    if all(
        bundle_package.get(field_name)
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
    ):
        if package_source_execution.get("status") == "executed":
            return "api_provider_delta_operation_execution_materialized_refs"
        return "api_provider_delta_commit_refs_complete"
    if _api_delta_operation_commit_refs_available(
        operation_bundle_refs=combined_bundle_refs,
    ):
        return "api_provider_delta_operation_execution_partial_refs"
    return None


def _api_delta_operation_commit_refs_available(
    *,
    operation_bundle_refs: Mapping[str, object],
) -> bool:
    return any(
        operation_bundle_refs.get(field_name)
        for field_name in (
            "semantic_branch_id",
            "semantic_object_instance_graph_commit_id",
            "semantic_root_object_instance_graph_commit_id",
        )
    )


def _api_delta_operation_step_by_name(
    *,
    steps: tuple[Mapping[str, object], ...],
    operation_name: str,
) -> Mapping[str, object]:
    for step in steps:
        if step.get("operation_name") == operation_name:
            return step
    return {}


def _api_delta_operation_step_result_payload(
    *,
    step: Mapping[str, object],
) -> Mapping[str, object]:
    evidence = step.get("evidence")
    if not isinstance(evidence, Mapping):
        return {}
    result = evidence.get("result")
    if isinstance(result, Mapping):
        return result
    return {}


def _api_delta_last_operation_result_with_branch(
    *,
    invoked_steps: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    for step in reversed(invoked_steps):
        result = _api_delta_operation_step_result_payload(step=step)
        if _optional_text(result.get("branch_id")) is not None:
            return result
    return _api_delta_operation_step_result_payload(step=invoked_steps[-1])


def _api_delta_operation_result_commit_id(
    *,
    result: Mapping[str, object],
) -> str | None:
    commit_id = _optional_text(result.get("head_commit_id")) or _optional_text(
        result.get("commit_id")
    )
    if commit_id is not None:
        return commit_id
    evidence = result.get("evidence")
    if not isinstance(evidence, Mapping):
        return None
    response = evidence.get("response")
    if not isinstance(response, Mapping):
        return None
    return _optional_text(response.get("object_instance_graph_commit_id"))


def _api_delta_commit_ref_probe_enabled(*, request: object) -> bool:
    return getattr(request, "enable_commit_ref_probe", False) is True


def _api_delta_operation_execution_requested(*, request: object) -> bool:
    return (
        getattr(request, _DELTA_OPERATION_EXECUTION_FLAG, False) is True
        or getattr(request, "enable_provider_delta_operation_execution", False) is True
        or getattr(request, "provider_delta_operation_execution_enabled", False) is True
    )


def _api_delta_operation_execution_baseline_block(
    *,
    request: object,
    baseline_preflight: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    resolved_preflight = (
        dict(baseline_preflight)
        if baseline_preflight is not None
        else _api_delta_baseline_hydration_preflight(request=request)
    )
    if resolved_preflight.get("current_head_context_available") is True:
        return None
    evidence = getattr(request, "previous_materialization_evidence", None)
    if (
        resolved_preflight.get("commit_backed_baseline_available") is True
        and resolved_preflight.get("baseline_ref_hydrator_ready") is True
    ):
        return {
            "baseline_evidence_status": "current_head_context_missing",
            "operation_execution_status": "baseline_current_head_missing",
            "operation_execution_reason": (
                "api_provider_delta_operation_execution_requires_hydrated_baseline_current_head"
            ),
            "previous_materialization_evidence_available": (
                isinstance(evidence, Mapping) and evidence.get("available") is True
            ),
            "previous_materialization_current_semantic_object_id_count": (
                _api_delta_previous_evidence_current_object_count(evidence=evidence)
                if isinstance(evidence, Mapping)
                else 0
            ),
            "baseline_hydration_preflight": resolved_preflight,
        }
    if not isinstance(evidence, Mapping):
        return None
    if evidence.get("available") is not True:
        return None
    source = _optional_text(evidence.get("evidence_source"))
    context_available = (
        evidence.get("provider_delta_operation_execution_context_available") is True
    )
    current_object_count = _api_delta_previous_evidence_current_object_count(
        evidence=evidence,
    )
    if context_available or current_object_count > 0:
        return None
    if source not in {None, "reused_workspace_materialization_receipt"}:
        return None
    return {
        "baseline_evidence_status": "semantic_context_missing",
        "operation_execution_status": "baseline_context_missing",
        "operation_execution_reason": (
            "api_provider_delta_operation_execution_requires_semantic_baseline_context"
        ),
        "previous_materialization_evidence_source": source or "minimal",
        "previous_materialization_evidence_available": True,
        "previous_materialization_current_semantic_object_id_count": (
            current_object_count
        ),
        "baseline_hydration_preflight": resolved_preflight,
    }


def _api_delta_result_mode(
    *,
    commit_ref_probe_details: Mapping[str, object],
    operation_execution: Mapping[str, object],
) -> str:
    if operation_execution.get("flag_requested") is True:
        if operation_execution.get("did_execute") is True:
            return "api_provider_delta_operation_execution"
        return "api_provider_delta_operation_execution_requested"
    mode = _optional_text(commit_ref_probe_details.get("mode"))
    if mode is not None:
        return mode
    return "api_provider_delta_result_dry_run"


def _api_delta_operation_execution_status(
    *,
    function_call_execution: Mapping[str, object],
    invoked_count: int,
    blocked_count: int,
    failed_count: int,
) -> str:
    function_execution_status = _optional_text(function_call_execution.get("status"))
    if function_execution_status in {"disabled", "backend_unavailable"}:
        return function_execution_status
    if function_execution_status != "executed":
        return function_execution_status or "unknown"
    if failed_count > 0:
        return "failed"
    if blocked_count > 0:
        return "blocked"
    if invoked_count > 0:
        return "executed"
    return "no_invocations"


def _api_delta_operation_execution_reason(*, execution_status: str) -> str:
    reasons = {
        "backend_unavailable": (
            "api_provider_delta_operation_execution_backend_unavailable"
        ),
        "blocked": "api_provider_delta_operation_execution_blocked_by_resolution",
        "disabled": "api_provider_delta_operation_execution_disabled",
        "executed": "api_provider_delta_operation_execution_invoked",
        "failed": "api_provider_delta_operation_execution_failed",
        "no_invocations": "api_provider_delta_operation_execution_no_invocations",
    }
    return reasons.get(
        execution_status,
        "api_provider_delta_operation_execution_status_unknown",
    )


def _api_delta_commit_ref_probe_context(
    *,
    request: object,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    required_fields = (
        "runtime",
        "index",
        "branch_id",
        "workspace_root",
    )
    context: dict[str, Any] = {}
    missing_fields: list[str] = []
    for field_name in required_fields:
        value = getattr(request, field_name, None)
        if value is None:
            missing_fields.append(field_name)
            continue
        context[field_name] = value
    context["actor_id"] = getattr(request, "actor_id", None)
    if "workspace_root" in context:
        context["workspace_root"] = Path(context["workspace_root"]).resolve()
    return context, tuple(missing_fields)


def _api_delta_request_detail(*, request: object) -> dict[str, object]:
    hints = getattr(request, "delta_cause_hints", None)
    changed_paths = _top_changed_path_payloads(request=request)
    return {
        "baseline_hydration_preflight": _api_delta_baseline_hydration_preflight(
            request=request,
        ),
        "provider_delta_durable_execution_inputs_preflight": (
            _api_delta_durable_execution_inputs_preflight(request=request)
        ),
        "delta_cause_hints": {
            "changed_path_count": _int_attr(hints, "changed_path_count"),
            "source_owned_path_count": _int_attr(hints, "source_owned_path_count"),
            "generated_fallout_path_count": _int_attr(
                hints,
                "generated_fallout_path_count",
            ),
            "top_changed_path_limit": _int_attr(hints, "top_changed_path_limit"),
            "top_changed_paths": changed_paths,
        },
    }


def _workspace_dependency_roots_from_context(
    context: Mapping[str, object] | object,
) -> tuple[Path, ...]:
    if not isinstance(context, Mapping):
        return ()
    payload = context.get(_WORKSPACE_DEPENDENCY_ROOTS_CONTEXT_KEY)
    if not isinstance(payload, Mapping):
        return ()
    raw_roots = payload.get("roots")
    if not isinstance(raw_roots, (list, tuple)):
        return ()
    roots: list[Path] = []
    for item in raw_roots:
        root_value: object
        if isinstance(item, Mapping):
            root_value = item.get("root")
        else:
            root_value = item
        if isinstance(root_value, Path):
            roots.append(root_value.expanduser().resolve())
        elif isinstance(root_value, str) and root_value.strip():
            roots.append(Path(root_value).expanduser().resolve())
    return tuple(dict.fromkeys(roots))


def _resolve_delta_manifest_path(value: object) -> Path | None:
    manifest_path_text = _optional_text(value)
    if manifest_path_text is None:
        return None
    candidate = Path(manifest_path_text).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if not candidate.is_absolute():
        cwd_candidate = (Path.cwd() / candidate).resolve()
        if cwd_candidate.is_file():
            return cwd_candidate
    return None


def _api_provider_delta_context_manifest_path(*, request: object) -> Path | None:
    manifest_path_text = _optional_text(getattr(request, "manifest_path", None))
    if manifest_path_text is None:
        manifest_path_text = _optional_text(
            _model_payload(getattr(request, "package", None)).get("manifest_path")
        )
    if manifest_path_text is None:
        return None
    workspace_root = Path(getattr(request, "workspace_root", Path.cwd()))
    candidate = Path(manifest_path_text).expanduser()
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    return candidate.resolve() if candidate.is_file() else None


def _api_provider_delta_resolved_argument_refs(
    *,
    manifest_path: Path,
    workspace_root: Path,
) -> dict[str, str]:
    from aware_api_runtime.compile_materialization import (  # noqa: WPS433
        resolve_api_package_materialization_spec,
    )

    spec = resolve_api_package_materialization_spec(
        api_toml_path=manifest_path,
        workspace_root=workspace_root,
    )
    refs: dict[str, str] = {}
    refs.update(
        _api_provider_delta_ontology_argument_refs(
            spec.compile_plan_payload.get("api_ontology")
        )
    )
    for raw_api in _mapping_items(spec.compile_plan_payload.get("api_ownership")):
        for raw_capability in _mapping_items(raw_api.get("capabilities")):
            for raw_endpoint in _mapping_items(raw_capability.get("endpoints")):
                raw_request_config = raw_endpoint.get("request_config")
                if not isinstance(raw_request_config, Mapping):
                    continue
                class_ref = _optional_text(raw_request_config.get("class_ref"))
                class_config_id = _optional_text(
                    raw_request_config.get("class_config_id")
                )
                if class_ref is not None and class_config_id is not None:
                    refs[class_ref] = class_config_id
    return dict(sorted(refs.items()))


def _api_provider_delta_ontology_argument_refs(value: object) -> dict[str, str]:
    refs: dict[str, str] = {}
    for raw_plan in _mapping_items(value):
        for raw_request_config in _mapping_items(
            raw_plan.get("capability_endpoint_request_configs")
        ):
            class_ref = _optional_text(raw_request_config.get("class_ref"))
            class_config_id = _optional_text(raw_request_config.get("class_config_id"))
            if class_ref is not None and class_config_id is not None:
                refs[class_ref] = class_config_id
    return refs


def _mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping_payload(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _model_payload(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return dict(model_dump(mode="json"))
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _api_client_service_protocol_compile_parity_receipts(
    *,
    request: SemanticPackageMaterializationRequest,
    result: object,
    artifact_ownership_receipts: tuple[dict[str, object], ...],
    language_post_step_receipts: tuple[dict[str, object], ...] = (),
) -> tuple[dict[str, object], ...]:
    available_evidence = _api_compile_parity_available_evidence(
        artifact_ownership_receipts=artifact_ownership_receipts,
        language_post_step_receipts=language_post_step_receipts,
    )
    required_evidence = _api_compile_parity_required_evidence(request=request)
    missing_required_evidence = tuple(
        evidence for evidence in required_evidence if evidence not in available_evidence
    )
    runtime_manifest_payload = _api_compile_parity_runtime_manifest_payload(
        artifact_ownership_receipts=artifact_ownership_receipts,
        workspace_root=request.workspace_root,
    )
    api = getattr(result, "api", None)
    api_package = getattr(result, "api_package", None)
    source_object_instance_graph_commit_id = getattr(
        result,
        "source_object_instance_graph_commit_id",
        None,
    )
    payload: dict[str, object] = {
        "schema": _API_COMPILE_PARITY_RECEIPT_SCHEMA,
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "semantic_owner": "aware_api.provider",
        "producer_key": "aware_api.api_client_service_protocol",
        "receipt_kind": _API_COMPILE_PARITY_RECEIPT_KIND,
        "status": (
            "compile_equivalent" if not missing_required_evidence else "incomplete"
        ),
        "env_artifacts_required": False,
        "replacement_target": "aware-cli compile api",
        "workspace_command": "workspace materialize",
        "package_name": _optional_text(getattr(api_package, "name", None)),
        "api_package_name": _optional_text(getattr(api_package, "name", None)),
        "api_package_id": _optional_text(getattr(api_package, "id", None)),
        "api_name": _optional_text(getattr(api, "name", None)),
        "api_id": _optional_text(getattr(api, "id", None)),
        "api_toml_path": request.manifest_path.as_posix(),
        "semantic_branch_id": str(request.branch_id),
        "source_code_package_id": _optional_text(
            getattr(result, "source_code_package_id", None)
        ),
        "source_object_instance_graph_commit_id": _optional_text(
            source_object_instance_graph_commit_id
        ),
        "api_object_instance_graph_commit_id": _optional_text(
            getattr(result, "api_object_instance_graph_commit_id", None)
        ),
        "api_package_object_instance_graph_commit_id": _optional_text(
            getattr(result, "package_head_commit_id", None)
        ),
        "runtime_compile_plan_hash": _optional_text(
            getattr(result, "runtime_compile_plan_hash", None)
        ),
        "source_files": tuple(getattr(result, "source_files", ()) or ()),
        "required_evidence": required_evidence,
        "available_evidence": tuple(sorted(available_evidence)),
        "missing_required_evidence": missing_required_evidence,
        "api_client": _api_compile_parity_component_payload(
            component_key="api_client",
            artifact_role="public_package_file",
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "service_protocol": _api_compile_parity_component_payload(
            component_key="service_protocol",
            artifact_role="service_protocol_package_file",
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "dart_public_package": _api_compile_parity_component_payload(
            component_key="dart_public_package",
            artifact_role="dart_public_package_file",
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "language_post_steps": _api_compile_parity_post_step_payload(
            language_post_step_receipts=language_post_step_receipts,
        ),
        "runtime_manifest": _api_compile_parity_runtime_manifest_detail(
            artifact_ownership_receipts=artifact_ownership_receipts,
            runtime_manifest_payload=runtime_manifest_payload,
        ),
        "compile_plan": _api_compile_parity_compile_plan_detail(
            artifact_ownership_receipts=artifact_ownership_receipts,
            runtime_manifest_payload=runtime_manifest_payload,
            runtime_compile_plan_hash=getattr(
                result,
                "runtime_compile_plan_hash",
                None,
            ),
        ),
        "dependency_graph_mode": _optional_text(
            runtime_manifest_payload.get("dependency_graph_mode")
        ),
        "accessible_dependency_graph_count": _int_from_mapping(
            runtime_manifest_payload,
            "accessible_dependency_graph_count",
        ),
        "artifact_role_counts": _api_compile_parity_artifact_role_counts(
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "artifact_ownership_receipt_count": len(artifact_ownership_receipts),
        "available_output_keys": _api_compile_parity_available_output_keys(
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "compatibility_artifact_family": "api_product_runtime",
        "compatibility_output_key": "api.product_runtime_file",
    }
    digest = _api_compile_parity_digest(payload)
    payload["digest_algorithm"] = "sha256"
    payload["digest"] = digest
    payload["receipt_id"] = f"sha256:{digest}"
    return (payload,)


def _api_compile_parity_available_evidence(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    language_post_step_receipts: tuple[Mapping[str, object], ...] = (),
) -> frozenset[str]:
    evidence: set[str] = set()
    for receipt in artifact_ownership_receipts:
        if not _api_compile_parity_receipt_is_available(receipt):
            continue
        artifact_role = _optional_text(receipt.get("artifact_role"))
        if artifact_role == "public_package_file":
            evidence.add("api_client")
        elif artifact_role == "service_protocol_package_file":
            evidence.add("service_protocol")
        elif artifact_role == "dart_public_package_file":
            evidence.add("dart_public_package")
        if _api_compile_parity_receipt_path_matches(
            receipt=receipt,
            suffix="api.manifest.json",
        ):
            evidence.add("runtime_manifest")
        if _api_compile_parity_receipt_path_matches(
            receipt=receipt,
            suffix="api.compile_plan.json",
        ):
            evidence.add("compile_plan")
    for receipt in language_post_step_receipts:
        if _optional_text(receipt.get("status")) != "succeeded":
            continue
        if _optional_text(receipt.get("tool_id")) == "dart.build_runner":
            evidence.add("dart_build_runner")
    return frozenset(evidence)


def _api_compile_parity_required_evidence(
    *,
    request: SemanticPackageMaterializationRequest,
) -> tuple[str, ...]:
    required = list(_API_COMPILE_PARITY_REQUIRED_EVIDENCE)
    try:
        declares_dart = _api_manifest_declares_dart_public_package(
            toml_path=request.manifest_path,
            workspace_root=request.workspace_root,
        )
    except Exception:
        declares_dart = False
    if declares_dart:
        required.extend(("dart_public_package", "dart_build_runner"))
    return tuple(required)


def _api_compile_parity_component_payload(
    *,
    component_key: str,
    artifact_role: str,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    receipts = tuple(
        receipt
        for receipt in artifact_ownership_receipts
        if _api_compile_parity_receipt_is_available(receipt)
        if _optional_text(receipt.get("artifact_role")) == artifact_role
    )
    return {
        "component_key": component_key,
        "status": "available" if receipts else "missing",
        "artifact_role": artifact_role,
        "artifact_count": len(receipts),
        "manifest_paths": _api_compile_parity_manifest_paths(receipts=receipts),
    }


def _api_compile_parity_post_step_payload(
    *,
    language_post_step_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    succeeded = tuple(
        receipt
        for receipt in language_post_step_receipts
        if _optional_text(receipt.get("status")) == "succeeded"
    )
    return {
        "status": "available" if succeeded else "missing",
        "receipt_count": len(language_post_step_receipts),
        "succeeded_receipt_count": len(succeeded),
        "tool_ids": tuple(
            sorted(
                {
                    tool_id
                    for receipt in succeeded
                    if (tool_id := _optional_text(receipt.get("tool_id"))) is not None
                }
            )
        ),
    }


def _api_compile_parity_runtime_manifest_detail(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    runtime_manifest_payload: Mapping[str, object],
) -> dict[str, object]:
    manifest_path = _api_compile_parity_first_manifest_path(
        artifact_ownership_receipts=artifact_ownership_receipts,
        suffix="api.manifest.json",
    )
    return {
        "status": ("available" if manifest_path is not None else "missing"),
        "manifest_path": manifest_path,
        "payload_read": bool(runtime_manifest_payload),
        "dependency_graph_mode": _optional_text(
            runtime_manifest_payload.get("dependency_graph_mode")
        ),
        "accessible_dependency_graph_count": _int_from_mapping(
            runtime_manifest_payload,
            "accessible_dependency_graph_count",
        ),
        "public_package_materialized": (
            runtime_manifest_payload.get("public_package_materialized") is True
        ),
        "service_protocol_materialized": (
            runtime_manifest_payload.get("service_protocol_materialized") is True
        ),
        "compile_plan_artifact_hash": _optional_text(
            runtime_manifest_payload.get("compile_plan_artifact_hash")
        ),
    }


def _api_compile_parity_compile_plan_detail(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    runtime_manifest_payload: Mapping[str, object],
    runtime_compile_plan_hash: object | None,
) -> dict[str, object]:
    compile_plan_path = _api_compile_parity_first_manifest_path(
        artifact_ownership_receipts=artifact_ownership_receipts,
        suffix="api.compile_plan.json",
    )
    return {
        "status": "available" if compile_plan_path is not None else "missing",
        "manifest_path": compile_plan_path,
        "runtime_compile_plan_hash": _optional_text(runtime_compile_plan_hash),
        "runtime_manifest_compile_plan_artifact_hash": _optional_text(
            runtime_manifest_payload.get("compile_plan_artifact_hash")
        ),
    }


def _api_compile_parity_runtime_manifest_payload(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    workspace_root: Path,
) -> dict[str, object]:
    for receipt in artifact_ownership_receipts:
        if not _api_compile_parity_receipt_is_available(receipt):
            continue
        if not _api_compile_parity_receipt_path_matches(
            receipt=receipt,
            suffix="api.manifest.json",
        ):
            continue
        path = _api_compile_parity_receipt_path(
            receipt=receipt,
            workspace_root=workspace_root,
        )
        if path is None:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, Mapping):
            return _mapping_payload(payload)
    return {}


def _api_compile_parity_first_manifest_path(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    suffix: str,
) -> str | None:
    paths = tuple(
        _optional_text(receipt.get("manifest_path"))
        for receipt in artifact_ownership_receipts
        if _api_compile_parity_receipt_is_available(receipt)
        if _api_compile_parity_receipt_path_matches(
            receipt=receipt,
            suffix=suffix,
        )
    )
    return next((path for path in paths if path is not None), None)


def _api_compile_parity_receipt_path_matches(
    *,
    receipt: Mapping[str, object],
    suffix: str,
) -> bool:
    for key in ("manifest_path", "path"):
        value = _optional_text(receipt.get(key))
        if value is not None and value.endswith(suffix):
            return True
    return False


def _api_compile_parity_receipt_path(
    *,
    receipt: Mapping[str, object],
    workspace_root: Path,
) -> Path | None:
    raw_path = _optional_text(receipt.get("path"))
    if raw_path is None:
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = workspace_root / path
    return path


def _api_compile_parity_receipt_is_available(
    receipt: Mapping[str, object],
) -> bool:
    return _optional_text(receipt.get("status")) in (
        _API_COMPILE_PARITY_AVAILABLE_STATUSES
    )


def _api_compile_parity_artifact_role_counts(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for receipt in artifact_ownership_receipts:
        if not _api_compile_parity_receipt_is_available(receipt):
            continue
        role = _optional_text(receipt.get("artifact_role"))
        if role is None:
            continue
        counts[role] = counts.get(role, 0) + 1
    return dict(sorted(counts.items()))


def _api_compile_parity_available_output_keys(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    output_keys: set[str] = set()
    for receipt in artifact_ownership_receipts:
        if not _api_compile_parity_receipt_is_available(receipt):
            continue
        output_key = _optional_text(receipt.get("output_key"))
        if output_key is not None:
            output_keys.add(output_key)
    return tuple(sorted(output_keys))


def _api_compile_parity_manifest_paths(
    *,
    receipts: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    paths: set[str] = set()
    for receipt in receipts:
        manifest_path = _optional_text(receipt.get("manifest_path"))
        if manifest_path is not None:
            paths.add(manifest_path)
    return tuple(sorted(paths))


def _int_from_mapping(value: Mapping[str, object], key: str) -> int | None:
    raw_value = value.get(key)
    if isinstance(raw_value, bool):
        return None
    if isinstance(raw_value, int):
        return raw_value
    if raw_value is None:
        return None
    try:
        return int(str(raw_value))
    except ValueError:
        return None


def _api_compile_parity_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _api_product_runtime_artifact_ownership_receipts_for_materialization(
    *,
    request: SemanticPackageMaterializationRequest,
    package_name: str,
    runtime_compile_plan_hash: object | None,
    source_files: tuple[str, ...],
    source_code_package_id: object | None,
    source_object_instance_graph_commit_id: object | None,
    dependency_repo_roots: tuple[Path, ...] = (),
    product_runtime_compile_result: object | None = None,
    dart_public_package_compile_result: object | None = None,
) -> tuple[dict[str, object], ...]:
    try:
        can_reuse_existing_runtime = (
            product_runtime_compile_result is None
            and dart_public_package_compile_result is None
            and not _api_manifest_declares_api_dto_exports(
                manifest_path=request.manifest_path,
            )
        )
        if can_reuse_existing_runtime:
            existing_receipts = (
                _api_product_runtime_artifact_ownership_receipts_from_existing_runtime(
                    manifest_path=request.manifest_path,
                    workspace_root=request.workspace_root,
                    package_name=package_name,
                    expected_runtime_compile_plan_hash=runtime_compile_plan_hash,
                    expected_source_files=source_files,
                    dependency_repo_roots=dependency_repo_roots,
                    source_code_package_id=source_code_package_id,
                    source_object_instance_graph_commit_id=(
                        source_object_instance_graph_commit_id
                    ),
                )
            )
            if existing_receipts is not None:
                return existing_receipts
        compile_result = product_runtime_compile_result
        if compile_result is None:
            compile_result = _compile_api_workspace_for_product_runtime_receipts(
                toml_path=request.manifest_path,
                workspace_root=request.workspace_root,
                dependency_repo_roots=dependency_repo_roots,
            )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        if service_protocol_materialization is None:
            return (
                _missing_api_product_runtime_artifact_ownership_receipt(
                    package_name=package_name,
                    workspace_root=request.workspace_root,
                    api_toml_path=request.manifest_path,
                    error="api_service_protocol_materialization_unavailable",
                    source_code_package_id=source_code_package_id,
                    source_object_instance_graph_commit_id=(
                        source_object_instance_graph_commit_id
                    ),
                ),
            )
        return (
            *_api_product_runtime_artifact_ownership_receipts(
                package_name=package_name,
                workspace_root=request.workspace_root,
                runtime_package_dir=(
                    service_protocol_materialization.runtime_package_dir
                ),
                source_code_package_id=source_code_package_id,
                source_object_instance_graph_commit_id=(
                    source_object_instance_graph_commit_id
                ),
            ),
            *_api_dto_artifact_ownership_receipts(
                api_package_name=package_name,
                workspace_root=request.workspace_root,
                dto_materializations=tuple(
                    getattr(
                        compile_result,
                        "api_dto_package_materializations",
                        (),
                    )
                    or ()
                ),
            ),
            *_api_dart_public_package_artifact_ownership_receipts(
                package_name=package_name,
                workspace_root=request.workspace_root,
                dart_public_package_compile_result=(dart_public_package_compile_result),
                source_code_package_id=source_code_package_id,
                source_object_instance_graph_commit_id=(
                    source_object_instance_graph_commit_id
                ),
            ),
        )
    except Exception as exc:
        return (
            _missing_api_product_runtime_artifact_ownership_receipt(
                package_name=package_name,
                workspace_root=request.workspace_root,
                api_toml_path=request.manifest_path,
                error=f"{type(exc).__name__}: {exc}",
                source_code_package_id=source_code_package_id,
                source_object_instance_graph_commit_id=(
                    source_object_instance_graph_commit_id
                ),
            ),
        )


def _api_product_runtime_artifact_ownership_receipts_for_compile_plan_input(
    *,
    request: SemanticPackageMaterializationRequest,
    package_name: str,
    compile_plan_payload: Mapping[str, object],
    compile_plan_path: Path | None,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    dependency_repo_roots: tuple[Path, ...] = (),
) -> tuple[dict[str, object], ...]:
    manifest_path = compile_plan_path or request.manifest_path
    source_api_toml_path = _source_api_toml_path_for_compile_plan_input(
        request=request,
        package_name=package_name,
    )
    try:
        compile_result = _compile_api_product_runtime_from_compile_plan(
            compile_plan_payload=compile_plan_payload,
            compile_plan_path=manifest_path,
            source_api_toml_path=source_api_toml_path,
            workspace_root=request.workspace_root,
            accessible_graphs=accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
        )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        if service_protocol_materialization is None:
            return (
                _missing_api_product_runtime_artifact_ownership_receipt(
                    package_name=package_name,
                    workspace_root=request.workspace_root,
                    api_toml_path=manifest_path,
                    error="api_service_protocol_materialization_unavailable",
                    source_code_package_id=None,
                    source_object_instance_graph_commit_id=None,
                ),
            )
        return (
            *_api_product_runtime_artifact_ownership_receipts(
                package_name=package_name,
                workspace_root=request.workspace_root,
                runtime_package_dir=(
                    service_protocol_materialization.runtime_package_dir
                ),
                source_code_package_id=None,
                source_object_instance_graph_commit_id=None,
            ),
            *_api_dto_artifact_ownership_receipts(
                api_package_name=package_name,
                workspace_root=request.workspace_root,
                dto_materializations=tuple(
                    getattr(
                        compile_result,
                        "api_dto_package_materializations",
                        (),
                    )
                    or ()
                ),
            ),
        )
    except Exception as exc:
        return (
            _missing_api_product_runtime_artifact_ownership_receipt(
                package_name=package_name,
                workspace_root=request.workspace_root,
                api_toml_path=manifest_path,
                error=f"{type(exc).__name__}: {exc}",
                source_code_package_id=None,
                source_object_instance_graph_commit_id=None,
            ),
        )


def _source_api_toml_path_for_compile_plan_input(
    *,
    request: SemanticPackageMaterializationRequest,
    package_name: str,
) -> Path | None:
    materialization_input = request.materialization_input
    if materialization_input is not None and materialization_input.source_manifest_path:
        source_path = _resolve_workspace_relative_path(
            workspace_root=request.workspace_root,
            path=Path(str(materialization_input.source_manifest_path)),
        )
        if _api_toml_path_matches_package(
            path=source_path,
            package_name=package_name,
        ):
            return source_path

    direct_matches = _find_api_toml_paths_for_package(
        search_root=(request.workspace_root / "apis").resolve(),
        package_name=package_name,
        recursive=False,
    )
    if len(direct_matches) == 1:
        return direct_matches[0]

    matches = _find_api_toml_paths_for_package(
        search_root=request.workspace_root.resolve(),
        package_name=package_name,
        recursive=True,
    )
    if len(matches) == 1:
        return matches[0]
    return None


def _resolve_workspace_relative_path(*, workspace_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (workspace_root / path).resolve()


def _find_api_toml_paths_for_package(
    *,
    search_root: Path,
    package_name: str,
    recursive: bool,
) -> tuple[Path, ...]:
    if not search_root.exists():
        return ()
    paths = (
        search_root.rglob("aware.api.toml")
        if recursive
        else search_root.glob("*/aware.api.toml")
    )
    return tuple(
        sorted(
            path.resolve()
            for path in paths
            if path.is_file()
            and not any(part in {".aware", "_aware", ".venv"} for part in path.parts)
            and _api_toml_path_matches_package(
                path=path,
                package_name=package_name,
            )
        )
    )


def _api_toml_path_matches_package(*, path: Path, package_name: str) -> bool:
    if path.name != "aware.api.toml" or not path.is_file():
        return False
    try:
        spec = load_aware_api_toml_spec(toml_path=path)
    except (AwareApiTomlError, OSError):
        return False
    return (spec.api.package_name or "").strip().casefold() == package_name.casefold()


def _api_product_runtime_artifact_ownership_receipts_for_delta(
    *,
    manifest_path: Path,
    package_name: str,
    source_code_package_id: object | None,
    source_object_instance_graph_commit_id: object | None,
) -> tuple[dict[str, object], ...]:
    workspace_root = _api_delta_workspace_root_from_manifest_path(
        manifest_path=manifest_path
    )
    try:
        workspace = APIWorkspace.from_toml(toml_path=manifest_path)
        workspace_root = workspace.repo_root
        compile_result = _compile_api_workspace_for_product_runtime_receipts(
            toml_path=manifest_path,
            workspace_root=workspace_root,
        )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        if service_protocol_materialization is None:
            return (
                _missing_api_product_runtime_artifact_ownership_receipt(
                    package_name=package_name,
                    workspace_root=workspace_root,
                    api_toml_path=manifest_path,
                    error="api_service_protocol_materialization_unavailable",
                    source_code_package_id=source_code_package_id,
                    source_object_instance_graph_commit_id=(
                        source_object_instance_graph_commit_id
                    ),
                ),
            )
        return (
            *_api_product_runtime_artifact_ownership_receipts(
                package_name=package_name,
                workspace_root=workspace_root,
                runtime_package_dir=(
                    service_protocol_materialization.runtime_package_dir
                ),
                source_code_package_id=source_code_package_id,
                source_object_instance_graph_commit_id=(
                    source_object_instance_graph_commit_id
                ),
            ),
            *_api_dto_artifact_ownership_receipts(
                api_package_name=package_name,
                workspace_root=workspace_root,
                dto_materializations=tuple(
                    getattr(
                        compile_result,
                        "api_dto_package_materializations",
                        (),
                    )
                    or ()
                ),
            ),
        )
    except Exception as exc:
        return (
            _missing_api_product_runtime_artifact_ownership_receipt(
                package_name=package_name,
                workspace_root=workspace_root,
                api_toml_path=manifest_path,
                error=f"{type(exc).__name__}: {exc}",
                source_code_package_id=source_code_package_id,
                source_object_instance_graph_commit_id=(
                    source_object_instance_graph_commit_id
                ),
            ),
        )


def _api_product_runtime_artifact_ownership_receipts_from_existing_runtime(
    *,
    manifest_path: Path,
    workspace_root: Path,
    package_name: str,
    expected_runtime_compile_plan_hash: object | None,
    expected_source_files: tuple[str, ...] | None,
    dependency_repo_roots: tuple[Path, ...] = (),
    source_code_package_id: object | None,
    source_object_instance_graph_commit_id: object | None,
) -> tuple[dict[str, object], ...] | None:
    if not package_name:
        return None
    runtime_compile_plan_hash = (
        str(expected_runtime_compile_plan_hash).strip()
        if expected_runtime_compile_plan_hash is not None
        else ""
    )
    if not runtime_compile_plan_hash:
        return None
    runtime_package_dir = _api_runtime_package_dir_for_manifest(
        manifest_path=manifest_path,
        workspace_root=workspace_root,
    )
    runtime_manifest_path = runtime_package_dir / "api.manifest.json"
    try:
        manifest_payload = json.loads(
            runtime_manifest_path.read_text(encoding="utf-8") or "{}",
        )
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(manifest_payload, Mapping):
        return None
    if not _existing_api_runtime_manifest_matches_request(
        manifest_payload=manifest_payload,
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        package_name=package_name,
        runtime_compile_plan_hash=runtime_compile_plan_hash,
        source_files=expected_source_files,
    ):
        return None
    if not _existing_api_runtime_accessible_dependency_graphs_match_request(
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        runtime_package_dir=runtime_package_dir,
        dependency_repo_roots=dependency_repo_roots,
    ):
        return None
    if not _existing_api_runtime_semantics_match_request(
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        runtime_package_dir=runtime_package_dir,
        dependency_repo_roots=dependency_repo_roots,
    ):
        return None
    try:
        return _api_product_runtime_artifact_ownership_receipts(
            package_name=package_name,
            workspace_root=workspace_root,
            runtime_package_dir=runtime_package_dir,
            source_code_package_id=source_code_package_id,
            source_object_instance_graph_commit_id=(
                source_object_instance_graph_commit_id
            ),
        )
    except Exception:
        return None


def _api_manifest_declares_api_dto_exports(*, manifest_path: Path) -> bool:
    try:
        snapshot = APIWorkspace.from_toml(toml_path=manifest_path).build_snapshot()
    except Exception:
        return False
    return any(
        getattr(getattr(export, "kind", None), "value", None) == "api_dto"
        for export in snapshot.spec.semantic_package_exports
    )


def _api_runtime_package_dir_for_manifest(
    *,
    manifest_path: Path,
    workspace_root: Path,
) -> Path:
    from aware_api_runtime.compile import (  # noqa: WPS433
        resolve_api_runtime_package_dir,
    )

    workspace = APIWorkspace.from_toml(
        toml_path=manifest_path,
        repo_root=workspace_root,
    )
    return resolve_api_runtime_package_dir(snapshot=workspace.build_snapshot())


def _existing_api_runtime_manifest_matches_request(
    *,
    manifest_payload: Mapping[object, object],
    manifest_path: Path,
    workspace_root: Path,
    package_name: str,
    runtime_compile_plan_hash: str,
    source_files: tuple[str, ...] | None,
) -> bool:
    if manifest_payload.get("status") != "ok":
        return False
    if manifest_payload.get("api_package_name") != package_name:
        return False
    if not manifest_payload.get("public_package_materialized"):
        return False
    if not manifest_payload.get("service_protocol_materialized"):
        return False
    if runtime_compile_plan_hash:
        if (
            manifest_payload.get("compile_plan_artifact_hash")
            != runtime_compile_plan_hash
        ):
            return False
    if source_files is not None:
        manifest_source_files = manifest_payload.get("source_files")
        if not isinstance(manifest_source_files, list):
            return False
        if tuple(str(item) for item in manifest_source_files) != tuple(
            source_files,
        ):
            return False
    try:
        manifest_relpath = (
            manifest_path.resolve()
            .relative_to(
                workspace_root.resolve(),
            )
            .as_posix()
        )
    except ValueError:
        return False
    return manifest_payload.get("api_toml_relpath") == manifest_relpath


def _existing_api_runtime_accessible_dependency_graphs_match_request(
    *,
    manifest_path: Path,
    workspace_root: Path,
    runtime_package_dir: Path,
    dependency_repo_roots: tuple[Path, ...] = (),
) -> bool:
    from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: WPS433
        _resolve_api_dependency_packages,
        load_api_accessible_dependency_graphs_from_runtime_artifact,
    )

    try:
        snapshot = APIWorkspace.from_toml(
            toml_path=manifest_path,
            repo_root=workspace_root,
        ).build_snapshot()
        expected_packages = _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    except Exception:
        return False
    if not expected_packages:
        return True
    try:
        accessible_graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
            runtime_package_dir=runtime_package_dir,
        )
    except Exception:
        return False
    actual_keys: set[str] = set()
    for graph in accessible_graphs:
        actual_keys.update(
            _casefolded_non_empty_texts(
                getattr(graph, "name", None),
                getattr(graph, "fqn_prefix", None),
            )
        )
    for package in expected_packages:
        expected_keys = _casefolded_non_empty_texts(
            package.package_name,
            getattr(package.spec.package, "package_name", None),
            getattr(package.spec.package, "fqn_prefix", None),
        )
        if not expected_keys.intersection(actual_keys):
            return False
    return True


def _existing_api_runtime_semantics_match_request(
    *,
    manifest_path: Path,
    workspace_root: Path,
    runtime_package_dir: Path,
    dependency_repo_roots: tuple[Path, ...] = (),
) -> bool:
    from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: WPS433
        API_RUNTIME_SEMANTICS_FILENAME,
        _resolve_api_dependency_packages,
    )

    semantics_path = runtime_package_dir / API_RUNTIME_SEMANTICS_FILENAME
    try:
        payload = json.loads(semantics_path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, Mapping):
        return False
    if payload.get("kind") != "api.runtime_semantics":
        return False
    try:
        snapshot = APIWorkspace.from_toml(
            toml_path=manifest_path,
            repo_root=workspace_root,
        ).build_snapshot()
        expected_packages = _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    except Exception:
        return False
    dependency_payloads = payload.get("dependency_packages")
    if not isinstance(dependency_payloads, list):
        return False
    dependency_payload_by_name = {
        str(item.get("package_name")).strip(): item
        for item in dependency_payloads
        if isinstance(item, Mapping) and str(item.get("package_name")).strip()
    }
    for package in expected_packages:
        package_payload = dependency_payload_by_name.get(package.package_name)
        if package_payload is None:
            return False
        if not _runtime_semantics_path_field_matches(
            package_payload=package_payload,
            workspace_root=workspace_root,
            key="aware_toml_relpath",
            expected_path=package.aware_toml_path,
        ):
            return False
        if not _runtime_semantics_path_field_matches(
            package_payload=package_payload,
            workspace_root=workspace_root,
            key="package_root_relpath",
            expected_path=package.package_root,
        ):
            return False
        if not _runtime_semantics_path_field_matches(
            package_payload=package_payload,
            workspace_root=workspace_root,
            key="python_root_relpath",
            expected_path=package.python_root,
        ):
            return False
        if not _runtime_semantics_path_field_matches(
            package_payload=package_payload,
            workspace_root=workspace_root,
            key="runtime_root_relpath",
            expected_path=package.runtime_root,
        ):
            return False
    return True


def _runtime_semantics_path_field_matches(
    *,
    package_payload: Mapping[object, object],
    workspace_root: Path,
    key: str,
    expected_path: Path,
) -> bool:
    value = package_payload.get(key)
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    if not path.is_absolute():
        path = workspace_root / path
    return path.expanduser().resolve() == expected_path.resolve()


def _casefolded_non_empty_texts(*values: object) -> set[str]:
    texts: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            texts.add(text.casefold())
    return texts


def _api_delta_workspace_root_from_manifest_path(*, manifest_path: Path) -> Path:
    for parent in (manifest_path.parent, *manifest_path.parents):
        if (parent / "aware.workspace.toml").is_file():
            return parent.resolve()
    return manifest_path.parent.resolve()


def _compile_api_workspace_for_product_runtime_receipts(
    *,
    toml_path: Path,
    workspace_root: Path,
    dependency_repo_roots: tuple[Path, ...] = (),
) -> object:
    from aware_api_runtime.compile import (  # noqa: WPS433
        compile_api_workspace,
        refresh_api_workspace_from_runtime_artifacts,
    )

    compile_result = compile_api_workspace(
        toml_path=toml_path,
        repo_root=workspace_root,
        materialize_service_protocol=True,
        public_package_target_language=CodeLanguage.python,
        dependency_repo_roots=dependency_repo_roots,
    )
    if _api_manifest_declares_dart_public_package(
        toml_path=toml_path,
        workspace_root=workspace_root,
    ):
        refresh_api_workspace_from_runtime_artifacts(
            toml_path=toml_path,
            repo_root=workspace_root,
            refresh_public_package=True,
            public_package_target_language=CodeLanguage.dart,
            dependency_repo_roots=dependency_repo_roots,
        )
    return compile_result


def _api_manifest_declares_dart_public_package(
    *,
    toml_path: Path,
    workspace_root: Path,
) -> bool:
    snapshot = APIWorkspace.from_toml(
        toml_path=toml_path,
        repo_root=workspace_root,
    ).build_snapshot()
    return snapshot.spec.targets.dart is not None


def _compile_api_product_runtime_from_compile_plan(
    *,
    compile_plan_payload: Mapping[str, object],
    compile_plan_path: Path,
    source_api_toml_path: Path | None,
    workspace_root: Path,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    dependency_repo_roots: tuple[Path, ...] = (),
) -> object:
    from aware_api_runtime.compile import (  # noqa: WPS433
        compile_api_product_runtime_from_compile_plan_payload,
    )

    return compile_api_product_runtime_from_compile_plan_payload(
        compile_plan_payload=compile_plan_payload,
        compile_plan_path=compile_plan_path,
        source_api_toml_path=source_api_toml_path,
        repo_root=workspace_root,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )


def _api_product_runtime_artifact_ownership_receipts(
    *,
    package_name: str,
    workspace_root: Path,
    runtime_package_dir: Path,
    source_code_package_id: object | None,
    source_object_instance_graph_commit_id: object | None,
) -> tuple[dict[str, object], ...]:
    from aware_api_runtime.build import (  # noqa: WPS433
        api_product_runtime_artifact_ownership_receipts,
    )

    return api_product_runtime_artifact_ownership_receipts(
        package_name=package_name,
        workspace_root=workspace_root,
        runtime_package_dir=runtime_package_dir,
        source_code_package_id=source_code_package_id,
        source_object_instance_graph_commit_id=source_object_instance_graph_commit_id,
    )


def _api_dart_public_package_artifact_ownership_receipts(
    *,
    package_name: str,
    workspace_root: Path,
    dart_public_package_compile_result: object | None,
    source_code_package_id: object | None,
    source_object_instance_graph_commit_id: object | None,
) -> tuple[dict[str, object], ...]:
    public_package_materialization = getattr(
        dart_public_package_compile_result,
        "public_package_materialization",
        None,
    )
    if public_package_materialization is None:
        return ()
    render_job = getattr(public_package_materialization, "render_job", None)
    target = getattr(render_job, "target", None)
    package_root = getattr(target, "package_root", None)
    if package_root is None:
        return ()
    resolved_root = Path(package_root).resolve()
    if not resolved_root.is_dir():
        raise RuntimeError(
            "API Dart public API package root is missing after materialization: "
            f"package_name={package_name!r} package_root={resolved_root}"
        )
    receipts: list[dict[str, object]] = []
    for path in _iter_api_product_package_files(root=resolved_root):
        relative_path = _workspace_relative_path(
            path=path,
            workspace_root=workspace_root,
        )
        content = path.read_bytes()
        receipt: dict[str, object] = {
            "producer_provider_key": "aware_api",
            "producer_key": "aware_api.dart_public_package",
            "producer_kind": "api_product_build",
            "semantic_owner": "aware_api.provider",
            "target_language_plugin_id": CodeLanguage.dart.value,
            "output_key": "dart.public_package_file",
            "output_kind": "file",
            "artifact_family": "api_product_runtime",
            "artifact_role": "dart_public_package_file",
            "artifact_key": f"{package_name}:dart_public_package_file:{relative_path}",
            "package_name": package_name,
            "path": path.as_posix(),
            "manifest_path": relative_path,
            "digest": sha256(content).hexdigest(),
            "digest_algorithm": "sha256",
            "size_bytes": len(content),
            "status": "available",
            "required_for": [
                "workspace_revision",
                "api_client",
                "dart_public_api_package",
            ],
            "runtime_contract_version": "aware.api.dart_public_api_package.v1",
            "provider_payload": {
                "workspace_relative_path": relative_path,
                "package_root": _workspace_relative_path(
                    path=resolved_root,
                    workspace_root=workspace_root,
                ),
            },
        }
        if source_code_package_id is not None:
            receipt["source_code_package_id"] = str(source_code_package_id)
        if source_object_instance_graph_commit_id is not None:
            receipt["source_object_instance_graph_commit_id"] = str(
                source_object_instance_graph_commit_id
            )
        receipts.append(receipt)
    return tuple(
        sorted(
            receipts,
            key=lambda item: str(item["manifest_path"]),
        )
    )


def _iter_api_product_package_files(*, root: Path) -> tuple[Path, ...]:
    excluded_parts = {".dart_tool", ".pub", "build", ".git"}
    return tuple(
        sorted(
            (
                path.resolve()
                for path in root.rglob("*")
                if path.is_file()
                and not path.is_symlink()
                and not any(part in excluded_parts for part in path.parts)
            ),
            key=lambda path: path.as_posix(),
        )
    )


def _missing_api_product_runtime_artifact_ownership_receipt(
    *,
    package_name: str,
    workspace_root: Path,
    api_toml_path: Path,
    error: str,
    source_code_package_id: object | None,
    source_object_instance_graph_commit_id: object | None,
) -> dict[str, object]:
    manifest_path = _workspace_relative_path(
        workspace_root=workspace_root,
        path=api_toml_path,
    )
    receipt: dict[str, object] = {
        "producer_provider_key": "aware_api",
        "producer_key": "aware_api.product_runtime",
        "producer_kind": "api_product_build",
        "semantic_owner": "aware_api.provider",
        "output_key": "api.product_runtime_file",
        "output_kind": "file",
        "artifact_family": "api_product_runtime",
        "artifact_role": "runtime_file",
        "artifact_key": f"{package_name}:runtime_file:missing",
        "package_name": package_name,
        "manifest_path": manifest_path,
        "status": "missing",
        "required_for": [
            "workspace_revision",
            "api_service_protocol",
            "dependency_import_resolution",
        ],
        "runtime_contract_version": "aware.api.product_runtime.v1",
        "error": error,
    }
    if source_code_package_id is not None:
        receipt["source_code_package_id"] = str(source_code_package_id)
    if source_object_instance_graph_commit_id is not None:
        receipt["source_object_instance_graph_commit_id"] = str(
            source_object_instance_graph_commit_id
        )
    return receipt


def _workspace_relative_path(*, workspace_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _int_attr(value: object, key: str) -> int:
    if value is None:
        return 0
    raw_value = getattr(value, key, None)
    if isinstance(raw_value, int):
        return raw_value
    try:
        return int(str(raw_value))
    except Exception:
        return 0


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _language_materialization_post_step_tool_mapping_by_tool_id(
    *,
    context: Mapping[str, object],
    mapping_key: str,
) -> Mapping[str, Mapping[str, str]]:
    raw_tooling = context.get(SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY)
    if not isinstance(raw_tooling, Mapping):
        return {}
    raw_tools = raw_tooling.get("tools")
    if not isinstance(raw_tools, (list, tuple)):
        return {}
    mappings: dict[str, dict[str, str]] = {}
    for raw_tool in raw_tools:
        if not isinstance(raw_tool, Mapping):
            continue
        tool_id = _optional_text(raw_tool.get("tool_id"))
        if tool_id is None:
            continue
        raw_mapping = raw_tool.get(mapping_key)
        if not isinstance(raw_mapping, Mapping):
            continue
        normalized = {
            str(key): str(value)
            for key, value in raw_mapping.items()
            if str(key).strip()
        }
        if normalized:
            mappings[tool_id] = normalized
    return mappings


def _runtime_code_package_refs(
    language_code_package_refs: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    refs: list[dict[str, object]] = []
    for language_ref in language_code_package_refs:
        source_code_package_id = language_ref.get("source_code_package_id")
        if source_code_package_id is None:
            source_code_package_id = language_ref.get("code_package_id")
        if source_code_package_id is None:
            continue
        refs.append(
            {
                "role": language_ref.get("role") or "api_language_package",
                "output_key": language_ref.get("output_key"),
                "source_code_package_id": source_code_package_id,
                "source_object_instance_graph_commit_id": (
                    language_ref.get("object_instance_graph_commit_id")
                ),
                "package_name": language_ref.get("package_name"),
                "manifest_relative_path": language_ref.get("manifest_relative_path"),
                "package_root": language_ref.get("package_root"),
                "sources_root": language_ref.get("sources_root"),
                "language": language_ref.get("language"),
            }
        )
    return tuple(refs)


def _is_uuid(value: object) -> bool:
    return isinstance(value, UUID)


def _semantic_object_config_graphs_from_context(
    context: Mapping[str, object],
) -> tuple[ObjectConfigGraph, ...]:
    raw_graphs = context.get("semantic_object_config_graphs")
    if not isinstance(raw_graphs, (list, tuple)):
        return ()
    return tuple(graph for graph in raw_graphs if isinstance(graph, ObjectConfigGraph))


def _api_delta_semantic_object_config_graphs_from_request(
    *,
    request: object,
) -> tuple[ObjectConfigGraph, ...]:
    return _semantic_object_config_graphs_from_context(
        _api_delta_operation_execution_context(request=request),
    )


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _resolution_status_counts(
    resolutions: tuple[ApiSemanticFunctionCallResolution, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for resolution in resolutions:
        status = str(getattr(resolution, "status", "")).strip()
        if not status:
            continue
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


async def _function_call_execution_detail(
    *,
    context: Mapping[str, object],
    function_call_resolutions: tuple[ApiSemanticFunctionCallResolution, ...],
) -> dict[str, object]:
    config = SemanticFunctionCallExecutionConfig.from_materialization_context(context)
    payload = config.evidence_payload()
    if not config.enabled:
        payload["status"] = "disabled"
        return payload
    backend = api_semantic_function_call_execution_backend_from_context(context)
    if backend is None:
        payload["status"] = "backend_unavailable"
        payload["reason"] = (
            "Semantic function-call execution was enabled, but no API "
            "execution backend was provided in materialization context."
        )
        return payload
    result = await execute_api_semantic_function_call_resolutions(
        resolutions=function_call_resolutions,
        backend=backend,
        continue_on_failure=config.continue_on_failure,
    )
    payload["status"] = "executed"
    payload.update(result.evidence_payload())
    return payload


__all__ = ["materialize", "materialize_delta"]
