"""Canonical module scaffold generation for Code-owned module rails."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


_MODULE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_PACKAGE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@dataclass(frozen=True, slots=True)
class ModuleScaffoldSpec:
    module_id: str
    module_snake: str
    module_hyphen: str
    class_prefix: str
    title: str
    description: str
    ontology_package_name: str
    runtime_project_name: str
    runtime_import_root: str
    fqn_prefix: str
    environment_slug: str
    dependencies: tuple[str, ...]
    runtime_handler_modules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModulePackageRegistration:
    module_id: str
    surface: str
    language: str
    manager: str
    distribution_name: str
    import_root: str
    package_root: Path
    pyproject_path: Path


@dataclass(frozen=True, slots=True)
class ModuleScaffoldResult:
    module_root: Path
    planned_paths: tuple[Path, ...]
    created_paths: tuple[Path, ...]
    overwritten_paths: tuple[Path, ...]
    package_registrations: tuple[ModulePackageRegistration, ...]
    dry_run: bool


def scaffold_module(
    *,
    repo_root: Path,
    module_id: str,
    dependencies: tuple[str, ...] = (),
    title: str | None = None,
    description: str | None = None,
    runtime_handler_modules: tuple[str, ...] = (),
    runtime_project_name: str | None = None,
    runtime_import_root: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> ModuleScaffoldResult:
    """Create a canonical module scaffold under `modules/<module_id>/`."""

    root = Path(repo_root).expanduser().resolve()
    spec = build_module_scaffold_spec(
        module_id=module_id,
        dependencies=dependencies,
        title=title,
        description=description,
        runtime_handler_modules=runtime_handler_modules,
        runtime_project_name=runtime_project_name,
        runtime_import_root=runtime_import_root,
    )
    files = build_module_scaffold_files(repo_root=root, spec=spec)
    package_registrations = build_module_package_registrations(
        repo_root=root, spec=spec
    )
    return _write_scaffold_files(
        files=files,
        package_registrations=package_registrations,
        force=force,
        dry_run=dry_run,
    )


def build_module_scaffold_spec(
    *,
    module_id: str,
    dependencies: tuple[str, ...] = (),
    title: str | None = None,
    description: str | None = None,
    runtime_handler_modules: tuple[str, ...] = (),
    runtime_project_name: str | None = None,
    runtime_import_root: str | None = None,
) -> ModuleScaffoldSpec:
    module = _normalize_module_id(module_id)
    module_hyphen = module.replace("_", "-")
    module_snake = module.replace("-", "_")
    class_prefix = _to_class_prefix(module)

    ontology_package_name = f"{module_hyphen}-ontology"
    default_runtime_project_name = f"aware-{module_hyphen}"
    default_runtime_import_root = f"aware_{module_snake}"
    runtime_project_name_value = (
        runtime_project_name.strip()
        if isinstance(runtime_project_name, str) and runtime_project_name.strip()
        else default_runtime_project_name
    )
    runtime_import_root_value = (
        runtime_import_root.strip()
        if isinstance(runtime_import_root, str) and runtime_import_root.strip()
        else default_runtime_import_root
    )
    if not _PACKAGE_NAME_RE.fullmatch(runtime_project_name_value):
        raise ValueError(
            "runtime_project_name must match ^[a-z0-9][a-z0-9_-]*$ (lowercase letters, digits, '_' or '-', "
            + "starting with a letter or digit)."
        )
    if not re.fullmatch(r"^[a-z_][a-z0-9_]*$", runtime_import_root_value):
        raise ValueError(
            "runtime_import_root must match ^[a-z_][a-z0-9_]*$ (lowercase letters, digits, '_' and starting "
            + "with a letter or underscore)."
        )
    fqn_prefix = f"aware_{module_snake}"
    environment_slug = f"aware_{module_snake}"

    normalized_deps = _normalize_dependencies(
        dependencies=dependencies,
        disallow=ontology_package_name,
    )
    normalized_handlers = _normalize_handler_modules(runtime_handler_modules)

    title_value = (
        title.strip()
        if isinstance(title, str) and title.strip()
        else _default_title(module)
    )
    description_value = (
        description.strip()
        if isinstance(description, str) and description.strip()
        else f"SSOT canonical (.aware) sources for {module_hyphen}."
    )

    return ModuleScaffoldSpec(
        module_id=module,
        module_snake=module_snake,
        module_hyphen=module_hyphen,
        class_prefix=class_prefix,
        title=title_value,
        description=description_value,
        ontology_package_name=ontology_package_name,
        runtime_project_name=runtime_project_name_value,
        runtime_import_root=runtime_import_root_value,
        fqn_prefix=fqn_prefix,
        environment_slug=environment_slug,
        dependencies=normalized_deps,
        runtime_handler_modules=normalized_handlers,
    )


def build_module_scaffold_files(
    *,
    repo_root: Path,
    spec: ModuleScaffoldSpec,
) -> dict[Path, str]:
    module_root = (Path(repo_root).resolve() / "modules" / spec.module_id).resolve()
    service_import_root = f"aware_{spec.module_snake}_environment_service"
    files = {
        module_root / "aware.module.toml": _render_aware_module_toml(spec=spec),
        module_root
        / "docs"
        / "specs"
        / "README.md": _render_module_specs_readme(spec=spec),
        module_root
        / "structure"
        / "aware.workflows.toml": _render_workflows_toml(spec=spec),
        module_root
        / "structure"
        / "ontology"
        / "aware.toml": _render_ontology_aware_toml(spec=spec),
        module_root
        / "structure"
        / "ontology"
        / "aware"
        / spec.module_snake
        / f"{spec.module_snake}_root.aware": _render_seed_aware_source(spec=spec),
        module_root
        / "runtime"
        / "pyproject.toml": _render_runtime_pyproject(spec=spec),
        module_root / "runtime" / "README.md": _render_runtime_readme(spec=spec),
        module_root / "runtime" / spec.runtime_import_root / "__init__.py": "",
        module_root
        / "runtime"
        / spec.runtime_import_root
        / "handlers"
        / "__init__.py": "",
        module_root
        / "runtime"
        / spec.runtime_import_root
        / "handlers"
        / "impl"
        / "__init__.py": "",
        module_root
        / "services"
        / "environment"
        / "pyproject.toml": _render_environment_service_pyproject(spec=spec),
        module_root
        / "services"
        / "environment"
        / "README.md": _render_environment_service_readme(spec=spec),
        module_root
        / "services"
        / "environment"
        / service_import_root
        / "__init__.py": "",
        module_root
        / "services"
        / "environment"
        / service_import_root
        / "providers.py": _render_environment_service_providers(spec=spec),
    }
    return files


def build_module_package_registrations(
    *,
    repo_root: Path,
    spec: ModuleScaffoldSpec,
) -> tuple[ModulePackageRegistration, ...]:
    module_root = (Path(repo_root).resolve() / "modules" / spec.module_id).resolve()
    service_import_root = f"aware_{spec.module_snake}_environment_service"
    service_project_name = f"aware-{spec.module_hyphen}-environment-service"
    runtime_root = (module_root / "runtime").resolve()
    service_root = (module_root / "services" / "environment").resolve()
    return (
        ModulePackageRegistration(
            module_id=spec.module_id,
            surface="runtime",
            language="python",
            manager="uv",
            distribution_name=spec.runtime_project_name,
            import_root=spec.runtime_import_root,
            package_root=runtime_root,
            pyproject_path=(runtime_root / "pyproject.toml").resolve(),
        ),
        ModulePackageRegistration(
            module_id=spec.module_id,
            surface="environment_service",
            language="python",
            manager="uv",
            distribution_name=service_project_name,
            import_root=service_import_root,
            package_root=service_root,
            pyproject_path=(service_root / "pyproject.toml").resolve(),
        ),
    )


def _write_scaffold_files(
    *,
    files: dict[Path, str],
    package_registrations: tuple[ModulePackageRegistration, ...],
    force: bool,
    dry_run: bool,
) -> ModuleScaffoldResult:
    if not files:
        raise ValueError("No scaffold files were produced.")

    ordered_paths = tuple(
        sorted((p.resolve() for p in files.keys()), key=lambda p: p.as_posix())
    )
    common_root = Path(
        os.path.commonpath([path.as_posix() for path in ordered_paths])
    ).resolve()
    if common_root.name == "modules":
        raise ValueError("Unable to resolve module root from scaffold paths.")
    if common_root.parent.name != "modules":
        raise ValueError("Scaffold paths must live under modules/<module_id>/...")
    module_root = common_root

    existing = [path for path in ordered_paths if path.exists()]
    if existing and not force:
        rel = ", ".join(path.as_posix() for path in existing)
        raise FileExistsError(f"Module scaffold would overwrite existing files: {rel}")

    created_paths: list[Path] = []
    overwritten_paths: list[Path] = []
    for path in ordered_paths:
        if path.exists():
            overwritten_paths.append(path)
        else:
            created_paths.append(path)
        if dry_run:
            continue
        if path.exists() and path.is_dir():
            raise IsADirectoryError(f"Expected file path but found directory: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        text = files[path]
        _ = path.write_text(
            text if text.endswith("\n") or not text else f"{text}\n", encoding="utf-8"
        )

    return ModuleScaffoldResult(
        module_root=module_root,
        planned_paths=ordered_paths,
        created_paths=tuple(created_paths),
        overwritten_paths=tuple(overwritten_paths),
        package_registrations=package_registrations,
        dry_run=dry_run,
    )


def _normalize_module_id(value: str) -> str:
    module_id = str(value).strip()
    if not _MODULE_ID_RE.fullmatch(module_id):
        raise ValueError(
            "module_id must match ^[a-z][a-z0-9_-]*$ (lowercase letters, digits, '_' or '-', starting with a letter)."
        )
    return module_id


def _normalize_dependencies(
    *, dependencies: tuple[str, ...], disallow: str
) -> tuple[str, ...]:
    out: set[str] = set()
    for dep in dependencies:
        name = str(dep).strip()
        if not name:
            continue
        if not _PACKAGE_NAME_RE.fullmatch(name):
            raise ValueError(
                f"dependency package_name must match ^[a-z0-9][a-z0-9_-]*$: {name!r}"
            )
        if name == disallow:
            raise ValueError(
                f"dependency {name!r} cannot reference the module's own ontology package"
            )
        out.add(name)
    return tuple(sorted(out))


def _normalize_handler_modules(values: tuple[str, ...]) -> tuple[str, ...]:
    modules: list[str] = []
    for item in values:
        value = str(item).strip()
        if not value:
            continue
        modules.append(value)
    return tuple(modules)


def _default_title(module_id: str) -> str:
    words = [part for part in re.split(r"[-_]+", module_id) if part]
    if not words:
        return module_id
    return " ".join(word.capitalize() for word in words)


def _to_class_prefix(module_id: str) -> str:
    words = [part for part in re.split(r"[-_]+", module_id) if part]
    if not words:
        return "Module"
    return "".join(word.capitalize() for word in words)


def _render_aware_module_toml(*, spec: ModuleScaffoldSpec) -> str:
    service_import_root = f"aware_{spec.module_snake}_environment_service"
    lines = [
        "aware = 1",
        "",
        "[[services]]",
        'surface = "environment"',
        "provider_modules = [",
        f'  "{service_import_root}.providers",',
        "]",
        "",
        "[[packages]]",
        'aware_toml_path = "structure/ontology/aware.toml"',
        "",
        "[runtime]",
    ]
    if spec.runtime_project_name != f"aware-{spec.module_hyphen}":
        lines.append(f'project_name = "{spec.runtime_project_name}"')
    if spec.runtime_import_root != f"aware_{spec.module_snake}":
        lines.append(f'import_root = "{spec.runtime_import_root}"')
    if spec.runtime_handler_modules:
        lines.append("handler_modules = [")
        for module in spec.runtime_handler_modules:
            lines.append(f'  "{module}",')
        lines.append("]")
    return "\n".join(lines)


def _render_module_specs_readme(*, spec: ModuleScaffoldSpec) -> str:
    module_rel = f"modules/{spec.module_id}"
    return "\n".join(
        [
            f"# {spec.title} — Specs",
            "",
            "Spec packages for this module follow the canonical protocol (repo root):",
            "",
            "- `docs/specs/PROTOCOL.md`",
            "",
            "## Where Specs Live",
            "",
            f"- `{module_rel}/docs/specs/<spec_slug>/`",
            "",
            "## Start Rule",
            "",
            (
                "- If this module begins as a cross-cutting extraction, create its spec package "
                "before moving ontology/code truth."
            ),
            (
                "- Use `docs/specs/PROTOCOL.md` to lock what becomes canonical in this module vs "
                "what remains with the source owner."
            ),
            "",
            "## Templates",
            "",
            "Copy and adapt these templates when creating a new spec package:",
            "",
            "- `docs/specs/TEMPLATE_SPEC.md`",
            "- `docs/specs/TEMPLATE_PHASES.md`",
            "- `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`",
            "- `docs/specs/TEMPLATE_ITERATION.md`",
            "",
            "Naming rule:",
            "",
            "- `spec_slug` must be stable and unversioned (do not use `-v0` / `-v1` suffixes).",
            "",
        ]
    )


def _render_workflows_toml(*, spec: ModuleScaffoldSpec) -> str:
    return "\n".join(
        [
            "aware = 1",
            "",
            "[workflow]",
            'mode = "build"',
            f'module_toml_path = "modules/{spec.module_id}/aware.module.toml"',
        ]
    )


def _render_ontology_aware_toml(*, spec: ModuleScaffoldSpec) -> str:
    lines = [
        "aware = 1",
        "",
        "[package]",
        f'package_name = "{spec.ontology_package_name}"',
        f'fqn_prefix = "{spec.fqn_prefix}"',
        'kind = "ontology"',
        "version_number = 1",
        f'title = "{spec.title}"',
        f'description = "{spec.description}"',
        "",
        "[build]",
        f'environment_slug = "{spec.environment_slug}"',
    ]
    for dep in spec.dependencies:
        lines.extend(
            [
                "",
                "[[dependencies]]",
                f'package_name = "{dep}"',
            ]
        )
    return "\n".join(lines)


def _render_runtime_pyproject(*, spec: ModuleScaffoldSpec) -> str:
    ontology_runtime_dep = _aware_distribution_name(spec.ontology_package_name)
    lines = [
        "[project]",
        f'name = "{spec.runtime_project_name}"',
        'version = "0.1.0"',
        f'description = "Aware {spec.module_id.replace("_", "-")} runtime module."',
        'authors = [{ name = "AWARE Team" }]',
        'requires-python = ">=3.12"',
        "dependencies = [",
        '  "pydantic>=2.8.2,<3.0.0",',
        f'  "{ontology_runtime_dep}",',
        "]",
        "",
        "[project.optional-dependencies]",
        'test = ["pytest>=8.4.2"]',
        "",
        "[build-system]",
        'requires = ["hatchling>=1.27.0"]',
        'build-backend = "hatchling.build"',
        "",
        "[tool.hatch.build.targets.wheel]",
        f'packages = ["{spec.runtime_import_root}"]',
        "[tool.aware.tests]",
        f'requires_module = "{spec.module_id}"',
    ]
    return "\n".join(lines)


def _render_runtime_readme(*, spec: ModuleScaffoldSpec) -> str:
    return "\n".join(
        [
            f"# {spec.runtime_project_name}",
            "",
            f"Runtime package for the `{spec.module_id}` module.",
        ]
    )


def _render_seed_aware_source(*, spec: ModuleScaffoldSpec) -> str:
    class_name = f"{spec.class_prefix}Root"
    fn_name = f"create_{spec.module_snake}_root"
    default_name = spec.module_hyphen
    return "\n".join(
        [
            f"class {class_name} {{",
            "    // Attributes",
            "    name String",
            "",
            f'    fn {fn_name}(name String = "{default_name}") -> {class_name} {{',
            '        """',
            f"        Creates the default root object for the {spec.module_hyphen} module scaffold.",
            '        """',
            "    }",
            "}",
        ]
    )


def _render_environment_service_pyproject(*, spec: ModuleScaffoldSpec) -> str:
    service_project_name = f"aware-{spec.module_hyphen}-environment-service"
    runtime_distribution = f"aware-{spec.module_hyphen}"
    lines = [
        "[project]",
        f'name = "{service_project_name}"',
        'version = "0.1.0"',
        f'description = "Aware {spec.module_hyphen} module environment service adapters."',
        'authors = [{ name = "AWARE Team" }]',
        'requires-python = ">=3.12"',
        "dependencies = [",
        '  "aware-service-runtime",',
        f'  "{runtime_distribution}",',
        "]",
        "",
        "[project.optional-dependencies]",
        'test = ["pytest>=8.4.2"]',
        "",
        "[build-system]",
        'requires = ["hatchling>=1.27.0"]',
        'build-backend = "hatchling.build"',
        "",
        "[tool.hatch.build.targets.wheel]",
        f'packages = ["aware_{spec.module_snake}_environment_service"]',
    ]
    return "\n".join(lines)


def _render_environment_service_readme(*, spec: ModuleScaffoldSpec) -> str:
    service_project_name = f"aware-{spec.module_hyphen}-environment-service"
    return "\n".join(
        [
            f"# {service_project_name}",
            "",
            f"Environment app-surface service adapters owned by the `{spec.module_id}` module.",
            "",
            "This rail is not the source of canonical service ontology truth.",
            "",
            "Use `structure/ontology/**` for canonical ontology-owned service semantics.",
            "Use `services/environment/**` for environment-surface adapter code only.",
        ]
    )


def _render_environment_service_providers(*, spec: ModuleScaffoldSpec) -> str:
    _ = spec
    return "\n".join(
        [
            '"""Provider registry for module-owned environment service plugins."""',
            "",
            "from collections.abc import Callable",
            "",
            "",
            "def register_plugins(register: Callable[[type], type]) -> None:",
            "    _ = register",
        ]
    )


def _aware_distribution_name(package_name: str) -> str:
    normalized = package_name.replace("_", "-")
    if normalized.startswith("aware-"):
        return normalized
    if normalized.startswith("aware_"):
        return normalized.replace("aware_", "aware-", 1)
    return f"aware-{normalized}"


__all__ = [
    "ModulePackageRegistration",
    "ModuleScaffoldResult",
    "ModuleScaffoldSpec",
    "build_module_package_registrations",
    "build_module_scaffold_files",
    "build_module_scaffold_spec",
    "scaffold_module",
]
