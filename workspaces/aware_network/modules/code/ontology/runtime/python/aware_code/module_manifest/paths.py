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
    manifest_path: Path
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
        manifest_abs = (module_root / pkg.manifest).resolve()
        if not manifest_abs.exists():
            raise AwareModuleTomlError(
                f"aware.toml not found for package: {manifest_abs}"
            )
        toml_spec = load_aware_toml_spec(toml_path=manifest_abs)
        if toml_spec.package.kind == AwarePackageKind.ontology:
            ontology_tomls.append(manifest_abs)

    if len(ontology_tomls) != 1:
        raise AwareModuleTomlError(
            "Each module must declare exactly one ontology package in "
            + "aware.module.toml; "
            + f"found {len(ontology_tomls)} ({[str(p) for p in ontology_tomls]})."
        )

    manifest_path = ontology_tomls[0]
    return ModuleOntologyPaths(
        manifest_path=manifest_path, aware_root=manifest_path.parent.resolve()
    )


__all__ = [
    "ModuleOntologyPaths",
    "resolve_module_ontology_paths",
]
