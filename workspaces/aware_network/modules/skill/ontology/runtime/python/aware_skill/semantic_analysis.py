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
from aware_skill.manifest import AwareSkillDependencyKind

from aware_skill.compile import compile_skill_workspace
from aware_skill.compiler import load_skill_ownership_from_sources
from aware_skill.models import SkillConfigPlan, SkillOwnership
from aware_skill.semantic_contract import SKILL_CONFIG_OWNER
from aware_skill.workspace import SkillWorkspace


_SKILL_REQUIRED_MATERIALIZATIONS = (
    "skill_compile_plan",
    "skill_ontology_plan",
    "skill_package",
)


@dataclass(frozen=True, slots=True)
class SkillSemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class SkillSemanticChangePreview:
    changed_source_files: tuple[str, ...]
    affected_skill_names: tuple[str, ...]
    affected_api_refs: tuple[str, ...]
    affected_endpoint_names: tuple[str, ...]
    semantic_deltas: tuple[SemanticCapabilityDelta, ...]
    semantic_events: tuple[SemanticCapabilityEvent, ...]
    skill_count: int
    api_count: int
    endpoint_count: int
    step_count: int
    required_materializations: tuple[str, ...]
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = ()


@dataclass(frozen=True, slots=True)
class SkillSemanticAnalysisResult:
    schema_version: int
    package_root: str
    source_files: tuple[str, ...]
    skill_configs: tuple[SkillConfigPlan, ...]
    skill_ownership: tuple[SkillOwnership, ...]
    diagnostics: tuple[SkillSemanticDiagnostic, ...]
    change_preview: SkillSemanticChangePreview
    code_package_delta: CodePackageDelta | None = None


def analyze_skill_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta | None = None,
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = (),
    fail_on_error: bool = True,
) -> SkillSemanticAnalysisResult:
    source_file_names = _source_file_names(source_files=source_files)
    try:
        skill_ownership = load_skill_ownership_from_sources(
            package_root=package_root,
            source_files=source_files,
        )
        skill_configs = tuple(
            _build_minimal_skill_config_plan(skill=skill)
            for skill in skill_ownership
        )
        diagnostics: tuple[SkillSemanticDiagnostic, ...] = ()
    except ValueError as exc:
        if fail_on_error:
            raise
        skill_ownership = ()
        skill_configs = ()
        diagnostics = (
            SkillSemanticDiagnostic(
                severity="error",
                code="aware_skill.semantic_analysis.invalid_source",
                message=str(exc),
            ),
        )

    return SkillSemanticAnalysisResult(
        schema_version=1,
        package_root=package_root.resolve().as_posix(),
        source_files=source_file_names,
        skill_configs=skill_configs,
        skill_ownership=skill_ownership,
        diagnostics=diagnostics,
        change_preview=_build_change_preview(
            skill_configs=skill_configs,
            source_files=source_file_names,
            code_package_delta=code_package_delta,
            required_semantic_dependencies=required_semantic_dependencies,
        ),
        code_package_delta=code_package_delta,
    )


def analyze_skill_code_package_delta(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = (),
    fail_on_error: bool = False,
) -> SkillSemanticAnalysisResult:
    return analyze_skill_sources(
        package_root=package_root,
        source_files=source_files,
        code_package_delta=code_package_delta,
        required_semantic_dependencies=required_semantic_dependencies,
        fail_on_error=fail_on_error,
    )


def analyze_skill_semantic_capability(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    workspace_analysis = _load_workspace_analysis_for_capability_request(
        request=request,
    )
    required_semantic_dependencies = (
        _load_required_semantic_dependencies_for_capability_request(request=request)
    )
    if workspace_analysis is None:
        analysis = analyze_skill_sources(
            package_root=request.package_root,
            source_files=request.source_files,
            code_package_delta=request.code_package_delta,
            required_semantic_dependencies=required_semantic_dependencies,
            fail_on_error=False,
        )
    else:
        package_root, source_files, skill_configs, skill_ownership = workspace_analysis
        source_file_names = _source_file_names(source_files=source_files)
        analysis = SkillSemanticAnalysisResult(
            schema_version=1,
            package_root=package_root.resolve().as_posix(),
            source_files=source_file_names,
            skill_configs=skill_configs,
            skill_ownership=skill_ownership,
            diagnostics=(),
            change_preview=_build_change_preview(
                skill_configs=skill_configs,
                source_files=source_file_names,
                code_package_delta=request.code_package_delta,
                required_semantic_dependencies=required_semantic_dependencies,
            ),
            code_package_delta=request.code_package_delta,
        )

    preview = analysis.change_preview
    return SemanticAnalysisCapabilityResult(
        provider_key="aware_skill",
        semantic_owner=SKILL_CONFIG_OWNER,
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
            affected_semantic_keys=preview.affected_skill_names,
            required_materializations=preview.required_materializations,
            required_semantic_dependencies=preview.required_semantic_dependencies,
            semantic_deltas=preview.semantic_deltas,
            semantic_events=preview.semantic_events,
            metadata={
                "affected_api_refs": preview.affected_api_refs,
                "affected_endpoint_names": preview.affected_endpoint_names,
                "skill_count": preview.skill_count,
                "api_count": preview.api_count,
                "endpoint_count": preview.endpoint_count,
                "step_count": preview.step_count,
            },
        ),
        payload=analysis,
        code_package_delta=request.code_package_delta,
    )


def _load_workspace_analysis_for_capability_request(
    *,
    request: SemanticAnalysisCapabilityRequest,
) -> tuple[Path, tuple[Path, ...], tuple[SkillConfigPlan, ...], tuple[SkillOwnership, ...]] | None:
    if request.manifest_path is None:
        return None
    manifest_path = request.manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        return None

    compile_result = compile_skill_workspace(
        toml_path=manifest_path,
        repo_root=request.workspace_root,
        emit_compile_plan=False,
    )
    snapshot = compile_result.snapshot
    compile_plan = compile_result.compile_plan
    if compile_plan is None:
        return (snapshot.package_root, snapshot.source_files, (), ())
    return (
        snapshot.package_root,
        snapshot.source_files,
        compile_plan.skill_configs,
        compile_plan.skill_ownership,
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
    try:
        snapshot = SkillWorkspace.from_toml(
            toml_path=manifest_path,
            repo_root=request.workspace_root,
        ).build_snapshot()
    except Exception:
        return ()
    source_ref = _manifest_source_ref(
        manifest_path=manifest_path,
        workspace_root=request.workspace_root,
    )
    requirements: list[SemanticCapabilityDependencyRequirement] = []
    for dependency in snapshot.spec.dependencies:
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        if dependency.kind not in (
            AwareSkillDependencyKind.api,
            AwareSkillDependencyKind.api_package,
        ):
            continue
        requirements.append(
            SemanticCapabilityDependencyRequirement(
                dependency_key=f"aware_skill.api_package:{package_name}",
                provider_key="aware_api",
                package_name=package_name,
                required_state="materialized",
                dependency_kind=dependency.kind.value,
                semantic_owner="aware_api.provider",
                manifest_kind="aware_api_toml",
                reason=(
                    "Skill package materialization requires API semantic "
                    "package truth before SkillConfig API endpoints can "
                    "resolve ApiCapabilityEndpoint refs."
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
    skill_configs: tuple[SkillConfigPlan, ...],
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ],
) -> SkillSemanticChangePreview:
    changed_source_files = _changed_source_files(
        source_files=source_files,
        code_package_delta=code_package_delta,
    )
    affected_skills = _affected_skill_configs(
        skill_configs=skill_configs,
        changed_source_files=changed_source_files,
    )
    semantic_deltas = _semantic_deltas_for_skill_configs(
        skill_configs=affected_skills,
    )
    semantic_events = _semantic_events_for_deltas(semantic_deltas=semantic_deltas)
    return SkillSemanticChangePreview(
        changed_source_files=changed_source_files,
        affected_skill_names=tuple(sorted(skill.name for skill in affected_skills)),
        affected_api_refs=tuple(
            sorted(
                {
                    api.api_ref
                    for skill in affected_skills
                    for api in skill.apis
                }
            )
        ),
        affected_endpoint_names=tuple(
            sorted(
                {
                    endpoint.name
                    for skill in affected_skills
                    for endpoint in skill.api_endpoints
                }
            )
        ),
        semantic_deltas=semantic_deltas,
        semantic_events=semantic_events,
        skill_count=len(skill_configs),
        api_count=sum(len(skill.apis) for skill in skill_configs),
        endpoint_count=sum(len(skill.api_endpoints) for skill in skill_configs),
        step_count=sum(len(skill.steps) for skill in skill_configs),
        required_materializations=(
            _SKILL_REQUIRED_MATERIALIZATIONS if skill_configs else ()
        ),
        required_semantic_dependencies=(
            _dedupe_dependency_requirements(required_semantic_dependencies)
            if skill_configs
            else ()
        ),
    )


def _semantic_deltas_for_skill_configs(
    *,
    skill_configs: tuple[SkillConfigPlan, ...],
) -> tuple[SemanticCapabilityDelta, ...]:
    deltas: list[SemanticCapabilityDelta] = []
    for skill in sorted(skill_configs, key=lambda item: item.name):
        skill_key = f"skill:{skill.name}"
        deltas.append(
            SemanticCapabilityDelta(
                delta_key=f"aware_skill.skill_config.upsert:{skill_key}",
                semantic_key=skill_key,
                verb="upsert",
                subject_type="aware_skill.SkillConfig",
                source="aware_skill.semantic_analysis",
                source_refs=(skill.source_path,),
                after_payload={
                    "name": skill.name,
                    "description": skill.description,
                    "api_count": len(skill.apis),
                    "endpoint_count": len(skill.api_endpoints),
                    "step_count": len(skill.steps),
                },
            )
        )
        for api in sorted(skill.apis, key=lambda item: item.api_ref):
            api_key = f"{skill_key}/api:{api.api_ref}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=f"aware_skill.skill_config_api.upsert:{api_key}",
                    semantic_key=api_key,
                    verb="upsert",
                    subject_type="aware_skill.SkillConfigApi",
                    source="aware_skill.semantic_analysis",
                    source_refs=(api.source_path,),
                    after_payload={
                        "skill_semantic_key": skill_key,
                        "skill_name": skill.name,
                        "api_ref": api.api_ref,
                    },
                )
            )
        for endpoint in sorted(
            skill.api_endpoints,
            key=lambda item: item.name,
        ):
            endpoint_key = f"{skill_key}/endpoint:{endpoint.name}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=(
                        "aware_skill.skill_config_api_endpoint.upsert:"
                        f"{endpoint_key}"
                    ),
                    semantic_key=endpoint_key,
                    verb="upsert",
                    subject_type="aware_skill.SkillConfigApiEndpoint",
                    source="aware_skill.semantic_analysis",
                    source_refs=(endpoint.source_path,),
                    after_payload={
                        "skill_semantic_key": skill_key,
                        "skill_name": skill.name,
                        "name": endpoint.name,
                        "endpoint_ref": endpoint.endpoint_ref,
                        "api_ref": endpoint.api_ref,
                        "capability_name": endpoint.capability_name,
                        "description": endpoint.description,
                    },
                )
            )
        for step in sorted(skill.steps, key=lambda item: item.position):
            step_key = f"{skill_key}/step:{step.position}"
            deltas.append(
                SemanticCapabilityDelta(
                    delta_key=f"aware_skill.skill_config_step.upsert:{step_key}",
                    semantic_key=step_key,
                    verb="upsert",
                    subject_type="aware_skill.SkillConfigStep",
                    source="aware_skill.semantic_analysis",
                    source_refs=(step.source_path,),
                    after_payload={
                        "skill_semantic_key": skill_key,
                        "skill_name": skill.name,
                        "position": step.position,
                        "endpoint_name": step.endpoint_name,
                        "endpoint_ref": step.endpoint_ref,
                        "api_ref": step.api_ref,
                        "instruction": step.instruction,
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
        "aware_skill.SkillConfig": "aware_skill.skill_config",
        "aware_skill.SkillConfigApi": "aware_skill.skill_config_api",
        "aware_skill.SkillConfigApiEndpoint": (
            "aware_skill.skill_config_api_endpoint"
        ),
        "aware_skill.SkillConfigStep": "aware_skill.skill_config_step",
    }.get(subject_type, subject_type)


def _changed_source_files(
    *,
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if code_package_delta is None:
        return source_files
    changed_paths = frozenset(
        _normalize_path_text(path.relative_path)
        for path in code_package_delta.paths
        if _normalize_path_text(path.relative_path)
    )
    if not changed_paths:
        return source_files
    manifest_relative_path = (
        _normalize_path_text(code_package_delta.manifest_relative_path)
        if code_package_delta.manifest_relative_path
        else ""
    )
    if manifest_relative_path and manifest_relative_path in changed_paths:
        return source_files
    matched = tuple(
        source_file
        for source_file in source_files
        if source_file in changed_paths
        or any(
            source_file.endswith(f"/{changed_path}")
            or changed_path.endswith(f"/{source_file}")
            for changed_path in changed_paths
        )
    )
    return matched or source_files


def _affected_skill_configs(
    *,
    skill_configs: tuple[SkillConfigPlan, ...],
    changed_source_files: tuple[str, ...],
) -> tuple[SkillConfigPlan, ...]:
    changed = frozenset(changed_source_files)
    return tuple(
        skill
        for skill in skill_configs
        if skill.source_path in changed
        or any(skill.source_path.endswith(f"/{path}") for path in changed)
    )


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


def _source_file_names(*, source_files: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in source_files)


def _normalize_path_text(value: str) -> str:
    return Path(value).as_posix().strip().strip("/")


def _build_minimal_skill_config_plan(*, skill: SkillOwnership) -> SkillConfigPlan:
    from aware_skill.builder import _build_skill_config_plan

    return _build_skill_config_plan(skill=skill)


__all__ = [
    "SkillSemanticAnalysisResult",
    "SkillSemanticChangePreview",
    "SkillSemanticDiagnostic",
    "analyze_skill_code_package_delta",
    "analyze_skill_semantic_capability",
    "analyze_skill_sources",
]
