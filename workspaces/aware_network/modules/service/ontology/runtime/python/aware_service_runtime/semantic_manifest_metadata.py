from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from aware_service_runtime.builder import build_service_compile_plan
from aware_service_runtime.workspace import ServiceWorkspace
from aware_service_ontology.stable_ids import stable_service_config_id


def resolve_service_manifest_semantic_package_metadata(
    *,
    workspace_root: Path,
    package_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    descriptor: object,
    metadata: Mapping[str, object],
) -> Mapping[str, object]:
    """Return Service-owned root identity metadata for a service manifest."""

    snapshot = ServiceWorkspace.from_toml(
        toml_path=manifest_path,
        repo_root=workspace_root,
    ).build_snapshot()
    compile_plan = build_service_compile_plan(snapshot=snapshot)
    service_names = tuple(config.name for config in compile_plan.service_configs)
    if len(service_names) != 1:
        raise ValueError(
            "Service semantic package metadata requires exactly one canonical "
            "`service` declaration per aware.service.toml package: "
            f"manifest_path={manifest_path} discovered={sorted(service_names)!r}"
        )
    service_name = service_names[0]
    service_config_id = stable_service_config_id(name=service_name)
    return {
        "semantic_root_name": service_name,
        "semantic_root_names": service_names,
        "semantic_root_id": str(service_config_id),
        "semantic_root_ids": (str(service_config_id),),
        "service_name": service_name,
        "service_names": service_names,
    }


__all__ = [
    "resolve_service_manifest_semantic_package_metadata",
]
