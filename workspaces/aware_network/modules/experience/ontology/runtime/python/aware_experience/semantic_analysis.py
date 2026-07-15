from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
    SemanticCapabilityChangePreview,
    SemanticCapabilityDependencyRequirement,
    SemanticCapabilityDiagnostic,
)
from aware_code_ontology.code.code_plan import CodePackageDelta

from .projection.compiler import load_projection_experience_ownership_from_sources
from .semantic_contract import EXPERIENCE_PROVIDER_OWNER

_EXPERIENCE_REQUIRED_MATERIALIZATIONS = (
    "experience_compile_plan",
    "experience_package_ontology_plan",
    "projection_experience_ontology_plan",
)


@dataclass(frozen=True, slots=True)
class ExperienceSemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceSemanticChangePreview:
    changed_source_files: tuple[str, ...]
    affected_experience_names: tuple[str, ...]
    required_materializations: tuple[str, ...]
    required_semantic_dependencies: tuple[
        SemanticCapabilityDependencyRequirement,
        ...,
    ] = ()


@dataclass(frozen=True, slots=True)
class ExperienceSemanticAnalysisResult:
    schema_version: int
    package_root: str
    source_files: tuple[str, ...]
    diagnostics: tuple[ExperienceSemanticDiagnostic, ...]
    change_preview: ExperienceSemanticChangePreview
    code_package_delta: CodePackageDelta | None = None


def analyze_experience_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta | None = None,
    fail_on_error: bool = True,
) -> ExperienceSemanticAnalysisResult:
    source_file_names = _source_file_names(source_files=source_files)
    try:
        ownership = load_projection_experience_ownership_from_sources(
            package_root=package_root,
            source_files=source_files,
        )
        projection_roots = _load_projection_root_refs_from_sources(
            package_root=package_root,
            source_files=source_files,
        )
        diagnostics: tuple[ExperienceSemanticDiagnostic, ...] = ()
    except ValueError as exc:
        if fail_on_error:
            raise
        ownership = ()
        projection_roots = ()
        diagnostics = (
            ExperienceSemanticDiagnostic(
                severity="error",
                code="aware_experience.semantic_analysis.invalid_source",
                message=str(exc),
            ),
        )

    affected_names = tuple(sorted(item.name for item in ownership))
    return ExperienceSemanticAnalysisResult(
        schema_version=1,
        package_root=package_root.resolve().as_posix(),
        source_files=source_file_names,
        diagnostics=diagnostics,
        change_preview=ExperienceSemanticChangePreview(
            changed_source_files=_changed_source_files(
                source_files=source_file_names,
                code_package_delta=code_package_delta,
            ),
            affected_experience_names=affected_names,
            required_materializations=(
                _EXPERIENCE_REQUIRED_MATERIALIZATIONS if affected_names else ()
            ),
            required_semantic_dependencies=(
                _ocg_dependency_requirements(projection_roots=projection_roots)
                if affected_names
                else ()
            ),
        ),
        code_package_delta=code_package_delta,
    )


def analyze_experience_code_package_delta(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    code_package_delta: CodePackageDelta,
    fail_on_error: bool = False,
) -> ExperienceSemanticAnalysisResult:
    return analyze_experience_sources(
        package_root=package_root,
        source_files=source_files,
        code_package_delta=code_package_delta,
        fail_on_error=fail_on_error,
    )


def analyze_experience_semantic_capability(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    analysis = analyze_experience_sources(
        package_root=request.package_root,
        source_files=request.source_files,
        code_package_delta=request.code_package_delta,
        fail_on_error=False,
    )
    preview = analysis.change_preview
    return SemanticAnalysisCapabilityResult(
        provider_key="aware_experience",
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
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
            affected_semantic_keys=preview.affected_experience_names,
            required_materializations=preview.required_materializations,
            required_semantic_dependencies=preview.required_semantic_dependencies,
            metadata={
                "affected_experience_names": preview.affected_experience_names,
            },
        ),
        payload=analysis,
        code_package_delta=request.code_package_delta,
    )


@dataclass(frozen=True, slots=True)
class _ProjectionRootRef:
    experience_name: str
    raw_projection_ref: str
    projection_key: str
    ocg_fqn_prefix: str
    source_path: str


def _load_projection_root_refs_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[_ProjectionRootRef, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    refs: list[_ProjectionRootRef] = []
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="experience source")
        source_text = source_path.read_text(encoding="utf-8")
        tree = parser.parse(source_text.encode("utf-8"))
        source_ref = relpath.as_posix()
        for node in tree.root_node.named_children:
            if node.type != "experience_def":
                continue
            experience_name = _symbol_key(_field_text(node, "name"))
            raw_projection_ref = _field_text(node, "projection")
            if not experience_name or not raw_projection_ref:
                continue
            ocg_fqn_prefix = _ocg_fqn_prefix_from_projection_ref(raw_projection_ref)
            projection_key = _projection_key_from_projection_ref(raw_projection_ref)
            if not ocg_fqn_prefix or not projection_key:
                continue
            refs.append(
                _ProjectionRootRef(
                    experience_name=experience_name,
                    raw_projection_ref=raw_projection_ref,
                    projection_key=projection_key,
                    ocg_fqn_prefix=ocg_fqn_prefix,
                    source_path=source_ref,
                )
            )
    return tuple(refs)


def _ocg_dependency_requirements(
    *,
    projection_roots: tuple[_ProjectionRootRef, ...],
) -> tuple[SemanticCapabilityDependencyRequirement, ...]:
    requirements: list[SemanticCapabilityDependencyRequirement] = []
    seen: set[str] = set()
    for root in projection_roots:
        key = root.ocg_fqn_prefix.casefold()
        if key in seen:
            continue
        seen.add(key)
        requirements.append(
            SemanticCapabilityDependencyRequirement(
                dependency_key=f"aware_experience.object_config_graph:{root.ocg_fqn_prefix}",
                provider_key="aware_meta",
                package_name=root.ocg_fqn_prefix,
                required_state="materialized",
                dependency_kind="object_config_graph",
                semantic_owner="aware_meta.provider",
                manifest_kind="aware_toml",
                package_selector={
                    "semantic_package_metadata": {
                        "fqn_prefix": root.ocg_fqn_prefix,
                    },
                },
                reason=(
                    "Experience ProjectionExperience materialization requires "
                    "the target ObjectConfigGraph package before projection refs "
                    "can resolve."
                ),
                source_refs=(root.source_path,),
                metadata={
                    "projection_key": root.projection_key,
                    "projection_ref": root.raw_projection_ref,
                    "experience_name": root.experience_name,
                },
            )
        )
    return tuple(requirements)


def _source_file_names(*, source_files: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in source_files)


def _changed_source_files(
    *,
    source_files: tuple[str, ...],
    code_package_delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if code_package_delta is None:
        return source_files
    delta_paths = tuple(
        path.relative_path
        for path in code_package_delta.paths
        if path.relative_path in source_files
    )
    return delta_paths or source_files


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _ocg_fqn_prefix_from_projection_ref(raw_projection_ref: str) -> str:
    parts = tuple(part for part in raw_projection_ref.strip().split(".") if part)
    if len(parts) <= 1:
        return parts[0] if parts else ""
    return parts[0]


def _projection_key_from_projection_ref(raw_projection_ref: str) -> str:
    parts = tuple(part for part in raw_projection_ref.strip().split(".") if part)
    if not parts:
        return ""
    return parts[-1].casefold()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    try:
        candidate.resolve().relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"{label} escapes package root: {candidate}") from exc
