from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib
from typing import Iterable, Protocol, TypeAlias, cast

from aware_experience.program.loader import (
    AwareProgramsTomlError,
    load_aware_programs_toml_spec,
)
from aware_experience.program.spec import (
    AwareProgramsTomlProgramSpec,
)


class ProgramRegistryEntryLike(Protocol):
    ref: str | None
    module_id: str | None
    program_name: str | None
    program_path: str | None
    invocation_plan_path: str | None


ManifestLike: TypeAlias = object


class ProgramRegistryError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProgramAssetRef:
    module_id: str
    program_name: str

    @classmethod
    def parse(cls, raw: str) -> "ProgramAssetRef":
        text = (raw or "").strip()
        if not text:
            raise ProgramRegistryError("Program ref is empty")
        if ":" not in text:
            raise ProgramRegistryError(
                "Invalid program ref "
                f"{text!r}; expected '<program_ref_namespace>:<program_name>'"
            )
        module_id, program_name = text.split(":", 1)
        module_id = module_id.strip()
        program_name = program_name.strip()
        if not module_id or not program_name:
            raise ProgramRegistryError(
                "Invalid program ref "
                f"{text!r}; expected '<program_ref_namespace>:<program_name>'"
            )
        return cls(module_id=module_id, program_name=program_name)

    @property
    def ref(self) -> str:
        return f"{self.module_id}:{self.program_name}"


@dataclass(frozen=True, slots=True)
class ProgramCompilePlanRequirements:
    required_projection_ids: tuple[str, ...]
    required_projection_node_ids: tuple[str, ...]
    required_projection_node_identity_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProgramRegistryIndex:
    entries_by_ref: dict[str, ProgramRegistryEntryLike]

    @classmethod
    def build(cls, *, manifest: ManifestLike) -> "ProgramRegistryIndex":
        entries = list(getattr(manifest, "program_registry", None) or [])
        indexed: dict[str, ProgramRegistryEntryLike] = {}
        for entry in entries:
            ref = _program_registry_ref(cast(ProgramRegistryEntryLike, entry))
            if not ref:
                continue
            if ref in indexed:
                raise ProgramRegistryError(
                    "Ambiguous program ref in manifest program_registry: "
                    f"{ref} (duplicate entries)"
                )
            indexed[ref] = cast(ProgramRegistryEntryLike, entry)
        return cls(entries_by_ref=indexed)

    def get(self, ref: ProgramAssetRef) -> ProgramRegistryEntryLike | None:
        return self.entries_by_ref.get(ref.ref)


def find_repo_root(*, start: Path | None = None) -> Path:
    """Resolve the Aware source repo root from the canonical aware.repo.toml anchor."""

    candidate = (start or Path.cwd()).expanduser().resolve()
    if not candidate.is_dir():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        manifest_path = parent / "aware.repo.toml"
        if manifest_path.is_file():
            _validate_aware_repo_toml_manifest(
                repo_root=parent,
                manifest_path=manifest_path,
            )
            return parent
    raise ProgramRegistryError(
        "Unable to resolve Aware repo root from "
        f"{(start or Path.cwd()).expanduser().resolve()}. "
        "Expected an ancestor aware.repo.toml."
    )


def _validate_aware_repo_toml_manifest(*, repo_root: Path, manifest_path: Path) -> None:
    try:
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8") or "")
    except Exception as exc:
        raise ProgramRegistryError(
            f"Invalid aware.repo.toml at {manifest_path}: {exc}"
        ) from exc
    if payload.get("aware_repo") != 1:
        raise ProgramRegistryError(f"{manifest_path} must declare aware_repo = 1.")
    repo_section = payload.get("repo")
    if not isinstance(repo_section, dict):
        raise ProgramRegistryError(f"{manifest_path} must declare a [repo] table.")
    workspaces_dir = repo_section.get("workspaces_dir")
    if not isinstance(workspaces_dir, str) or not workspaces_dir.strip():
        raise ProgramRegistryError(f"{manifest_path} must declare repo.workspaces_dir.")
    if Path(workspaces_dir).is_absolute():
        raise ProgramRegistryError(
            f"{manifest_path} repo.workspaces_dir must be relative."
        )
    workspaces_path = repo_root / workspaces_dir
    if not workspaces_path.is_dir():
        raise ProgramRegistryError(
            f"{manifest_path} declares missing workspaces_dir: {workspaces_path}"
        )


def resolve_program_asset_paths(
    *,
    repo_root: Path,
    program_refs: Iterable[str],
) -> list[Path]:
    """
    Resolve module-owned program references to `.aware` file paths.

    Contract:
    - Ref format: `<program_ref_namespace>:<program_name>`.
    - Source manifests are discovered from declared module experience packages
      first. Legacy root-module experience layout discovery is accepted only
      for modules that have not been promoted to declared packages yet.
      Legacy module program manifests are accepted only as fallback for
      isolated test workspaces that do not define experience packages.
    - Enforce one ref->source mapping (fail closed on ambiguity).
    """

    refs = [ProgramAssetRef.parse(ref) for ref in (program_refs or [])]
    if not refs:
        return []

    manifest_entries_by_ref = _index_program_manifests(repo_root=repo_root)
    results: list[Path] = []
    for ref in refs:
        match = manifest_entries_by_ref.get(ref.ref)
        if match is None:
            available = sorted(manifest_entries_by_ref.keys())
            raise ProgramRegistryError(
                "Program resolution requires aware.programs.toml with matching ref: "
                f"ref={ref.ref} (available={available})"
            )
        src = (match[0] / match[1].path).resolve()
        if repo_root not in src.parents:
            raise ProgramRegistryError(
                f"Program path escapes repo root: {src} ({match[2]})"
            )
        if not src.exists():
            raise ProgramRegistryError(f"Program path not found: {src} ({match[2]})")
        if not src.is_file():
            raise ProgramRegistryError(
                f"Program path is not a file: {src} ({match[2]})"
            )
        results.append(src)

    return results


def _index_program_manifests(
    *, repo_root: Path
) -> dict[str, tuple[Path, AwareProgramsTomlProgramSpec, Path]]:
    indexed: dict[str, tuple[Path, AwareProgramsTomlProgramSpec, Path]] = {}
    seen_roots: set[Path] = set()

    # Declared experience packages are canonical.
    for experience_toml in _iter_declared_experience_tomls(repo_root=repo_root):
        programs_root = experience_toml.parent.resolve()
        if programs_root in seen_roots:
            continue
        _validate_experience_compile_plan_contract(
            repo_root=repo_root,
            experience_toml=experience_toml.resolve(),
        )
        manifest_path = (programs_root / "aware.programs.toml").resolve()
        if not manifest_path.exists():
            continue
        _index_program_manifest_file(
            indexed=indexed,
            manifest_path=manifest_path,
            programs_root=programs_root,
        )
        seen_roots.add(programs_root)

    # Legacy root-module experience layout fallback for modules not yet declared.
    for experience_toml in sorted(
        repo_root.glob("modules/*/experience/**/aware.experience.toml")
    ):
        programs_root = experience_toml.parent.resolve()
        if programs_root in seen_roots:
            continue
        _validate_experience_compile_plan_contract(
            repo_root=repo_root,
            experience_toml=experience_toml.resolve(),
        )
        manifest_path = (programs_root / "aware.programs.toml").resolve()
        if not manifest_path.exists():
            continue
        _index_program_manifest_file(
            indexed=indexed,
            manifest_path=manifest_path,
            programs_root=programs_root,
        )
        seen_roots.add(programs_root)

    if indexed:
        return indexed

    # Legacy fallback for isolated workspaces/tests without experience manifests.
    for manifest_path in sorted(
        repo_root.glob("modules/*/programs/aware.programs.toml")
    ):
        programs_root = manifest_path.parent.resolve()
        if programs_root in seen_roots:
            continue
        _index_program_manifest_file(
            indexed=indexed,
            manifest_path=manifest_path.resolve(),
            programs_root=programs_root,
        )
        seen_roots.add(programs_root)

    return indexed


def _iter_declared_experience_tomls(*, repo_root: Path) -> list[Path]:
    experience_tomls: list[Path] = []
    seen: set[Path] = set()
    module_tomls = [
        *sorted(repo_root.glob("modules/*/aware.module.toml")),
        *sorted(repo_root.glob("workspaces/*/modules/*/aware.module.toml")),
    ]
    for module_toml in module_tomls:
        try:
            payload = tomllib.loads(module_toml.read_text(encoding="utf-8") or "")
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise ProgramRegistryError(
                f"Invalid aware.module.toml at {module_toml}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ProgramRegistryError(
                f"Invalid aware.module.toml at {module_toml}: root must be a table"
            )
        packages = payload.get("packages") or []
        if not isinstance(packages, list):
            raise ProgramRegistryError(
                f"Invalid aware.module.toml at {module_toml}: packages must be a list"
            )
        for row in packages:
            if not isinstance(row, dict):
                raise ProgramRegistryError(
                    f"Invalid aware.module.toml at {module_toml}: package row must be a table"
                )
            if str(row.get("kind") or "").strip() != "experience":
                continue
            manifest_raw = str(row.get("manifest") or "").strip()
            if not manifest_raw:
                raise ProgramRegistryError(
                    f"Invalid experience package in {module_toml}: manifest is required"
                )
            experience_toml = (module_toml.parent / manifest_raw).resolve()
            if (
                repo_root != experience_toml
                and repo_root not in experience_toml.parents
            ):
                raise ProgramRegistryError(
                    f"Experience package manifest escapes repo root: {experience_toml} ({module_toml})"
                )
            if not experience_toml.exists():
                raise ProgramRegistryError(
                    f"Declared experience package manifest not found: {experience_toml} ({module_toml})"
                )
            if not experience_toml.is_file():
                raise ProgramRegistryError(
                    f"Declared experience package manifest is not a file: {experience_toml} ({module_toml})"
                )
            if experience_toml in seen:
                continue
            experience_tomls.append(experience_toml)
            seen.add(experience_toml)
    return experience_tomls


def _index_program_manifest_file(
    *,
    indexed: dict[str, tuple[Path, AwareProgramsTomlProgramSpec, Path]],
    manifest_path: Path,
    programs_root: Path,
) -> None:
    try:
        spec = load_aware_programs_toml_spec(toml_path=manifest_path)
    except AwareProgramsTomlError as exc:
        raise ProgramRegistryError(
            f"Invalid aware.programs.toml at {manifest_path}: {exc}"
        ) from exc

    for row in spec.programs:
        if row.ref in indexed:
            first_root, _, first_manifest = indexed[row.ref]
            raise ProgramRegistryError(
                "Ambiguous program ref across manifests: "
                f"ref={row.ref} first={first_manifest} second={manifest_path} "
                f"(first_root={first_root}, second_root={programs_root})"
            )
        indexed[row.ref] = (programs_root, row, manifest_path)


def _validate_experience_compile_plan_contract(
    *,
    repo_root: Path,
    experience_toml: Path,
) -> None:
    try:
        payload = tomllib.loads(experience_toml.read_text(encoding="utf-8") or "")
    except Exception as exc:  # pragma: no cover - defensive adapter
        raise ProgramRegistryError(
            f"Invalid aware.experience.toml at {experience_toml}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ProgramRegistryError(
            f"Invalid aware.experience.toml at {experience_toml}: root must be a table"
        )
    experience_section = payload.get("experience")
    if not isinstance(experience_section, dict):
        raise ProgramRegistryError(
            f"Invalid aware.experience.toml at {experience_toml}: missing [experience]"
        )
    package_name_raw = experience_section.get("package_name")
    if not isinstance(package_name_raw, str) or not package_name_raw.strip():
        raise ProgramRegistryError(
            f"Invalid aware.experience.toml at {experience_toml}: experience.package_name must be non-empty"
        )
    package_name = package_name_raw.strip()
    compile_plan_path = (
        repo_root
        / ".aware"
        / "experience"
        / "runtime"
        / package_name
        / "experience.compile_plan.json"
    ).resolve()
    if not compile_plan_path.exists():
        return
    if not compile_plan_path.is_file():
        raise ProgramRegistryError(
            f"Invalid experience compile plan path (not a file): {compile_plan_path}"
        )
    try:
        compile_plan_payload = json.loads(
            compile_plan_path.read_text(encoding="utf-8") or "{}"
        )
    except Exception as exc:  # pragma: no cover - defensive adapter
        raise ProgramRegistryError(
            f"Invalid experience compile plan at {compile_plan_path}: {exc}"
        ) from exc
    if not isinstance(compile_plan_payload, dict):
        raise ProgramRegistryError(
            f"Invalid experience compile plan at {compile_plan_path}: root must be an object"
        )
    for key in ("program_ownership", "action_ownership", "environment_ownership"):
        if key not in compile_plan_payload:
            raise ProgramRegistryError(
                f"Invalid experience compile plan at {compile_plan_path}: missing required field {key}"
            )
        if not isinstance(compile_plan_payload[key], list):
            raise ProgramRegistryError(
                f"Invalid experience compile plan at {compile_plan_path}: field {key} must be a list"
            )
    program_ownership_raw = compile_plan_payload.get("program_ownership") or []
    for idx, row in enumerate(program_ownership_raw):
        if not isinstance(row, dict):
            raise ProgramRegistryError(
                "Invalid experience compile plan at "
                f"{compile_plan_path}: program_ownership[{idx}] must be an object"
            )
        _ = _coerce_required_pcatalog_keys(
            row=row,
            compile_plan_path=compile_plan_path,
            context=f"program_ownership[{idx}]",
        )


def resolve_program_compile_plan_requirements(
    *,
    repo_root: Path,
    ref: ProgramAssetRef,
) -> ProgramCompilePlanRequirements | None:
    runtime_root = (repo_root / ".aware" / "experience" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return None

    match: ProgramCompilePlanRequirements | None = None
    match_path: Path | None = None
    for compile_plan_path in sorted(
        runtime_root.glob("*/experience.compile_plan.json")
    ):
        if not compile_plan_path.is_file():
            continue
        try:
            payload = json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}")
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise ProgramRegistryError(
                f"Invalid experience compile plan at {compile_plan_path}: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ProgramRegistryError(
                f"Invalid experience compile plan at {compile_plan_path}: root must be an object"
            )

        rows = payload.get("program_ownership")
        if rows is None:
            continue
        if not isinstance(rows, list):
            raise ProgramRegistryError(
                f"Invalid experience compile plan at {compile_plan_path}: field program_ownership must be a list"
            )
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ProgramRegistryError(
                    "Invalid experience compile plan at "
                    f"{compile_plan_path}: program_ownership[{idx}] must be an object"
                )
            row_ref = str(row.get("ref") or "").strip()
            if row_ref != ref.ref:
                continue
            requirements = _coerce_required_pcatalog_keys(
                row=row,
                compile_plan_path=compile_plan_path,
                context=f"program_ownership[{idx}]",
            )
            if match is not None and match_path is not None:
                raise ProgramRegistryError(
                    "Ambiguous program compile-plan ownership rows: "
                    f"ref={ref.ref!r} first={match_path} second={compile_plan_path}"
                )
            match = requirements
            match_path = compile_plan_path

    return match


def _coerce_required_pcatalog_keys(
    *,
    row: dict[str, object],
    compile_plan_path: Path,
    context: str,
) -> ProgramCompilePlanRequirements:
    return ProgramCompilePlanRequirements(
        required_projection_ids=_coerce_required_key_list(
            row=row,
            key="required_projection_ids",
            compile_plan_path=compile_plan_path,
            context=context,
        ),
        required_projection_node_ids=_coerce_required_key_list(
            row=row,
            key="required_projection_node_ids",
            compile_plan_path=compile_plan_path,
            context=context,
        ),
        required_projection_node_identity_ids=_coerce_required_key_list(
            row=row,
            key="required_projection_node_identity_ids",
            compile_plan_path=compile_plan_path,
            context=context,
        ),
    )


def _coerce_required_key_list(
    *,
    row: dict[str, object],
    key: str,
    compile_plan_path: Path,
    context: str,
) -> tuple[str, ...]:
    raw = row.get(key)
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ProgramRegistryError(
            "Invalid experience compile plan at "
            f"{compile_plan_path}: {context}.{key} must be a list"
        )
    values: list[str] = []
    for idx, item in enumerate(raw):
        token = str(item or "").strip()
        if not token:
            raise ProgramRegistryError(
                "Invalid experience compile plan at "
                f"{compile_plan_path}: {context}.{key}[{idx}] must be a non-empty string"
            )
        values.append(token)
    return tuple(values)


def resolve_program_asset_path(
    *,
    repo_root: Path,
    ref: ProgramAssetRef,
) -> Path:
    """Legacy helper retained for compatibility; source scanning is no longer allowed."""

    del repo_root
    raise ProgramRegistryError(
        "Legacy runtime source scan fallback has been removed for program refs: "
        f"{ref.ref}. Rebuild environment artifacts and use manifest program_registry entries."
    )


def resolve_program_asset_path_from_manifest(
    *,
    repo_root: Path,
    manifest: ManifestLike,
    ref: ProgramAssetRef,
) -> Path | None:
    """Resolve a program ref via manifest-embedded `program_registry` when present.

    Returns:
    - `Path` when registry is present and contains the ref.
    - `None` when registry is not present (caller may use compatibility fallback).
    """

    entry = resolve_program_registry_entry_from_manifest(
        manifest=manifest,
        ref=ref,
    )
    if entry is None:
        return None
    return resolve_program_asset_path_from_registry_entry(
        repo_root=repo_root,
        entry=entry,
    )


def resolve_program_registry_entry_from_manifest(
    *,
    manifest: ManifestLike,
    ref: ProgramAssetRef,
) -> ProgramRegistryEntryLike | None:
    index = ProgramRegistryIndex.build(manifest=manifest)
    if not index.entries_by_ref:
        return None

    entry = index.get(ref)
    if entry is None:
        available = sorted(index.entries_by_ref.keys())
        raise ProgramRegistryError(
            "Program ref not found in manifest program_registry: "
            f"{ref.ref} (available={available})"
        )
    return entry


def resolve_program_asset_path_from_registry_entry(
    *,
    repo_root: Path,
    entry: ProgramRegistryEntryLike,
) -> Path:
    return _resolve_registry_relative_path(
        repo_root=repo_root,
        relative_path=entry.program_path,
        field_name="program_path",
    )


def resolve_program_invocation_plan_path_from_registry_entry(
    *,
    repo_root: Path,
    entry: ProgramRegistryEntryLike,
) -> Path:
    return _resolve_registry_relative_path(
        repo_root=repo_root,
        relative_path=entry.invocation_plan_path,
        field_name="invocation_plan_path",
    )


def _resolve_registry_relative_path(
    *,
    repo_root: Path,
    relative_path: str | None,
    field_name: str,
) -> Path:
    raw = (relative_path or "").strip()
    if not raw:
        raise ProgramRegistryError(
            f"Program registry entry missing required {field_name}"
        )
    src = (repo_root / raw).resolve()
    if repo_root != src and repo_root not in src.parents:
        raise ProgramRegistryError(
            f"Program registry path escapes repo root ({field_name}={raw!r})"
        )
    if not src.exists():
        raise ProgramRegistryError(
            f"Program registry path not found ({field_name}={raw!r})"
        )
    if not src.is_file():
        raise ProgramRegistryError(
            f"Program registry path is not a file ({field_name}={raw!r})"
        )
    return src


def _optional_entry_text(
    entry: ProgramRegistryEntryLike, field_name: str
) -> str | None:
    value = getattr(entry, field_name, None)
    if value is None:
        return None
    return str(value)


def _program_registry_ref(entry: ProgramRegistryEntryLike) -> str:
    ref = (_optional_entry_text(entry, "ref") or "").strip()
    if ref:
        return ref
    module_id = (_optional_entry_text(entry, "module_id") or "").strip()
    program_name = (_optional_entry_text(entry, "program_name") or "").strip()
    return f"{module_id}:{program_name}"


__all__ = [
    "ProgramAssetRef",
    "ProgramCompilePlanRequirements",
    "ProgramRegistryError",
    "ProgramRegistryEntryLike",
    "ProgramRegistryIndex",
    "find_repo_root",
    "resolve_program_asset_path",
    "resolve_program_asset_path_from_manifest",
    "resolve_program_asset_path_from_registry_entry",
    "resolve_program_invocation_plan_path_from_registry_entry",
    "resolve_program_asset_paths",
    "resolve_program_compile_plan_requirements",
    "resolve_program_registry_entry_from_manifest",
]
