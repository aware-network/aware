"""Helpers to deterministically bootstrap generated Pydantic (DTO) packages.

SSOT:
- DTO packages are pure wire contracts.
- They MUST NOT import aware_orm or install runtime artifacts.
"""

from __future__ import annotations

import json
from importlib import import_module
from importlib.resources import files
import sys
from typing import Any

from aware_utils.logging import logger

from aware_utils.pydantic.class_config_registry import (
    register_pydantic_package_class_configs,
)


def _collect_pydantic_models(
    *, modules: list[object], package_prefix: str
) -> list[type[Any]]:
    """Collect Pydantic model classes defined in the given module objects."""
    from pydantic import BaseModel as PydanticBaseModel

    local_models: list[type[Any]] = []
    for module_obj in modules:
        module_dict = getattr(module_obj, "__dict__", {})
        if not isinstance(module_dict, dict):
            continue
        for value in module_dict.values():
            if not isinstance(value, type):
                continue
            if value is PydanticBaseModel:
                continue
            try:
                if not issubclass(value, PydanticBaseModel):
                    continue
            except Exception:
                continue

            module_name = getattr(value, "__module__", "")
            if not module_name.startswith(package_prefix + "."):
                continue
            local_models.append(value)

    return local_models


def bootstrap_pydantic_package(
    *,
    package_prefix: str,
    module_names: list[str],
    strict_imports: bool = False,
    extra_types_ns: dict[str, object] | None = None,
) -> None:
    """Bootstrap a generated DTO package (Pydantic-only).

    Responsibilities:
    - Import generated modules in a deterministic order.
    - Rebuild Pydantic models so forward references resolve.

    Non-responsibilities:
    - ORM registration / OCG→ORM binding (belongs to aware_orm).
    - Touching filesystem artifacts.
    """

    # Preserve the renderer-provided import order.
    seen: set[str] = set()
    ordered: list[str] = []
    for m in module_names:
        if m in seen:
            continue
        ordered.append(m)
        seen.add(m)
    module_names = ordered

    imported_modules: list[object] = []
    for mod in module_names:
        try:
            imported_modules.append(import_module(mod))
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            logger.critical(
                f"Package bootstrap (pydantic): failed to import {mod}: {exc}"
            )

    # Collect local Pydantic model classes defined in the imported modules.
    try:
        local_models = _collect_pydantic_models(
            modules=imported_modules, package_prefix=package_prefix
        )
    except Exception as exc:
        if strict_imports:  # pragma: no cover
            raise
        logger.critical(
            f"Package bootstrap (pydantic): failed to scan local models: {exc}"
        )
        local_models = []

    # Shared namespace for resolving forward references.
    #
    # Prefer local package models on name collisions.
    types_ns: dict[str, object] = {
        # Ensure builtin container generics resolve to builtin types even when a model
        # class defines a method with the same name (e.g. `Terminal.list`).
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "frozenset": frozenset,
    }
    if extra_types_ns:
        for name, value in extra_types_ns.items():
            if name and name not in types_ns:
                types_ns[name] = value
    for model_class in local_models:
        name = getattr(model_class, "__name__", None)
        if name:
            types_ns[name] = model_class

    def _rebuild_ns_for_model(model_class: type[Any]) -> dict[str, object]:
        module_name = getattr(model_class, "__module__", "")
        module_ns: dict[str, object] = {}
        try:
            module_obj = import_module(module_name)
            module_dict = getattr(module_obj, "__dict__", {})
            if isinstance(module_dict, dict):
                module_ns = module_dict
        except Exception:
            module_ns = {}

        # Start from module globals so imported symbols used in annotations resolve,
        # then overlay our synthesized namespace (builtins + local models).
        ns = dict(module_ns)
        ns.update(types_ns)
        return ns

    # Deterministic rebuild ordering for stable logs and behavior.
    local_models = sorted(
        local_models,
        key=lambda c: (getattr(c, "__module__", ""), getattr(c, "__name__", "")),
    )

    for model_class in local_models:
        shadow: dict[str, object] = {}
        try:
            rebuild_ns = _rebuild_ns_for_model(model_class)

            # Guard against builtin generic shadowing during eval.
            for name, builtin_type in {
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "frozenset": frozenset,
            }.items():
                try:
                    v = getattr(model_class, name)
                except Exception:
                    continue
                if callable(v) and not isinstance(v, type):
                    shadow[name] = v
                    setattr(model_class, name, builtin_type)

            model_class.model_rebuild(_types_namespace=rebuild_ns)
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            model_name = getattr(model_class, "__name__", "<unknown>")
            logger.critical(
                "Package bootstrap (pydantic): failed model_rebuild for "
                f"{model_name}: {exc}",
            )
        finally:
            for name, original in shadow.items():
                try:
                    setattr(model_class, name, original)
                except Exception:
                    pass


def _publish_pydantic_package_model_aliases(
    *,
    package_prefix: str,
    classes_payload: object,
) -> None:
    """Expose generated models from authored package-level class refs.

    API manifests intentionally use authored refs such as
    `aware_code_service_dto.code.PublishCodePackageResponse`. The generated class may
    live in a leaf module like `aware_code_service_dto.code.features.package_distribution`,
    so publish the class on the package module after bootstrap imports it.
    """

    if not isinstance(classes_payload, list):
        return

    for entry in classes_payload:
        if not isinstance(entry, dict):
            continue
        module_name = str(entry.get("module") or "").strip()
        class_name = str(entry.get("name") or "").strip()
        if not module_name or not class_name:
            continue
        if not module_name.startswith(package_prefix + "."):
            continue

        package_module_name, _, _ = module_name.rpartition(".")
        if not package_module_name:
            continue
        try:
            source_module = import_module(module_name)
            package_module = import_module(package_module_name)
            model_class = getattr(source_module, class_name)
        except Exception as exc:
            logger.debug(
                "Package bootstrap (pydantic): failed to publish model alias "
                f"{package_module_name}.{class_name}: {exc}"
            )
            continue

        if not hasattr(package_module, class_name):
            setattr(package_module, class_name, model_class)


_BOOTSTRAPPING: set[str] = set()
_BOOTSTRAPPED_ROOT_BY_PACKAGE: dict[str, str] = {}


def bootstrap_pydantic_package_from_artifacts(
    *,
    package_prefix: str,
    strict_imports: bool = False,
) -> None:
    """
    Bootstrap a generated DTO package using embedded `_aware/python.bootstrap.json`.

    This keeps generated `__init__.py` stable (no huge module lists) while still
    ensuring deterministic dependency-first import + Pydantic model rebuilds.
    """

    try:
        pkg = import_module(package_prefix)
        root = files(pkg)
        root_key = str(root)
    except Exception as exc:
        if strict_imports:  # pragma: no cover
            raise
        logger.critical(
            f"Package bootstrap (pydantic): missing package root for {package_prefix}: {exc}"
        )
        return

    if _BOOTSTRAPPED_ROOT_BY_PACKAGE.get(package_prefix) == root_key:
        return
    if package_prefix in _BOOTSTRAPPING:
        msg = f"Re-entrant bootstrap_pydantic_package_from_artifacts detected for {package_prefix}"
        if strict_imports:  # pragma: no cover
            raise RuntimeError(msg)
        logger.warning(msg)
        return

    _BOOTSTRAPPING.add(package_prefix)
    success = False
    try:
        bootstrap_path = root.joinpath("_aware", "python.bootstrap.json")
        payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))

        # Register embedded ClassConfig binding snapshots (DTO packages only).
        #
        # This is not ORM binding: it only registers class-level semantic metadata
        # (e.g., `ClassConfig.value_mode`) so runtimes can encode/decode CLASS values
        # deterministically without heuristics.
        try:
            register_pydantic_package_class_configs(
                package_prefix=package_prefix, strict=False
            )
        except Exception:
            # Best-effort: DTO packages must remain importable even if metadata is unavailable.
            if strict_imports:  # pragma: no cover
                raise

        # `dependency_import_roots` means the generated source references those roots.
        # Only `pydantic_model_dependency_import_roots` is safe to pre-import and
        # scan for Pydantic model classes needed by forward refs.
        deps = _normalized_manifest_roots(
            payload.get("pydantic_model_dependency_import_roots")
        )
        dependency_types: dict[str, object] = {}
        for dep_norm in deps:
            try:
                dep_pkg = import_module(dep_norm)
            except Exception as exc:
                if strict_imports:  # pragma: no cover
                    raise
                logger.critical(
                    f"Package bootstrap (pydantic): failed to import dependency {dep_norm}: {exc}"
                )
                continue
            try:
                dep_root = files(dep_pkg)
                dep_bootstrap = dep_root.joinpath("_aware", "python.bootstrap.json")
                dep_payload = json.loads(dep_bootstrap.read_text(encoding="utf-8"))
                dep_modules = dep_payload.get("modules") or []
                module_names = [
                    m for m in dep_modules if isinstance(m, str) and m.strip()
                ]
                imported: list[object] = []
                for mod in module_names:
                    try:
                        imported.append(import_module(mod))
                    except Exception:
                        continue
                if not imported:
                    imported = [
                        m
                        for name, m in sys.modules.items()
                        if isinstance(name, str) and name.startswith(dep_norm + ".")
                    ]
                dep_models = _collect_pydantic_models(
                    modules=imported, package_prefix=dep_norm
                )
                for model_class in dep_models:
                    name = getattr(model_class, "__name__", None)
                    if name and name not in dependency_types:
                        dependency_types[name] = model_class
            except Exception as exc:
                if strict_imports:  # pragma: no cover
                    raise
                logger.debug(
                    f"Package bootstrap (pydantic): failed to scan dependency models {dep_norm}: {exc}"
                )

        modules = payload.get("modules") or []
        module_names: list[str] = []
        if isinstance(modules, list):
            module_names = [m for m in modules if isinstance(m, str) and m.strip()]

        bootstrap_pydantic_package(
            package_prefix=package_prefix,
            module_names=module_names,
            strict_imports=strict_imports,
            extra_types_ns=dependency_types,
        )
        try:
            models_path = root.joinpath("_aware", "python.models.json")
            models_payload = json.loads(models_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            logger.debug(
                "Package bootstrap (pydantic): missing python.models.json for "
                f"{package_prefix}: {exc}"
            )
            models_payload = {}
        _publish_pydantic_package_model_aliases(
            package_prefix=package_prefix,
            classes_payload=models_payload.get("classes"),
        )
        success = True
    except Exception as exc:
        if strict_imports:  # pragma: no cover
            raise
        logger.critical(
            f"Package bootstrap (pydantic): missing or invalid python.bootstrap.json: {exc}"
        )
        return
    finally:
        _BOOTSTRAPPING.discard(package_prefix)
        if success:
            _BOOTSTRAPPED_ROOT_BY_PACKAGE[package_prefix] = root_key


def _normalized_manifest_roots(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    roots: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item.strip():
            continue
        root = item.replace("-", "_").strip()
        if not root or root in seen:
            continue
        roots.append(root)
        seen.add(root)
    return roots


__all__ = ["bootstrap_pydantic_package", "bootstrap_pydantic_package_from_artifacts"]
