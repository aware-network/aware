"""Package rail installer

This module loads embedded `_aware/*` resources and delegates binding to the
ORM-native graph binding contract.
"""

import base64
from importlib import import_module
from importlib.resources import files
import sys

from pydantic import ValidationError

from aware_orm._support import logger

from .package_artifacts import (
    DEFAULT_ARTIFACTS_DIR,
    PYTHON_MODELS_MANIFEST_FILENAME,
    ORM_GRAPH_BINDING_FILENAME,
    ORM_GRAPH_BINDING_B64_FILENAME,
    get_package_artifact_paths,
)
from .bootstrap_context import defer_install, get_bootstrap_root
from .graph_binding import bind_entities_by_fqn, index_entities_from_msgpack
from .errors import PackageInstallError


_INSTALLING: set[str] = set()
_INSTALLED: set[str] = set()


def _installed_package_is_current(
    *,
    package_prefix: str,
    artifacts_dir: str,
) -> bool:
    try:
        from .models_manifest import ModelsManifest
        from aware_orm.registry import ORMModelRegistry
    except Exception:
        return True

    try:
        models_path, _ = get_package_artifact_paths(
            package_prefix=package_prefix,
            artifacts_dir=artifacts_dir,
        )
    except Exception:
        return True
    if not models_path.is_file():
        return True

    try:
        models_manifest = ModelsManifest.model_validate_json(
            models_path.read_text(encoding="utf-8")
        )
    except Exception:
        return True

    if not models_manifest.classes:
        return True

    for entry in models_manifest.classes:
        fqn = f"{entry.module}.{entry.name}"
        model_class = ORMModelRegistry.get_class_by_fqn(fqn)
        if model_class is None:
            return False

        module_obj = sys.modules.get(entry.module)
        if module_obj is None:
            return False
        if getattr(module_obj, entry.name, None) is not model_class:
            return False

        class_config = model_class.get_class_config()
        if getattr(class_config, "id", None) != entry.class_config_id:
            return False
        if (
            ORMModelRegistry.get_class_by_class_config_id(entry.class_config_id)
            is not model_class
        ):
            return False

    return True


def install_package_runtime_artifacts(
    *,
    package_prefix: str,
    artifacts_dir: str = DEFAULT_ARTIFACTS_DIR,
    strict: bool = True,
) -> None:
    """Bind canonical ClassConfigs to ORM model classes from embedded package resources."""

    # IMPORTANT: do not import `aware_environment` from here.
    #
    # Generated ontology packages import `aware_orm.runtime` during bootstrap, and
    # `aware_environment/__init__.py` is intentionally heavy (docs + runtime exports).
    # Importing it here can re-order ontology imports and break forward-ref rebuilds.
    from .models_manifest import ModelsManifest

    # IMPORTANT (canonical bootstrap contract):
    #
    # Installing embedded artifacts requires parsing binding snapshots, which can transitively
    # import other generated packages. When a package is imported as a *dependency* during a
    # root package bootstrap, running installs eagerly can re-enter the bootstrap stack and
    # create cycles (even when the declared dependency graph is a DAG).
    #
    # Therefore: if there is an active bootstrap root and it's not this package, defer install
    # until the root completes bootstrapping and drains deferred installs.
    root = get_bootstrap_root()
    if root is not None and root != package_prefix:
        logger.debug(f"Deferring install for dependency {package_prefix} (bootstrap root={root})")
        defer_install(root_package=root, package_prefix=package_prefix)
        return

    # Re-entrancy guard: this function is invoked during package `__init__` import.
    if package_prefix in _INSTALLED and _installed_package_is_current(
        package_prefix=package_prefix,
        artifacts_dir=artifacts_dir,
    ):
        return
    if package_prefix in _INSTALLING:
        msg = f"Re-entrant install_package_runtime_artifacts detected for {package_prefix}"
        # During recursive package bootstraps, a dependency may be imported while its
        # artifacts are still being installed. Treat this as a no-op: the outer install
        # will complete and mark the package as installed.
        logger.warning(msg)
        return

    _INSTALLING.add(package_prefix)
    models_path, binding_path = get_package_artifact_paths(
        package_prefix=package_prefix,
        artifacts_dir=artifacts_dir,
    )
    b64_path = files(import_module(package_prefix)).joinpath(
        artifacts_dir,
        ORM_GRAPH_BINDING_B64_FILENAME,
    )

    binding_bytes: bytes | None = None
    if binding_path.is_file():
        binding_bytes = binding_path.read_bytes()
    elif b64_path.is_file():
        try:
            binding_bytes = base64.b64decode(b64_path.read_text(encoding="utf-8"), validate=True)
        except Exception as exc:
            msg = (
                f"Invalid embedded fallback runtime artifact under {package_prefix}/{artifacts_dir}: "
                f"{ORM_GRAPH_BINDING_B64_FILENAME} decode failed ({exc})"
            )
            if strict:
                raise PackageInstallError(msg) from exc
            logger.critical(msg)
            return

    if not models_path.is_file() or binding_bytes is None:
        msg = (
            f"Missing embedded runtime artifacts under {package_prefix}/{artifacts_dir}: "
            f"{PYTHON_MODELS_MANIFEST_FILENAME}={models_path.is_file()}, "
            f"{ORM_GRAPH_BINDING_FILENAME}={binding_path.is_file()}, "
            f"{ORM_GRAPH_BINDING_B64_FILENAME}={b64_path.is_file()}"
        )
        if strict:
            raise PackageInstallError(msg)
        logger.critical(msg)
        return

    try:
        models_manifest = ModelsManifest.model_validate_json(models_path.read_text(encoding="utf-8"))
        try:
            entity_index = index_entities_from_msgpack(binding_bytes)
        except ValidationError as exc:
            hint = (
                "Invalid embedded ORM graph binding snapshot schema; this package likely contains stale "
                + "generated artifacts. "
                + "Recompile/update the module artifacts and refresh caches."
            )
            if strict:
                raise PackageInstallError(f"{package_prefix}: {hint}") from exc
            logger.critical("%s: %s", package_prefix, hint)
            return

        # Ensure modules are importable (best-effort) before binding.
        # Most modules should already be imported by `bootstrap_orm_package`; skip those.
        modules_to_import = sorted({e.module for e in models_manifest.classes})
        for module_name in modules_to_import:
            if module_name in sys.modules:
                continue
            try:
                import_module(module_name)
            except Exception as exc:
                if strict:
                    raise
                logger.critical(f"Package artifacts: failed to import {module_name}: {exc}")

        pairs = [(f"{e.module}.{e.name}", str(e.class_config_id)) for e in models_manifest.classes]
        try:
            bind_entities_by_fqn(bindings=pairs, entity_index=entity_index, strict=strict)
        except RuntimeError as exc:
            raise PackageInstallError(str(exc)) from exc
    finally:
        _INSTALLING.discard(package_prefix)
        _INSTALLED.add(package_prefix)
