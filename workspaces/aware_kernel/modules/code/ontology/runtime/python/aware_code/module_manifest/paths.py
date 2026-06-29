"""Path helpers for module package layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_code.module_manifest.loader import AwareModuleTomlError
from aware_code.module_manifest.spec import AwareModuleSpec
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import AwarePackageKind


@dataclass(frozen=True, slots=True)
class ModuleOntologyPaths:
    aware_toml_path: Path
    aware_root: Path


def resolve_module_ontology_paths(
    *, module_root: Path, module_spec: AwareModuleSpec
) -> ModuleOntologyPaths:
    """Resolve the module's ontology package root (directory containing its `aware.toml`)."""
    module_root = Path(module_root).expanduser().resolve()

    ontology_tomls: list[Path] = []
    for pkg in module_spec.packages:
        if pkg.kind != "ontology":
            continue
        aware_toml_abs = (module_root / pkg.aware_toml_path).resolve()
        if not aware_toml_abs.exists():
            raise AwareModuleTomlError(
                f"aware.toml not found for package: {aware_toml_abs}"
            )
        toml_spec = load_aware_toml_spec(toml_path=aware_toml_abs)
        if toml_spec.package.kind == AwarePackageKind.ontology:
            ontology_tomls.append(aware_toml_abs)

    if len(ontology_tomls) != 1:
        raise AwareModuleTomlError(
            "Each module must declare exactly one ontology package in "
            + "aware.module.toml; "
            + f"found {len(ontology_tomls)} ({[str(p) for p in ontology_tomls]})."
        )

    aware_toml_path = ontology_tomls[0]
    return ModuleOntologyPaths(
        aware_toml_path=aware_toml_path, aware_root=aware_toml_path.parent.resolve()
    )


__all__ = [
    "ModuleOntologyPaths",
    "resolve_module_ontology_paths",
]
