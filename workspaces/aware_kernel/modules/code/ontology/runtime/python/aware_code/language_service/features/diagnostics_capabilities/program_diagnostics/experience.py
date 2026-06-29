from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

from aware_code_ontology.code.code_section_enums import CodeSectionType

from aware_workspace.compiler.workspace import WorkspaceSnapshot

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.projection.compiler import load_projection_experience_ownership_from_sources

from .contracts import ProgramCompilePlanRequirements, ProgramExperienceLookup


def resolve_experience_root_for_path(*, path: Path) -> Path | None:
    resolved = path.resolve()
    for parent in [resolved.parent, *resolved.parents]:
        if (parent / "aware.experience.toml").is_file():
            return parent
    return None


def build_experience_lookup(
    *,
    snapshot: WorkspaceSnapshot,
    uri_to_path: Callable[[str], Path],
    uri: str,
) -> ProgramExperienceLookup:
    projection_fallback_symbols: set[str] = set()
    for other_code in snapshot.codes_by_uri.values():
        for other_section in other_code.code_sections:
            if other_section.type != CodeSectionType.projection:
                continue
            projection = other_section.code_section_projection
            if projection is None:
                continue
            symbol_name = (projection.name or "").strip()
            projection_name = (projection.projection_name or "").strip()
            if symbol_name:
                projection_fallback_symbols.add(symbol_name)
            if projection_name:
                projection_fallback_symbols.add(projection_name)

    uri_path = uri_to_path(uri)
    experience_root = resolve_experience_root_for_path(path=uri_path)
    experience_names: set[str] = set()
    compile_plan_requirements_by_program_name: dict[str, ProgramCompilePlanRequirements] = {}
    if experience_root is not None:
        experience_toml = experience_root / "aware.experience.toml"
        try:
            experience_workspace = ExperienceWorkspace.from_toml(toml_path=experience_toml)
            experience_snapshot = experience_workspace.build_snapshot()
            ownerships = load_projection_experience_ownership_from_sources(
                package_root=experience_snapshot.package_root,
                source_files=experience_snapshot.source_files,
            )
            for ownership in ownerships:
                experience_name = (ownership.name or "").strip()
                if not experience_name:
                    continue
                experience_names.add(experience_name)
            compile_plan_requirements_by_program_name = _load_compile_plan_requirements_for_source(
                repo_root=experience_snapshot.repo_root,
                package_name=(experience_snapshot.spec.experience.package_name or "").strip(),
                package_root=experience_snapshot.package_root,
                source_path=uri_path,
            )
        except Exception:
            experience_names = set()
            compile_plan_requirements_by_program_name = {}

    return ProgramExperienceLookup(
        experience_candidates=tuple(sorted(experience_names)),
        experience_names=frozenset(experience_names),
        projection_fallback_symbols=frozenset(projection_fallback_symbols),
        compile_plan_requirements_by_program_name=compile_plan_requirements_by_program_name,
    )


def _load_compile_plan_requirements_for_source(
    *,
    repo_root: Path,
    package_name: str,
    package_root: Path,
    source_path: Path,
) -> dict[str, ProgramCompilePlanRequirements]:
    if not package_name:
        return {}
    try:
        source_rel = source_path.resolve().relative_to(package_root.resolve()).as_posix()
    except Exception:
        return {}
    compile_plan_path = (
        repo_root / ".aware" / "experience" / "runtime" / package_name / "experience.compile_plan.json"
    ).resolve()
    if not compile_plan_path.exists() or not compile_plan_path.is_file():
        return {}
    try:
        payload = json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("program_ownership")
    if not isinstance(rows, list):
        return {}

    out: dict[str, ProgramCompilePlanRequirements] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_path = str(row.get("path") or "").strip()
        row_name = str(row.get("name") or "").strip()
        if not row_path or not row_name or row_path != source_rel:
            continue
        out[row_name] = ProgramCompilePlanRequirements(
            required_projection_ids=_coerce_required_key_list(
                row=row,
                key="required_projection_ids",
            ),
            required_projection_node_ids=_coerce_required_key_list(
                row=row,
                key="required_projection_node_ids",
            ),
            required_projection_node_identity_ids=_coerce_required_key_list(
                row=row,
                key="required_projection_node_identity_ids",
            ),
        )
    return out


def _coerce_required_key_list(*, row: dict[str, object], key: str) -> tuple[str, ...]:
    raw = row.get(key)
    if raw is None:
        return ()
    if not isinstance(raw, list):
        return ()
    values: list[str] = []
    for item in raw:
        token = str(item or "").strip()
        if not token:
            continue
        values.append(token)
    return tuple(values)
