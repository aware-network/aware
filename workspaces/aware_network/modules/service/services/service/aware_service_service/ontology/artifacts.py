from __future__ import annotations

import importlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from aware_orm.graph.plan_cache import GraphPlanCache
from aware_orm.graph.runtime import GraphSQLRuntime
from aware_orm.graph.serialization import deserialize_plans
from aware_orm.projection.plan import ProjectionPlanCache
from aware_orm.projection.runtime import ProjectionRuntime
from aware_orm.projection.serialization import deserialize_projection_plans
from aware_orm.runtime.bundle_binding import install_bindings_from_payload
from aware_orm.runtime.bundle_sql_metadata import (
    install_sql_metadata_from_bindings_payload,
)
from aware_orm.runtime.plan_registry import (
    build_graph_config_registry,
    load_plan_registry_from_payload,
)
from aware_service_runtime.host_contract import (
    ServiceHostContractError,
    ontology_runtime_artifact_root_from_manifest_path as _contract_ontology_runtime_artifact_root_from_manifest_path,
    ontology_runtime_artifact_sql_root_from_manifest_path as _contract_ontology_runtime_artifact_sql_root_from_manifest_path,
)
from aware_service_service.ontology.errors import (
    service_activation_requires_materialization as _service_activation_requires_materialization,
)
from aware_utils.logging import logger


def ontology_runtime_artifact_root_from_manifest_path(manifest_path: Path) -> Path:
    return _contract_ontology_runtime_artifact_root_from_manifest_path(manifest_path)


def ontology_runtime_artifact_sql_root_from_manifest_path(
    manifest_path: Path,
) -> Path:
    try:
        return _contract_ontology_runtime_artifact_sql_root_from_manifest_path(
            manifest_path
        )
    except ServiceHostContractError as exc:
        raise _service_activation_requires_materialization(str(exc)) from exc


def install_ontology_runtime_artifact_manifest(*, manifest_path: Path) -> int:
    resolved_manifest_path = manifest_path.expanduser().resolve()
    manifest = _load_json_mapping(resolved_manifest_path)
    if isinstance(manifest.get("modules"), list):
        raise _service_activation_requires_materialization(
            "ServiceHost runtime install requires package-owned ontology runtime "
            "artifact manifests; composed environment manifests are retired: "
            f"{resolved_manifest_path}"
        )
    if not isinstance(manifest.get("ocg"), Mapping):
        raise _service_activation_requires_materialization(
            "ServiceHost runtime install requires an ontology runtime artifact "
            f"manifest with an ocg descriptor: {resolved_manifest_path}"
        )

    base_path = resolved_manifest_path.parent
    for module_name in _ontology_runtime_manifest_python_modules(manifest):
        importlib.import_module(module_name)

    binding_snapshot = _manifest_artifact_bytes(
        manifest=manifest,
        artifact_key="ocg_binding_snapshot",
        base_path=base_path,
        required=True,
    )
    bindings = _manifest_artifact_bytes(
        manifest=manifest,
        artifact_key="bindings",
        base_path=base_path,
        required=True,
    )
    binding_result = install_bindings_from_payload(
        bindings=bindings,
        orm_graph_binding_snapshot_bytes=binding_snapshot,
        strict=True,
    )
    logger.info(
        "Ontology runtime artifact binding install complete "
        "(manifest=%s bound=%s planner_version=%s)",
        resolved_manifest_path,
        binding_result.bound_count,
        binding_result.planner_version,
    )
    sql_meta_result = install_sql_metadata_from_bindings_payload(
        bindings,
        strict=True,
    )
    logger.info(
        "Ontology runtime artifact SQL metadata installed " "(manifest=%s count=%s)",
        resolved_manifest_path,
        sql_meta_result.installed,
    )

    graphsql = _manifest_artifact_bytes(
        manifest=manifest,
        artifact_key="graphsql",
        base_path=base_path,
        required=False,
        require_ready_status=True,
    )
    if graphsql:
        plan_registry_payload = _manifest_artifact_bytes(
            manifest=manifest,
            artifact_key="plan_registry",
            base_path=base_path,
            required=False,
        )
        plan_registry = load_plan_registry_from_payload(plan_registry_payload)
        GraphSQLRuntime.install(
            GraphPlanCache(deserialize_plans(graphsql)),
            build_graph_config_registry(plan_registry=plan_registry),
            plan_registry,
        )

    projection_plans = _manifest_artifact_bytes(
        manifest=manifest,
        artifact_key="projection_plans",
        base_path=base_path,
        required=False,
    )
    if not projection_plans:
        return 0
    projection_cache = ProjectionPlanCache(
        deserialize_projection_plans(projection_plans)
    )
    ProjectionRuntime.extend(projection_cache)
    return len(tuple(projection_cache.all()))


def _ontology_runtime_manifest_python_modules(
    manifest: Mapping[str, object],
) -> tuple[str, ...]:
    loader = manifest.get("loader")
    if not isinstance(loader, Mapping):
        return ()
    raw_modules = loader.get("python_modules") or loader.get("python_imports")
    if isinstance(raw_modules, str):
        modules = (raw_modules,)
    elif isinstance(raw_modules, Sequence) and not isinstance(
        raw_modules, (bytes, str)
    ):
        modules = tuple(str(item) for item in raw_modules)
    else:
        modules = ()
    return tuple(dict.fromkeys(module.strip() for module in modules if module.strip()))


def _manifest_artifact_bytes(
    *,
    manifest: Mapping[str, object],
    artifact_key: str,
    base_path: Path,
    required: bool,
    require_ready_status: bool = False,
) -> bytes | None:
    descriptor = manifest.get(artifact_key)
    if not isinstance(descriptor, Mapping):
        if required:
            raise _service_activation_requires_materialization(
                "Ontology runtime artifact manifest is missing artifact "
                f"{artifact_key!r}."
            )
        return None
    if require_ready_status:
        status = str(descriptor.get("status") or "").strip()
        if status and status != "ready":
            return None
    raw_file = str(descriptor.get("file") or "").strip()
    if not raw_file:
        if required:
            raise _service_activation_requires_materialization(
                "Ontology runtime artifact manifest entry is missing file: "
                f"{artifact_key!r}."
            )
        return None
    path = Path(raw_file).expanduser()
    if not path.is_absolute():
        path = base_path / path
    resolved_path = path.resolve()
    if not resolved_path.is_file():
        if required:
            raise _service_activation_requires_materialization(
                "Ontology runtime artifact manifest entry points to a missing "
                f"file: artifact={artifact_key!r} path={resolved_path}"
            )
        return None
    return resolved_path.read_bytes()


def _load_json_mapping(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise _service_activation_requires_materialization(
            f"Ontology runtime artifact manifest must be valid JSON: {path}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise _service_activation_requires_materialization(
            f"Ontology runtime artifact manifest must decode to an object: {path}"
        )
    return cast(dict[str, object], payload)


__all__ = [
    "install_ontology_runtime_artifact_manifest",
    "ontology_runtime_artifact_root_from_manifest_path",
    "ontology_runtime_artifact_sql_root_from_manifest_path",
]
