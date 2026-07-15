from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDependencyRequirement,
    SemanticCapabilityDelta,
    SemanticCapabilityDiagnostic,
    SemanticCapabilityEvent,
)
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.manifest.spec import AwareServiceDependencyKind

from .compiler import load_service_ownership_from_sources
from .models import ServiceOwnership
from .semantic_contract import SERVICE_ROOT_OWNER

_SERVICE_REQUIRED_MATERIALIZATIONS = (
    "service_compile_plan",
    "service_ontology_plan",
)


@dataclass(frozen=True, slots=True)
class ServiceSemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceSemanticChangePreview:
    changed_source_files: tuple[str, ...]
    affected_service_names: tuple[str, ...]
    affected_operation_names: tuple[str, ...]
    semantic_deltas: tuple[SemanticCapabilityDelta, ...]
    semantic_events: tuple[SemanticCapabilityEvent, ...]
    service_count: int
    operation_count: int
    endpoint_count: int
    required_materializations: tuple[str, ...]
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = ()


@dataclass(frozen=True, slots=True)
class ServiceSemanticAnalysisResult:
    schema_version: int
    package_root: str
    source_files: tuple[str, ...]
    service_ownership: tuple[ServiceOwnership, ...]
    diagnostics: tuple[ServiceSemanticDiagnostic, ...]
    change_preview: ServiceSemanticChangePreview
    code_package_delta: CodePackageDelta | None = None


def analyze_service_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta | None = None,
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = (),
    fail_on_error: bool = True,
) -> ServiceSemanticAnalysisResult:
    source_file_names = _source_file_names(source_files=source_files)
    try:
        service_ownership = load_service_ownership_from_sources(
            package_root=package_root,
            source_files=source_files,
        )
        diagnostics: tuple[ServiceSemanticDiagnostic, ...] = ()
    except ValueError as exc:
        if fail_on_error:
            raise
        service_ownership = ()
        diagnostics = (
            ServiceSemanticDiagnostic(
                severity="error",
                code="aware_service.semantic_analysis.invalid_source",
                message=str(exc),
            ),
        )

    return ServiceSemanticAnalysisResult(
        schema_version=1,
        package_root=package_root.resolve().as_posix(),
        source_files=source_file_names,
        service_ownership=service_ownership,
        diagnostics=diagnostics,
        change_preview=_build_change_preview(
            service_ownership=service_ownership,
            source_files=source_file_names,
            code_package_delta=code_package_delta,
            required_semantic_dependencies=required_semantic_dependencies,
        ),
        code_package_delta=code_package_delta,
    )


def analyze_service_code_package_delta(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = (),
    fail_on_error: bool = False,
) -> ServiceSemanticAnalysisResult:
    return analyze_service_sources(
        package_root=package_root,
        source_files=source_files,
        code_package_delta=code_package_delta,
        required_semantic_dependencies=required_semantic_dependencies,
        fail_on_error=fail_on_error,
    )


def analyze_service_semantic_capability(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    required_semantic_dependencies = (
        _load_required_semantic_dependencies_for_capability_request(request=request)
    )
    analysis = analyze_service_sources(
        package_root=request.package_root,
        source_files=request.source_files,
        code_package_delta=request.code_package_delta,
        required_semantic_dependencies=required_semantic_dependencies,
        fail_on_error=False,
    )
    preview = analysis.change_preview
    return SemanticAnalysisCapabilityResult(
        provider_key="aware_service",
        semantic_owner=SERVICE_ROOT_OWNER,
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
            affected_semantic_keys=preview.affected_service_names,
            required_materializations=preview.required_materializations,
            required_semantic_dependencies=preview.required_semantic_dependencies,
            semantic_deltas=preview.semantic_deltas,
            semantic_events=preview.semantic_events,
            metadata={
                "affected_operation_names": preview.affected_operation_names,
                "service_count": preview.service_count,
                "operation_count": preview.operation_count,
                "endpoint_count": preview.endpoint_count,
            },
        ),
        payload=analysis,
        code_package_delta=request.code_package_delta,
    )


def _load_required_semantic_dependencies_for_capability_request(
    *,
    request: SemanticAnalysisCapabilityRequest,
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    if request.manifest_path is None:
        return ()
    manifest_path = request.manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        return ()
    spec = load_aware_service_toml_spec(toml_path=manifest_path)
    source_ref = _manifest_source_ref(
        manifest_path=manifest_path,
        workspace_root=request.workspace_root,
    )
    requirements: list[SemanticCapabilityDependencyRequirement] = []
    for dependency in spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        if dependency.kind is not AwareServiceDependencyKind.api_service_protocol:
            continue
        requirements.append(
            SemanticCapabilityDependencyRequirement(
                dependency_key=f"aware_service.api_service_protocol:{package_name}",
                provider_key="aware_api",
                package_name=package_name,
                required_state="materialized",
                dependency_kind=dependency.kind.value,
                semantic_owner="aware_api.provider",
                manifest_kind="aware_api_toml",
                reason=(
                    "Service package materialization requires the API service "
                    "protocol package semantic lane before ServiceConfig can "
                    "resolve endpoint refs."
                ),
                source_refs=(source_ref,),
                metadata={
                    "version_number": dependency.version_number,
                    "expected_hash_sha256": dependency.expected_hash_sha256,
                },
            )
        )
    return tuple(requirements)


def _manifest_source_ref(
    *,
    manifest_path: Path,
    workspace_root: Path | None,
) -> str:
    if workspace_root is None:
        return manifest_path.as_posix()
    try:
        return manifest_path.relative_to(
            workspace_root.expanduser().resolve()
        ).as_posix()
    except ValueError:
        return manifest_path.as_posix()


def _build_change_preview(
    *,
    service_ownership: tuple[ServiceOwnership, ...],
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ],
) -> ServiceSemanticChangePreview:
    changed_source_files = _changed_source_files(
        source_files=source_files,
        code_package_delta=code_package_delta,
    )
    affected_services = _affected_service_ownership(
        service_ownership=service_ownership,
        changed_source_files=changed_source_files,
    )
    affected_operation_names = tuple(
        sorted(
            {
                operation.name
                for service in affected_services
                for operation in service.operations
            }
        )
    )
    semantic_dependencies = _dedupe_dependency_requirements(
        (
            *required_semantic_dependencies,
            *_experience_dependency_requirements(
                affected_services=affected_services,
            ),
        )
    )
    semantic_deltas = _semantic_deltas_for_services(service_ownership=affected_services)
    semantic_events = _semantic_events_for_deltas(semantic_deltas=semantic_deltas)
    return ServiceSemanticChangePreview(
        changed_source_files=changed_source_files,
        affected_service_names=tuple(
            sorted(service.name for service in affected_services)
        ),
        affected_operation_names=affected_operation_names,
        semantic_deltas=semantic_deltas,
        semantic_events=semantic_events,
        service_count=len(service_ownership),
        operation_count=sum(len(service.operations) for service in service_ownership),
        endpoint_count=sum(
            len(operation.api_endpoints)
            for service in service_ownership
            for operation in service.operations
        ),
        required_materializations=(
            _SERVICE_REQUIRED_MATERIALIZATIONS if service_ownership else ()
        ),
        required_semantic_dependencies=(
            semantic_dependencies if service_ownership else ()
        ),
    )


def _experience_dependency_requirements(
    *,
    affected_services: tuple[ServiceOwnership, ...],
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    requirements: list[SemanticCapabilityDependencyRequirement] = []
    seen_refs: set[str] = set()
    for service in affected_services:
        for experience in service.experiences:
            experience_ref = experience.experience_ref.strip()
            if not experience_ref:
                continue
            experience_key = experience_ref.casefold()
            if experience_key in seen_refs:
                continue
            seen_refs.add(experience_key)
            requirements.append(
                SemanticCapabilityDependencyRequirement(
                    dependency_key=(
                        f"aware_service.projection_experience:{experience_ref}"
                    ),
                    provider_key="aware_experience",
                    package_name=experience_ref,
                    required_state="materialized",
                    dependency_kind="ProjectionExperience",
                    semantic_owner="aware_experience.provider",
                    manifest_kind="aware_experience_toml",
                    package_selector={
                        "semantic_package_metadata": {
                            "fqn_prefix": experience_ref,
                        },
                    },
                    reason=(
                        "Service package materialization requires the "
                        "ProjectionExperience semantic lane before ServiceConfig "
                        "can resolve experience refs."
                    ),
                    source_refs=(experience.source_path,),
                    metadata={"experience_ref": experience_ref},
                )
            )
    return tuple(requirements)


def _dedupe_dependency_requirements(
    dependencies: tuple[SemanticCapabilityDependencyRequirement, ...],
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    deduped: list[SemanticCapabilityDependencyRequirement] = []
    seen_keys: set[str] = set()
    for dependency in dependencies:
        key = dependency.dependency_key.strip()
        if not key:
            key = (
                f"{dependency.provider_key}:"
                f"{dependency.dependency_kind}:"
                f"{dependency.package_name}"
            )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(dependency)
    return tuple(deduped)


def _semantic_deltas_for_services(
    *,
    service_ownership: tuple[ServiceOwnership, ...],
) -> tuple[SemanticCapabilityDelta, ...]:
    deltas: list[SemanticCapabilityDelta] = []
    for service in sorted(service_ownership, key=lambda item: item.name):
        service_key = f"service:{service.name}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=f"aware_service.service_config.upsert:{service_key}",
                semantic_key=service_key,
                verb="upsert",
                subject_type="aware_service.ServiceConfig",
                source="aware_service.semantic_analysis",
                source_refs=(service.source_path,),
                after_payload={
                    "name": service.name,
                    "api_count": len(service.apis),
                    "experience_count": len(service.experiences),
                    "operation_count": len(service.operations),
                },
            )
        )
        for api in sorted(service.apis, key=lambda item: item.api_ref):
            api_key = f"{service_key}/api:{api.api_ref}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=f"aware_service.service_config_api.upsert:{api_key}",
                    semantic_key=api_key,
                    verb="upsert",
                    subject_type="aware_service.ServiceConfigApi",
                    source="aware_service.semantic_analysis",
                    source_refs=(api.source_path,),
                    after_payload={
                        "service_semantic_key": service_key,
                        "service_name": service.name,
                        "api_ref": api.api_ref,
                        "projection_count": len(api.api_projections),
                    },
                )
            )
        for experience in sorted(
            service.experiences,
            key=lambda item: item.experience_ref,
        ):
            experience_key = f"{service_key}/experience:{experience.experience_ref}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=(
                        "aware_service.service_config_experience.upsert:"
                        f"{experience_key}"
                    ),
                    semantic_key=experience_key,
                    verb="upsert",
                    subject_type="aware_service.ServiceConfigExperience",
                    source="aware_service.semantic_analysis",
                    source_refs=(experience.source_path,),
                    after_payload={
                        "service_semantic_key": service_key,
                        "service_name": service.name,
                        "experience_ref": experience.experience_ref,
                    },
                )
            )
        for operation in sorted(service.operations, key=lambda item: item.name):
            operation_key = f"{service_key}/operation:{operation.name}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=(
                        "aware_service.service_operation_config.upsert:"
                        f"{operation_key}"
                    ),
                    semantic_key=operation_key,
                    verb="upsert",
                    subject_type="aware_service.ServiceOperationConfig",
                    source="aware_service.semantic_analysis",
                    source_refs=(operation.source_path,),
                    after_payload={
                        "service_semantic_key": service_key,
                        "service_name": service.name,
                        "name": operation.name,
                        "admission_mode": operation.admission_mode,
                        "settlement_policy": operation.settlement_policy,
                        "endpoint_count": len(operation.api_endpoints),
                    },
                )
            )
            for endpoint in sorted(
                operation.api_endpoints,
                key=lambda item: item.endpoint_ref,
            ):
                endpoint_key = f"{operation_key}/endpoint:{endpoint.endpoint_ref}"
                deltas.append(
                    SemanticCapabilityDelta(
                        delta_key=(
                            "aware_service.service_operation_config_api_endpoint."
                            f"upsert:{endpoint_key}"
                        ),
                        semantic_key=endpoint_key,
                        verb="upsert",
                        subject_type=(
                            "aware_service.ServiceOperationConfigApiEndpoint"
                        ),
                        source="aware_service.semantic_analysis",
                        source_refs=(endpoint.source_path,),
                        after_payload={
                            "operation_semantic_key": operation_key,
                            "service_name": service.name,
                            "operation_name": operation.name,
                            "endpoint_ref": endpoint.endpoint_ref,
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
            event_key=f"{_event_prefix(delta.subject_type)}.{delta.verb}ed",
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


def _event_prefix(subject_type: str) -> str:
    return {
        "aware_service.ServiceConfig": "aware_service.service_config",
        "aware_service.ServiceConfigApi": "aware_service.service_config_api",
        "aware_service.ServiceConfigExperience": (
            "aware_service.service_config_experience"
        ),
        "aware_service.ServiceOperationConfig": (
            "aware_service.service_operation_config"
        ),
        "aware_service.ServiceOperationConfigApiEndpoint": (
            "aware_service.service_operation_config_api_endpoint"
        ),
    }.get(subject_type, subject_type)


def _changed_source_files(
    *,
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if code_package_delta is None:
        return source_files
    changed = tuple(
        path.relative_path
        for path in code_package_delta.paths
        if path.relative_path in source_files
    )
    return tuple(sorted(changed)) or source_files


def _affected_service_ownership(
    *,
    service_ownership: tuple[ServiceOwnership, ...],
    changed_source_files: tuple[str, ...],
) -> tuple[ServiceOwnership, ...]:
    changed = frozenset(changed_source_files)
    return tuple(
        service for service in service_ownership if service.source_path in changed
    )


def _source_file_names(*, source_files: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in source_files)


__all__ = [
    "ServiceSemanticAnalysisResult",
    "ServiceSemanticChangePreview",
    "ServiceSemanticDiagnostic",
    "analyze_service_code_package_delta",
    "analyze_service_semantic_capability",
    "analyze_service_sources",
]
