"""Workspace-owned module-create transaction and root descriptor sync."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal, cast

from aware_code.module_manifest.scaffold import (
    ModulePackageRegistration,
    scaffold_module,
)

from aware_workspace_operator.models import (
    WorkspaceModuleCreateOptions,
    WorkspaceModuleCreateOutcome,
    WorkspaceModuleCreateReport,
    WorkspaceModulePackageRegistration,
    WorkspaceRootPyprojectStatus,
)
from aware_workspace_operator.renderers import render_workspace_pyproject

RootPyprojectAction = Literal["create", "overwrite", "skip"]


def run_workspace_module_create(
    *, options: WorkspaceModuleCreateOptions
) -> WorkspaceModuleCreateOutcome:
    """Create a module via grammar and sync workspace-root descriptors."""

    repo_root = Path(options.repo_root).resolve()
    repo_root.mkdir(parents=True, exist_ok=True)

    scaffold_result = scaffold_module(
        repo_root=repo_root,
        module_id=options.module_id,
        dependencies=options.dependencies,
        title=options.title,
        description=options.description,
        runtime_handler_modules=options.runtime_handler_modules,
        runtime_project_name=options.runtime_project_name,
        runtime_import_root=options.runtime_import_root,
        force=options.force,
        dry_run=options.dry_run,
    )

    root_pyproject, root_path, root_created_paths, root_overwritten_paths = (
        _sync_workspace_root_pyproject(
            repo_root=repo_root,
            package_registrations=scaffold_result.package_registrations,
            dry_run=options.dry_run,
        )
    )

    planned_paths = list(scaffold_result.planned_paths)
    if root_pyproject.planned_action != "skip":
        planned_paths.append(root_path)

    created_paths = list(scaffold_result.created_paths)
    created_paths.extend(root_created_paths)
    overwritten_paths = list(scaffold_result.overwritten_paths)
    overwritten_paths.extend(root_overwritten_paths)

    report = WorkspaceModuleCreateReport(
        repo_root=repo_root.as_posix(),
        module_root=scaffold_result.module_root.as_posix(),
        dry_run=options.dry_run,
        planned_paths=sorted(path.as_posix() for path in planned_paths),
        created_paths=sorted(path.as_posix() for path in created_paths),
        overwritten_paths=sorted(path.as_posix() for path in overwritten_paths),
        package_registrations=[
            _to_workspace_package_registration(registration)
            for registration in scaffold_result.package_registrations
        ],
        root_pyproject=root_pyproject,
        next_steps=(
            []
            if options.dry_run
            else [
                "aware-cli workspace materialize --workspace-toml "
                "aware.workspace.toml --package "
                f"{options.module_id}-ontology --plan"
            ]
        ),
    )
    return WorkspaceModuleCreateOutcome(report=report, exit_code=0)


def print_workspace_module_create_result(*, payload: dict[str, object]) -> None:
    """Render a human-readable module-create summary."""

    report = WorkspaceModuleCreateReport.model_validate(payload)
    repo_root = Path(report.repo_root).resolve()
    action_label = "Planned" if report.dry_run else "Scaffolded"
    print(
        f"{action_label} module: {_display_path(Path(report.module_root), repo_root=repo_root)}"
    )
    print("Files:")
    overwritten = set(report.overwritten_paths)
    created = set(report.created_paths)
    for path_str in report.planned_paths:
        path = Path(path_str)
        if path_str in overwritten:
            marker = "overwrite"
        elif path_str in created:
            marker = "create"
        else:
            marker = "skip"
        print(f"- [{marker}] {_display_path(path, repo_root=repo_root)}")
    for step in report.next_steps:
        print(f"Next: {step}")


def _sync_workspace_root_pyproject(
    *,
    repo_root: Path,
    package_registrations: tuple[ModulePackageRegistration, ...],
    dry_run: bool,
) -> tuple[WorkspaceRootPyprojectStatus, Path, list[Path], list[Path]]:
    pyproject_path = (repo_root / "pyproject.toml").resolve()
    existing_members, existing_sources = _load_workspace_pyproject_state(
        pyproject_path=pyproject_path
    )

    target_members = sorted(
        {
            *existing_members,
            *(
                registration.package_root.resolve().relative_to(repo_root).as_posix()
                for registration in package_registrations
            ),
        }
    )
    target_sources = sorted(
        {
            *existing_sources,
            *(registration.distribution_name for registration in package_registrations),
        }
    )

    registrations_already_present = all(
        registration.package_root.resolve().relative_to(repo_root).as_posix()
        in existing_members
        and registration.distribution_name in existing_sources
        for registration in package_registrations
    )

    rendered = render_workspace_pyproject(
        repo_root=repo_root,
        workspace_members=tuple(target_members),
        workspace_sources=tuple(target_sources),
    )
    current_text = (
        pyproject_path.read_text(encoding="utf-8") if pyproject_path.exists() else None
    )
    planned_action = (
        "skip"
        if pyproject_path.exists() and registrations_already_present
        else _planned_root_action(
            exists=pyproject_path.exists(),
            current_text=current_text,
            rendered_text=rendered,
        )
    )
    if planned_action != "skip" and not dry_run:
        pyproject_path.parent.mkdir(parents=True, exist_ok=True)
        _ = pyproject_path.write_text(rendered, encoding="utf-8")

    created_paths = [pyproject_path] if planned_action == "create" else []
    overwritten_paths = [pyproject_path] if planned_action == "overwrite" else []
    status = WorkspaceRootPyprojectStatus(
        path=pyproject_path.as_posix(),
        exists=pyproject_path.exists() or planned_action == "create",
        planned_action=planned_action,
        workspace_members=target_members,
        workspace_sources=target_sources,
    )
    return status, pyproject_path, created_paths, overwritten_paths


def _load_workspace_pyproject_state(
    *, pyproject_path: Path
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not pyproject_path.exists():
        return (), ()
    try:
        payload = _string_object_mapping(
            tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        )
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(
            f"Workspace root pyproject is not valid TOML: {pyproject_path}"
        ) from exc

    if payload is None:
        return (), ()

    tool = _string_object_mapping(payload.get("tool"))
    if tool is None:
        return (), ()
    uv = _string_object_mapping(tool.get("uv"))
    if uv is None:
        return (), ()

    members: tuple[str, ...] = ()
    workspace = _string_object_mapping(uv.get("workspace"))
    if workspace is not None:
        members = _string_tuple(workspace.get("members"))

    sources: tuple[str, ...] = ()
    raw_sources = _string_object_mapping(uv.get("sources"))
    if raw_sources is not None:
        sources = _workspace_source_names(raw_sources)

    return members, sources


def _planned_root_action(
    *,
    exists: bool,
    current_text: str | None,
    rendered_text: str,
) -> RootPyprojectAction:
    if not exists:
        return "create"
    if current_text == rendered_text:
        return "skip"
    return "overwrite"


def _string_object_mapping(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    mapping: dict[str, object] = {}
    for key, item in cast(dict[object, object], value).items():
        if not isinstance(key, str):
            return None
        mapping[key] = item
    return mapping


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    string_values: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            return ()
        string_values.append(item)
    return tuple(sorted(string_values))


def _workspace_source_names(raw_sources: dict[str, object]) -> tuple[str, ...]:
    source_names: list[str] = []
    for name, value in raw_sources.items():
        source = _string_object_mapping(value)
        if source is not None and source.get("workspace") is True:
            source_names.append(name)
    return tuple(sorted(source_names))


def _to_workspace_package_registration(
    registration: ModulePackageRegistration,
) -> WorkspaceModulePackageRegistration:
    return WorkspaceModulePackageRegistration(
        module_id=registration.module_id,
        surface=registration.surface,
        language=registration.language,
        manager=registration.manager,
        distribution_name=registration.distribution_name,
        import_root=registration.import_root,
        package_root=registration.package_root.as_posix(),
        pyproject_path=registration.pyproject_path.as_posix(),
    )


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.resolve().as_posix()


__all__ = [
    "print_workspace_module_create_result",
    "run_workspace_module_create",
]
