from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
)
from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
    SemanticCapabilityActionBinding,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDelta,
    SemanticCapabilityDiagnostic,
    SemanticCapabilityEvent,
    SemanticCapabilityFunctionCallBinding,
)

from ..semantic_contract import API_API_OWNER
from .compiler import (
    load_api_ownership_from_source_texts,
    load_api_ownership_from_sources,
)
from ..models import APIOwnership, BindingMapTruth, ProjectionOwnedClassTruth
from ..semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CREATE_CAPABILITY_FUNCTION_REF,
    API_CREATE_FUNCTION_REF,
)

if TYPE_CHECKING:
    from ..workspace import APIWorkspaceSnapshot

_API_REQUIRED_MATERIALIZATIONS = (
    "api_compile_plan",
    "api_ontology_plan",
)


@dataclass(frozen=True, slots=True)
class APISemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class APISemanticChangePreview:
    changed_source_files: tuple[str, ...]
    affected_api_names: tuple[str, ...]
    affected_capability_names: tuple[str, ...]
    semantic_deltas: tuple[SemanticCapabilityDelta, ...]
    semantic_events: tuple[SemanticCapabilityEvent, ...]
    action_bindings: tuple[SemanticCapabilityActionBinding, ...]
    api_count: int
    capability_count: int
    endpoint_count: int
    graph_count: int
    required_materializations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class APISemanticAnalysisResult:
    schema_version: int
    package_root: str
    source_files: tuple[str, ...]
    api_ownership: tuple[APIOwnership, ...]
    diagnostics: tuple[APISemanticDiagnostic, ...]
    change_preview: APISemanticChangePreview
    code_package_delta: CodePackageDelta | None = None


def analyze_api_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_truth_by_name: (
        dict[str, dict[str, ProjectionOwnedClassTruth]] | None
    ) = None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None = None,
    code_package_delta: CodePackageDelta | None = None,
    fail_on_error: bool = True,
) -> APISemanticAnalysisResult:
    source_file_names = _source_file_names(source_files=source_files)
    try:
        api_ownership = load_api_ownership_from_sources(
            package_root=package_root,
            source_files=source_files,
            projection_truth_by_name=projection_truth_by_name,
            binding_truth_by_ref=binding_truth_by_ref,
        )
        diagnostics: tuple[APISemanticDiagnostic, ...] = ()
    except ValueError as exc:
        if fail_on_error:
            raise
        api_ownership = ()
        diagnostics = (
            APISemanticDiagnostic(
                severity="error",
                code="aware_api.semantic_analysis.invalid_source",
                message=str(exc),
            ),
        )

    return APISemanticAnalysisResult(
        schema_version=1,
        package_root=package_root.resolve().as_posix(),
        source_files=source_file_names,
        api_ownership=api_ownership,
        diagnostics=diagnostics,
        change_preview=_build_change_preview(
            api_ownership=api_ownership,
            source_files=source_file_names,
            code_package_delta=code_package_delta,
        ),
        code_package_delta=code_package_delta,
    )


def analyze_api_code_package_delta(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
    projection_truth_by_name: (
        dict[str, dict[str, ProjectionOwnedClassTruth]] | None
    ) = None,
    binding_truth_by_ref: dict[tuple[str, str], BindingMapTruth] | None = None,
    fail_on_error: bool = False,
) -> APISemanticAnalysisResult:
    try:
        source_texts = _delta_source_texts(
            source_files=source_files,
            code_package_delta=code_package_delta,
        )
        source_file_names = _source_file_names(source_files=tuple(source_texts))
        api_ownership = load_api_ownership_from_source_texts(
            package_root=package_root,
            source_texts=source_texts,
            projection_truth_by_name=projection_truth_by_name,
            binding_truth_by_ref=binding_truth_by_ref,
        )
        diagnostics: tuple[APISemanticDiagnostic, ...] = ()
    except ValueError as exc:
        if fail_on_error:
            raise
        source_file_names = ()
        api_ownership = ()
        diagnostics = (
            APISemanticDiagnostic(
                severity="error",
                code="aware_api.semantic_analysis.invalid_delta_source",
                message=str(exc),
            ),
        )

    return APISemanticAnalysisResult(
        schema_version=1,
        package_root=package_root.resolve().as_posix(),
        source_files=source_file_names,
        api_ownership=api_ownership,
        diagnostics=diagnostics,
        change_preview=_build_change_preview(
            api_ownership=api_ownership,
            source_files=source_file_names,
            code_package_delta=code_package_delta,
        ),
        code_package_delta=code_package_delta,
    )


def analyze_api_semantic_capability(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    snapshot = _load_workspace_snapshot_for_capability_request(request=request)
    source_files = (
        snapshot.source_files if snapshot is not None else request.source_files
    )
    binding_truth_by_ref = _load_dependency_binding_truths_for_capability_request(
        request=request,
        snapshot=snapshot,
    )
    if request.code_package_delta is None:
        analysis = analyze_api_sources(
            package_root=request.package_root,
            source_files=source_files,
            binding_truth_by_ref=binding_truth_by_ref,
            fail_on_error=False,
        )
    else:
        analysis = analyze_api_code_package_delta(
            package_root=request.package_root,
            source_files=source_files,
            binding_truth_by_ref=binding_truth_by_ref,
            code_package_delta=request.code_package_delta,
            fail_on_error=False,
        )
    preview = analysis.change_preview
    return SemanticAnalysisCapabilityResult(
        provider_key="aware_api",
        semantic_owner=API_API_OWNER,
        package_root=analysis.package_root,
        source_files=analysis.source_files,
        diagnostics=tuple(
            SemanticCapabilityDiagnostic(
                severity=diagnostic.severity,
                code=diagnostic.code,
                message=diagnostic.message,
                source_path=diagnostic.source_path,
            )
            for diagnostic in analysis.diagnostics
        ),
        change_preview=SemanticCapabilityChangePreview(
            changed_source_files=preview.changed_source_files,
            affected_semantic_keys=preview.affected_api_names,
            required_materializations=preview.required_materializations,
            semantic_deltas=preview.semantic_deltas,
            semantic_events=preview.semantic_events,
            action_bindings=preview.action_bindings,
            metadata={
                "affected_capability_names": preview.affected_capability_names,
                "api_count": preview.api_count,
                "capability_count": preview.capability_count,
                "endpoint_count": preview.endpoint_count,
                "graph_count": preview.graph_count,
            },
        ),
        payload=analysis,
        code_package_delta=request.code_package_delta,
    )


def _load_dependency_binding_truths_for_capability_request(
    *,
    request: SemanticAnalysisCapabilityRequest,
    snapshot: "APIWorkspaceSnapshot | None",
) -> dict[tuple[str, str], BindingMapTruth] | None:
    from ..dependencies.runtime_resolution import load_api_dependency_binding_truths

    if snapshot is None:
        return None
    if not snapshot.spec.dependencies:
        return {}
    return load_api_dependency_binding_truths(snapshot=snapshot)


def _load_workspace_snapshot_for_capability_request(
    *,
    request: SemanticAnalysisCapabilityRequest,
) -> "APIWorkspaceSnapshot | None":
    if request.manifest_path is None:
        return None
    manifest_path = request.manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        return None

    from ..workspace import APIWorkspace

    repo_root = (
        request.workspace_root.expanduser().resolve()
        if request.workspace_root
        else None
    )
    return APIWorkspace.from_toml(
        toml_path=manifest_path,
        repo_root=repo_root,
    ).build_snapshot()


def _build_change_preview(
    *,
    api_ownership: tuple[APIOwnership, ...],
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> APISemanticChangePreview:
    changed_source_files = _changed_source_files(
        source_files=source_files,
        code_package_delta=code_package_delta,
    )
    affected_apis = _affected_api_ownership(
        api_ownership=api_ownership,
        changed_source_files=changed_source_files,
    )
    affected_capability_names = tuple(
        sorted(
            {
                capability.name
                for api in affected_apis
                for capability in api.capabilities
            }
        )
    )
    semantic_deltas = _semantic_deltas_for_apis(api_ownership=affected_apis)
    semantic_events = _semantic_events_for_deltas(semantic_deltas=semantic_deltas)
    return APISemanticChangePreview(
        changed_source_files=changed_source_files,
        affected_api_names=tuple(sorted(api.name for api in affected_apis)),
        affected_capability_names=affected_capability_names,
        semantic_deltas=semantic_deltas,
        semantic_events=semantic_events,
        action_bindings=_api_action_bindings_for_events(semantic_events),
        api_count=len(api_ownership),
        capability_count=sum(len(api.capabilities) for api in api_ownership),
        endpoint_count=sum(
            len(capability.endpoints)
            for api in api_ownership
            for capability in api.capabilities
        ),
        graph_count=sum(len(api.graphs) for api in api_ownership),
        required_materializations=(
            _API_REQUIRED_MATERIALIZATIONS if api_ownership else ()
        ),
    )


def _semantic_deltas_for_apis(
    *,
    api_ownership: tuple[APIOwnership, ...],
) -> tuple[SemanticCapabilityDelta, ...]:
    deltas: list[SemanticCapabilityDelta] = []
    for api in sorted(api_ownership, key=lambda item: item.name):
        api_key = f"api:{api.name}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=f"aware_api.api.upsert:{api_key}",
                semantic_key=api_key,
                verb="upsert",
                subject_type="aware_api.Api",
                source="aware_api.semantic_analysis",
                source_refs=(api.source_path,),
                after_payload={
                    "name": api.name,
                    "capability_count": len(api.capabilities),
                    "graph_count": len(api.graphs),
                },
            )
        )
        for capability in sorted(api.capabilities, key=lambda item: item.name):
            capability_key = f"{api_key}/capability:{capability.name}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=f"aware_api.api_capability.upsert:{capability_key}",
                    semantic_key=capability_key,
                    verb="upsert",
                    subject_type="aware_api.ApiCapability",
                    source="aware_api.semantic_analysis",
                    source_refs=(capability.source_path,),
                    after_payload={
                        "api_semantic_key": api_key,
                        "api_name": api.name,
                        "name": capability.name,
                        "description": capability.description,
                        "endpoint_count": len(capability.endpoints),
                    },
                )
            )
            for endpoint in sorted(
                capability.endpoints,
                key=lambda item: item.name,
            ):
                endpoint_key = f"{capability_key}/endpoint:{endpoint.name}"
                deltas.append(
                    SemanticCapabilityDelta(
                        delta_key=(
                            "aware_api.api_capability_endpoint.upsert:"
                            f"{endpoint_key}"
                        ),
                        semantic_key=endpoint_key,
                        verb="upsert",
                        subject_type="aware_api.ApiCapabilityEndpoint",
                        source="aware_api.semantic_analysis",
                        source_refs=(endpoint.source_path,),
                        after_payload={
                            "capability_semantic_key": capability_key,
                            "api_name": api.name,
                            "capability_name": capability.name,
                            "name": endpoint.name,
                            "description": endpoint.description,
                            "request_class_ref": (endpoint.request_config.class_ref),
                        },
                    )
                )
    return tuple(deltas)


def _semantic_events_for_deltas(
    *,
    semantic_deltas: tuple[SemanticCapabilityDelta, ...],
) -> tuple[SemanticCapabilityEvent, ...]:
    return tuple(
        SemanticCapabilityEvent(
            event_key=_event_key_for_delta(delta),
            semantic_key=delta.semantic_key,
            verb=delta.verb,
            subject_type=delta.subject_type,
            source=delta.source,
            source_refs=delta.source_refs,
            delta_keys=(delta.delta_key,),
            payload=dict(delta.after_payload or {}),
        )
        for delta in semantic_deltas
    )


def _event_key_for_delta(delta: SemanticCapabilityDelta) -> str:
    subject_event_prefix_by_type = {
        "aware_api.Api": "aware_api.api",
        "aware_api.ApiCapability": "aware_api.api_capability",
        "aware_api.ApiCapabilityEndpoint": "aware_api.api_capability_endpoint",
    }
    prefix = subject_event_prefix_by_type.get(delta.subject_type, delta.subject_type)
    return f"{prefix}.{delta.verb}ed"


def _api_action_bindings_for_events(
    semantic_events: tuple[SemanticCapabilityEvent, ...],
) -> tuple[SemanticCapabilityActionBinding, ...]:
    event_keys = frozenset(event.event_key for event in semantic_events)
    bindings = (
        SemanticCapabilityActionBinding(
            action_key="aware_api.api.upserted.apply_ontology",
            event_key="aware_api.api.upserted",
            action_type="function_call",
            description="Apply an API semantic upsert through Api.create.",
            function_call_binding=SemanticCapabilityFunctionCallBinding(
                binding_key="aware_api.api.upserted.api_create",
                event_key="aware_api.api.upserted",
                function_ref=API_CREATE_FUNCTION_REF,
                argument_bindings={
                    "name": "payload.name",
                    "description": "payload.description",
                },
                result_semantic_key_template="semantic_key",
            ),
        ),
        SemanticCapabilityActionBinding(
            action_key="aware_api.api_capability.upserted.apply_ontology",
            event_key="aware_api.api_capability.upserted",
            action_type="function_call",
            description=(
                "Apply an API capability semantic upsert through "
                "Api.create_capability."
            ),
            function_call_binding=SemanticCapabilityFunctionCallBinding(
                binding_key="aware_api.api_capability.upserted.api_create_capability",
                event_key="aware_api.api_capability.upserted",
                function_ref=API_CREATE_CAPABILITY_FUNCTION_REF,
                receiver_semantic_key_template="payload.api_semantic_key",
                argument_bindings={
                    "name": "payload.name",
                    "description": "payload.description",
                },
                result_semantic_key_template="semantic_key",
            ),
        ),
        SemanticCapabilityActionBinding(
            action_key="aware_api.api_capability_endpoint.upserted.apply_ontology",
            event_key="aware_api.api_capability_endpoint.upserted",
            action_type="function_call",
            description=(
                "Apply an API endpoint semantic upsert through "
                "ApiCapability.create_endpoint."
            ),
            function_call_binding=SemanticCapabilityFunctionCallBinding(
                binding_key=(
                    "aware_api.api_capability_endpoint.upserted."
                    "api_capability_create_endpoint"
                ),
                event_key="aware_api.api_capability_endpoint.upserted",
                function_ref=API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
                receiver_semantic_key_template="payload.capability_semantic_key",
                argument_bindings={
                    "name": "payload.name",
                    "description": "payload.description",
                },
                argument_ref_bindings={
                    "request_class_config_id": "payload.request_class_ref",
                },
                result_semantic_key_template="semantic_key",
                metadata={"argument_ref_resolution": "class_config_id"},
            ),
        ),
    )
    return tuple(binding for binding in bindings if binding.event_key in event_keys)


def _affected_api_ownership(
    *,
    api_ownership: tuple[APIOwnership, ...],
    changed_source_files: tuple[str, ...],
) -> tuple[APIOwnership, ...]:
    if not changed_source_files:
        return api_ownership
    changed = frozenset(changed_source_files)
    return tuple(api for api in api_ownership if api.source_path in changed)


def _changed_source_files(
    *,
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if code_package_delta is None:
        return ()
    changed_paths = frozenset(
        _normalize_path_text(path.relative_path)
        for path in code_package_delta.paths
        if _normalize_path_text(path.relative_path)
    )
    if not changed_paths:
        return ()
    manifest_relative_path = (
        _normalize_path_text(code_package_delta.manifest_relative_path)
        if code_package_delta.manifest_relative_path
        else ""
    )
    if manifest_relative_path and manifest_relative_path in changed_paths:
        return source_files
    return tuple(
        source_file
        for source_file in source_files
        if source_file in changed_paths
        or any(
            source_file.endswith(f"/{changed_path}") for changed_path in changed_paths
        )
    )


def _delta_source_texts(
    *,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
) -> dict[Path, str]:
    source_file_names = _source_file_names(source_files=source_files)
    manifest_relative_path = (
        _normalize_path_text(code_package_delta.manifest_relative_path)
        if code_package_delta.manifest_relative_path
        else ""
    )
    source_texts: dict[Path, str] = {}
    undeclared_sources: list[str] = []
    missing_content: list[str] = []
    delete_sources: list[str] = []
    for delta_path in code_package_delta.paths:
        relative_path = _normalize_path_text(delta_path.relative_path)
        if not relative_path or relative_path == manifest_relative_path:
            continue
        if not _is_authored_aware_source_delta_path(
            delta_path=delta_path,
            relative_path=relative_path,
        ):
            continue
        matched_source_file = _matched_source_file(
            relative_path=relative_path,
            source_file_names=source_file_names,
        )
        if matched_source_file is None and source_file_names:
            undeclared_sources.append(relative_path)
            continue
        if _enum_value(delta_path.kind) == CodePackageDeltaKind.delete.value:
            delete_sources.append(relative_path)
            continue
        content_text = _delta_path_content_text(delta_path)
        if content_text is None:
            missing_content.append(relative_path)
            continue
        source_texts[Path(matched_source_file or relative_path)] = content_text

    if undeclared_sources:
        raise ValueError(
            "API CodePackageDelta source paths must be declared in the "
            "current manifest source set: " + ", ".join(sorted(undeclared_sources))
        )
    if delete_sources:
        raise ValueError(
            "API CodePackageDelta deletes require full rebuild until baseline "
            "remove planning is implemented: " + ", ".join(sorted(delete_sources))
        )
    if missing_content:
        raise ValueError(
            "API CodePackageDelta source upserts require content_text or "
            "content_plan.content_text: " + ", ".join(sorted(missing_content))
        )
    if not source_texts:
        raise ValueError(
            "API CodePackageDelta requires at least one content-backed authored "
            "Aware source upsert"
        )
    return dict(sorted(source_texts.items(), key=lambda item: item[0].as_posix()))


def _matched_source_file(
    *,
    relative_path: str,
    source_file_names: tuple[str, ...],
) -> str | None:
    for source_file in source_file_names:
        if source_file == relative_path or source_file.endswith(f"/{relative_path}"):
            return source_file
    return None


def _is_authored_aware_source_delta_path(
    *,
    delta_path: object,
    relative_path: str,
) -> bool:
    path_role = _enum_value(getattr(delta_path, "path_role", None))
    if path_role and path_role != "authored_source":
        return False
    language = _enum_value(getattr(delta_path, "language", None))
    if language and language != "aware":
        return False
    return relative_path.endswith(".aware") or language == "aware"


def _delta_path_content_text(delta_path: object) -> str | None:
    content_text = getattr(delta_path, "content_text", None)
    if content_text is not None:
        return str(content_text)
    content_plan = getattr(delta_path, "content_plan", None)
    content_plan_text = getattr(content_plan, "content_text", None)
    if content_plan_text is not None:
        return str(content_plan_text)
    return None


def _source_file_names(*, source_files: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in source_files)


def _normalize_path_text(value: str) -> str:
    return Path(value).as_posix().strip().strip("/")


def _enum_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value or "").strip()


__all__ = [
    "APISemanticAnalysisResult",
    "APISemanticChangePreview",
    "APISemanticDiagnostic",
    "analyze_api_code_package_delta",
    "analyze_api_semantic_capability",
    "analyze_api_sources",
]
