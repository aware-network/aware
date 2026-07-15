"""Helpers to deterministically bootstrap generated ORM packages.

Goal:
- Keep generated package `__init__.py` very small and declarative.
- Centralize the token-precise mechanics of:
  - importing module list
  - registering ORMModel subclasses into ORMModelRegistry
  - rebuilding models with a shared _types_namespace to resolve forward refs

This is intentionally "pure runtime glue": it does not touch environment bundles,
manifests, or the filesystem.
"""

from __future__ import annotations

import json
import ast
import sys
from functools import lru_cache
from importlib import import_module
from importlib.resources import files
from pathlib import Path
from typing import Any

from aware_orm._support import logger

from .bootstrap_context import (
    get_bootstrap_root,
    pop_deferred_installs,
    reset_bootstrap_root,
    set_bootstrap_root,
)
from .package_artifacts import DEFAULT_ARTIFACTS_DIR, PYTHON_BOOTSTRAP_MANIFEST_FILENAME


@lru_cache(maxsize=512)
def _get_type_checking_imports(module_name: str) -> dict[str, object]:
    """
    Best-effort resolution of symbols imported under `if TYPE_CHECKING:`.

    Why:
    - Generated ontology modules commonly keep relationship imports under TYPE_CHECKING to
      avoid runtime import cycles.
    - Pydantic v2 still needs those symbols available when evaluating postponed annotations.
    - When multiple packages define the same class name (e.g. `StorageBucket`), relying on
      a flat name→class namespace can resolve to the wrong type. TYPE_CHECKING imports are
      the canonical intent for which symbol a module wants for a given name.
    """

    try:
        module_obj = import_module(module_name)
    except Exception:
        return {}

    file_path = getattr(module_obj, "__file__", None)
    if not isinstance(file_path, str) or not file_path:
        return {}

    try:
        src = Path(file_path).read_text(encoding="utf-8")
    except Exception:
        return {}

    try:
        tree = ast.parse(src, filename=file_path)
    except Exception:
        return {}

    out: dict[str, object] = {}

    def _import_as(module_path: str, name: str, as_name: str) -> None:
        try:
            mod = import_module(module_path)
        except Exception:
            return
        try:
            out[as_name] = getattr(mod, name)
        except Exception:
            return

    def _import_module_as(module_path: str, as_name: str) -> None:
        try:
            out[as_name] = import_module(module_path)
        except Exception:
            return

    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"):
            continue

        for stmt in node.body:
            if isinstance(stmt, ast.ImportFrom):
                module_path = stmt.module
                if not isinstance(module_path, str) or not module_path:
                    continue
                for alias in stmt.names:
                    name = alias.name
                    as_name = alias.asname or name
                    if not isinstance(name, str) or not isinstance(as_name, str):
                        continue
                    _import_as(module_path, name, as_name)
            elif isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    module_path = alias.name
                    if not isinstance(module_path, str) or not module_path:
                        continue
                    as_name = alias.asname or module_path.split(".", 1)[0]
                    if not isinstance(as_name, str) or not as_name:
                        continue
                    _import_module_as(module_path, as_name)

    return out


_BOOTSTRAPPING: set[str] = set()
_BOOTSTRAPPED: set[str] = set()


def _manifest_module_names(*, package_prefix: str) -> tuple[str, ...]:
    try:
        pkg = import_module(package_prefix)
        root = files(pkg)
        manifest_path = root.joinpath(
            DEFAULT_ARTIFACTS_DIR,
            PYTHON_BOOTSTRAP_MANIFEST_FILENAME,
        )
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return ()

    modules = payload.get("modules") or []
    if not isinstance(modules, list):
        return ()
    return tuple(m for m in modules if isinstance(m, str) and m.strip())


def _bootstrapped_package_is_current(*, package_prefix: str) -> bool:
    try:
        from aware_orm.registry import ORMModelRegistry

        existing = ORMModelRegistry.get_all_fqn_to_class()
    except Exception:
        return True

    package_fqns = {
        fqn: model_class
        for fqn, model_class in existing.items()
        if fqn.startswith(package_prefix + ".")
    }
    if not package_fqns:
        return False

    manifest_modules = _manifest_module_names(package_prefix=package_prefix)
    for module_name in manifest_modules:
        if module_name not in sys.modules:
            return False

    for fqn, model_class in package_fqns.items():
        module_name, _, class_name = fqn.rpartition(".")
        if not module_name or not class_name:
            return False
        module_obj = sys.modules.get(module_name)
        if module_obj is None:
            return False
        if getattr(module_obj, class_name, None) is not model_class:
            return False

    return True


def _discard_stale_registry_class(registry: object, model_class: type[Any]) -> None:
    class_name = getattr(model_class, "__name__", None)
    if isinstance(class_name, str) and class_name:
        try:
            name_index = getattr(registry, "_name_to_classes")
            classes = name_index.get(class_name)
            if isinstance(classes, list):
                name_index[class_name] = [
                    candidate for candidate in classes if candidate is not model_class
                ]
        except Exception:
            pass

    try:
        class_config_index = getattr(registry, "_class_config_id_to_model")
        for class_config_id, candidate in list(class_config_index.items()):
            if candidate is model_class:
                class_config_index.pop(class_config_id, None)
    except Exception:
        pass


def _register_stub_models_from_manifest(*, package_prefix: str, strict_imports: bool) -> None:
    """Best-effort: import a package's declared modules and register ORMModel stubs.

    This is used to break bootstrap re-entrancy deadlocks where:
    - Package A is bootstrapping (dependencies-first)
    - A dependency (or runtime helper) imports package A again before A has imported its modules
    - Pydantic `model_rebuild` in the dependency then fails because symbols from A do not exist yet

    Importing module bodies is safe because generated ontology modules must not execute
    relationship imports at runtime (they are guarded under TYPE_CHECKING).
    """

    try:
        pkg = import_module(package_prefix)
        root = files(pkg)
        manifest_path = root.joinpath(DEFAULT_ARTIFACTS_DIR, PYTHON_BOOTSTRAP_MANIFEST_FILENAME)
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return

    modules = payload.get("modules") or []
    if not isinstance(modules, list):
        return
    module_names = [m for m in modules if isinstance(m, str) and m.strip()]
    if not module_names:
        return

    try:
        from aware_orm.models.orm_model import ORMModel
        from aware_orm.registry import ORMModelRegistry
    except Exception:
        return

    imported_modules: list[object] = []
    for mod in module_names:
        try:
            imported_modules.append(import_module(mod))
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            logger.debug(f"Package bootstrap: re-entrant stub import failed for {mod}: {exc}")

    try:
        existing_fqns = ORMModelRegistry.get_all_fqn_to_class()
    except Exception:
        return

    for module_obj in imported_modules:
        module_dict = getattr(module_obj, "__dict__", {})
        if not isinstance(module_dict, dict):
            continue
        for value in module_dict.values():
            if not isinstance(value, type):
                continue
            if value is ORMModel:
                continue
            try:
                if not issubclass(value, ORMModel):
                    continue
            except Exception:
                continue
            module_name = getattr(value, "__module__", "")
            if not module_name.startswith(package_prefix + "."):
                continue
            try:
                fqn = ORMModelRegistry.get_fqn_for_class(value)
            except Exception:
                continue
            existing_class = existing_fqns.get(fqn)
            if existing_class is value:
                continue
            if existing_class is not None:
                _discard_stale_registry_class(ORMModelRegistry, existing_class)
            try:
                ORMModelRegistry.register_class_stub(value)
                setattr(value, "_registry_key", fqn)
                existing_fqns[fqn] = value
            except Exception:
                if strict_imports:  # pragma: no cover
                    raise
                continue


def bootstrap_orm_package_from_artifacts(
    *,
    package_prefix: str,
    strict_imports: bool = False,
) -> None:
    """
    Bootstrap a generated ORM package using embedded `_aware/python.bootstrap.json`.

    Why:
    - Keeps generated `__init__.py` stable (no huge module lists).
    - Ensures deterministic dependency-first import + Pydantic `model_rebuild`.
    """

    if package_prefix in _BOOTSTRAPPED:
        # Tests can temporarily clear ORMModelRegistry while ontology packages remain imported.
        # In that case the package is "bootstrapped" (import + model_rebuild happened) but the
        # registry no longer contains the classes required for bundle binding installs.
        #
        # Also handle import-cache isolation: sys.modules can be cleared while the registry
        # still points at old class objects. In that case, re-run bootstrap so generated
        # package imports install and rebuild the current class objects.
        if _bootstrapped_package_is_current(package_prefix=package_prefix):
            return
        _get_type_checking_imports.cache_clear()
    if package_prefix in _BOOTSTRAPPING:
        msg = f"Re-entrant bootstrap_orm_package_from_artifacts detected for {package_prefix}"
        if strict_imports:  # pragma: no cover
            raise RuntimeError(msg)
        logger.warning(msg)
        _register_stub_models_from_manifest(package_prefix=package_prefix, strict_imports=False)
        return

    root = get_bootstrap_root()
    is_root_call = root is None
    token = set_bootstrap_root(package_prefix) if is_root_call else None

    _BOOTSTRAPPING.add(package_prefix)
    success = False
    try:
        try:
            pkg = import_module(package_prefix)
            root = files(pkg)
            manifest_path = root.joinpath(DEFAULT_ARTIFACTS_DIR, PYTHON_BOOTSTRAP_MANIFEST_FILENAME)
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            logger.critical(f"Package bootstrap: missing or invalid {PYTHON_BOOTSTRAP_MANIFEST_FILENAME}: {exc}")
            return

        deps = payload.get("dependency_import_roots") or []
        deps_list: list[str] = []
        if isinstance(deps, list):
            deps_list = [d for d in deps if isinstance(d, str) and d.strip()]

        modules = payload.get("modules") or []
        module_names: list[str] = []
        if isinstance(modules, list):
            module_names = [m for m in modules if isinstance(m, str) and m.strip()]

        # Import dependencies first (they bootstrap themselves on import).
        for dep in deps_list:
            dep_norm = dep.replace("-", "_").strip()
            try:
                import_module(dep_norm)
            except Exception as exc:
                if strict_imports:  # pragma: no cover
                    raise
                logger.critical(f"Package bootstrap: failed to import dependency {dep_norm}: {exc}")

        success = bootstrap_orm_package(
            package_prefix=package_prefix,
            module_names=module_names,
            strict_imports=strict_imports,
        )
    finally:
        _BOOTSTRAPPING.discard(package_prefix)
        if success:
            _BOOTSTRAPPED.add(package_prefix)

        # Root bootstrap: after all dependency packages have been imported and rebuilt, install
        # deferred package artifacts in dependency order.
        if is_root_call:
            if token is not None:
                reset_bootstrap_root(token)
            if success:
                try:
                    _install_deferred_package_artifacts(root_package=package_prefix, strict=strict_imports)
                except Exception:
                    if strict_imports:  # pragma: no cover
                        raise
                    logger.critical(
                        "Package bootstrap: failed to install deferred artifacts",
                        exc_info=True,
                    )
        elif token is not None:  # pragma: no cover
            # Defensive: we only set the token for root calls.
            reset_bootstrap_root(token)


def _load_bootstrap_manifest(*, package_prefix: str) -> dict[str, Any]:
    pkg = import_module(package_prefix)
    root = files(pkg)
    manifest_path = root.joinpath(DEFAULT_ARTIFACTS_DIR, PYTHON_BOOTSTRAP_MANIFEST_FILENAME)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _install_deferred_package_artifacts(*, root_package: str, strict: bool) -> None:
    from .package_install import install_package_runtime_artifacts

    deferred = pop_deferred_installs(root_package)
    packages: set[str] = {root_package, *deferred}
    if not packages:
        return

    manifests: dict[str, dict[str, Any]] = {}
    for pkg in packages:
        try:
            manifests[pkg] = _load_bootstrap_manifest(package_prefix=pkg)
        except Exception as exc:
            if strict:  # pragma: no cover
                raise
            logger.critical(f"Package bootstrap: failed to read bootstrap manifest for {pkg}: {exc}")
            manifests[pkg] = {}

    dep_edges: dict[str, set[str]] = {pkg: set() for pkg in packages}
    for pkg, payload in manifests.items():
        deps = payload.get("dependency_import_roots") or []
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if not isinstance(dep, str) or not dep.strip():
                continue
            dep_norm = dep.replace("-", "_").strip()
            if dep_norm in packages:
                dep_edges[pkg].add(dep_norm)

    # Kahn topological sort.
    incoming_count: dict[str, int] = {pkg: 0 for pkg in packages}
    for pkg, deps in dep_edges.items():
        for dep in deps:
            incoming_count[pkg] += 1

    ready: list[str] = sorted([pkg for pkg, n in incoming_count.items() if n == 0])
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for child, deps in dep_edges.items():
            if n not in deps:
                continue
            incoming_count[child] -= 1
            if incoming_count[child] == 0:
                ready.append(child)
                ready.sort()

    if len(order) != len(packages):
        msg = f"Detected a package dependency cycle while installing artifacts: {sorted(packages)}"
        if strict:
            raise RuntimeError(msg)
        logger.critical(msg)
        # Best-effort fallback: install in import order.
        order = sorted(packages)

    for pkg in order:
        try:
            install_package_runtime_artifacts(package_prefix=pkg, strict=True)
        except Exception as exc:
            if strict:  # pragma: no cover
                raise
            logger.critical(f"Package bootstrap: failed to install artifacts for {pkg}: {exc}")


def bootstrap_orm_package(
    *,
    package_prefix: str,
    module_names: list[str],
    strict_imports: bool = False,
) -> bool:
    """Bootstrap a generated ORM package.

    Args:
        package_prefix: Root package name (usually __name__ from the package __init__.py).
        module_names: Fully qualified module names to import (e.g. `pkg.models.user`).
        strict_imports: When True, raise on import or rebuild errors.
    """
    # Avoid circular imports when ORM imports ontology primitives.
    from aware_orm.models.orm_model import ORMModel
    from aware_orm.registry import ORMModelRegistry

    # Preserve the renderer-provided import order.
    #
    # Sorting here is dangerous because it can flip a working import order into a
    # circular-import failure (some ontology modules intentionally rely on ordering).
    seen: set[str] = set()
    ordered: list[str] = []
    for m in module_names:
        if m in seen:
            continue
        ordered.append(m)
        seen.add(m)
    module_names = ordered

    had_errors = False
    imported_modules: list[object] = []
    for mod in module_names:
        try:
            imported_modules.append(import_module(mod))
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            had_errors = True
            logger.critical(f"Package bootstrap: failed to import {mod}: {exc}")

    # Union of TYPE_CHECKING imports across the package.
    #
    # Why:
    # - Pydantic `model_rebuild` can recursively build schemas for nested models.
    # - When rebuilding model A, forward refs in model B may be evaluated with the
    #   `_types_namespace` passed to model A.
    # - Relying only on per-module TYPE_CHECKING imports can therefore miss symbols
    #   required by nested models, yielding undefined-annotation errors.
    #
    # Best-effort: failures are tolerated so bootstrap remains resilient.
    package_type_checking_ns: dict[str, object] = {}
    for module_obj in imported_modules:
        module_name = getattr(module_obj, "__name__", None)
        if not isinstance(module_name, str) or not module_name:
            continue
        try:
            for name, value in _get_type_checking_imports(module_name).items():
                if name and name not in package_type_checking_ns:
                    package_type_checking_ns[name] = value
        except Exception:
            continue

    # Collect local Pydantic models (including inline-value BaseModel classes).
    #
    # Canonical ontology packages may contain both:
    # - graph_ref classes (ORMModel)
    # - inline_value classes (BaseModel) and per-function IO models (BaseModel)
    #
    # The ORM bootstrap must rebuild *all* local Pydantic models so postponed annotations
    # resolve deterministically without requiring eager runtime imports.
    from pydantic import BaseModel as PydanticBaseModel  # noqa: WPS433

    local_pydantic_models: list[type[Any]] = []
    for module_obj in imported_modules:
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
            local_pydantic_models.append(value)

    # Phase A registration (without metaclass):
    # Discover ORMModel subclasses defined in the imported modules and register them by FQN.
    existing_fqns: dict[str, type[Any]] = {}
    try:
        existing_fqns = ORMModelRegistry.get_all_fqn_to_class()
        for module_obj in imported_modules:
            module_dict = getattr(module_obj, "__dict__", {})
            if not isinstance(module_dict, dict):
                continue
            for value in module_dict.values():
                if not isinstance(value, type):
                    continue
                if value is ORMModel:
                    continue
                try:
                    if not issubclass(value, ORMModel):
                        continue
                except Exception:
                    continue

                module_name = getattr(value, "__module__", "")
                if not module_name.startswith(package_prefix + "."):
                    continue

                fqn = ORMModelRegistry.get_fqn_for_class(value)
                existing_class = existing_fqns.get(fqn)
                if existing_class is value:
                    continue
                if existing_class is not None:
                    _discard_stale_registry_class(ORMModelRegistry, existing_class)
                ORMModelRegistry.register_class_stub(value)
                setattr(value, "_registry_key", fqn)
                existing_fqns[fqn] = value
    except Exception as exc:
        if strict_imports:  # pragma: no cover
            raise
        had_errors = True
        logger.critical(f"Package bootstrap: ORMModelRegistry unavailable: {exc}")
        return False

    # Build a shared types namespace so Pydantic can resolve forward references.
    #
    # IMPORTANT:
    # - Generated ontology packages use postponed annotations + TYPE_CHECKING imports,
    #   so referenced classes must exist in `_types_namespace` at rebuild time.
    # - Cross-package refs must work without requiring generated packages to re-export
    #   dependency symbols.
    #
    # Strategy:
    # - Prefer local package classes on name collisions.
    # - Then include cross-package classes (dependency packages).
    types_ns: dict[str, object] = {
        # Ensure builtin container generics resolve to builtin types even when a model
        # class defines a method with the same name (e.g. `Terminal.list`).
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "frozenset": frozenset,
    }

    # Prefer local package classes on name collisions.
    for _fqn, model_class in existing_fqns.items():
        module = getattr(model_class, "__module__", "")
        if not module.startswith(package_prefix + "."):
            continue
        name = getattr(model_class, "__name__", None)
        if name and name not in types_ns:
            types_ns[name] = model_class

    # Also include local non-ORM Pydantic models (inline_value + function IO).
    for model_class in local_pydantic_models:
        name = getattr(model_class, "__name__", None)
        if name and name not in types_ns:
            types_ns[name] = model_class

    for _fqn, model_class in existing_fqns.items():
        module = getattr(model_class, "__module__", "")
        if module.startswith(package_prefix + "."):
            continue
        name = getattr(model_class, "__name__", None)
        if name and name not in types_ns:
            types_ns[name] = model_class

    # Finally, include TYPE_CHECKING imports union across all imported modules.
    # Keep existing entries as the authoritative mapping (local classes first).
    for name, value in package_type_checking_ns.items():
        if name and name not in types_ns:
            types_ns[name] = value

    # Best-effort: include already-imported ORMModel subclasses even if they are not
    # currently registered in ORMModelRegistry (e.g. tests that temporarily clear the
    # registry while ontology packages remain imported).
    #
    # This keeps `model_rebuild` stable when a dependency package was bootstrapped
    # earlier in the process and then the registry was cleared afterward.
    try:

        def _walk_subclasses(cls: type[Any]) -> list[type[Any]]:
            out: list[type[Any]] = []
            for sub in cls.__subclasses__():
                out.append(sub)
                out.extend(_walk_subclasses(sub))
            return out

        for loaded in _walk_subclasses(ORMModel):
            if loaded is ORMModel:
                continue
            module = getattr(loaded, "__module__", "")
            if not isinstance(module, str) or not module:
                continue
            # Prefer Aware-owned packages; keep the namespace tight.
            if not module.startswith("aware_"):
                continue
            name = getattr(loaded, "__name__", None)
            if name and name not in types_ns:
                types_ns[name] = loaded
    except Exception:
        # Best-effort: if introspection fails, fall back to registry-only behavior.
        pass

    def _rebuild_ns_for_model(model_class: type[Any]) -> dict[str, object]:
        """
        Build the namespace used for `model_rebuild`.

        Start from the defining module globals (to include imported enums/constants),
        then overlay the synthesized `types_ns` (builtins + models).
        """
        module_name = getattr(model_class, "__module__", "")
        module_ns: dict[str, object] = {}
        try:
            module_obj = import_module(module_name)
            module_dict = getattr(module_obj, "__dict__", {})
            if isinstance(module_dict, dict):
                module_ns = module_dict
        except Exception:
            module_ns = {}

        ns = dict(module_ns)
        ns.update(types_ns)
        try:
            ns.update(_get_type_checking_imports(module_name))
        except Exception:
            # Best-effort: missing TYPE_CHECKING imports should not crash bootstrap.
            pass
        return ns

    local_models: list[type[Any]] = [
        model_class
        for model_class in existing_fqns.values()
        if getattr(model_class, "__module__", "").startswith(package_prefix + ".")
    ]
    local_models = sorted(
        local_models,
        key=lambda c: (getattr(c, "__module__", ""), getattr(c, "__name__", "")),
    )

    for model_class in local_models:
        shadow: dict[str, object] = {}
        try:
            rebuild_ns = _rebuild_ns_for_model(model_class)

            # Pydantic evaluates postponed annotations with a `localns` that includes the
            # class namespace. If a model defines methods named like builtin generics
            # (e.g. `Terminal.list`), those methods shadow builtin `list` during eval,
            # causing: TypeError: 'function' object is not subscriptable.
            #
            # Workaround: temporarily shadow those method names with the builtin types
            # just for `model_rebuild`, then restore.
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
                # Only shadow callables (methods) — do not touch class attributes/types.
                if callable(v) and not isinstance(v, type):
                    shadow[name] = v
                    setattr(model_class, name, builtin_type)

            model_class.model_rebuild(_types_namespace=rebuild_ns)
        except Exception as exc:
            if strict_imports:  # pragma: no cover
                raise
            had_errors = True
            logger.critical(
                "Package bootstrap: failed model_rebuild for "
                f"{getattr(model_class, '__module__', '<unknown>')}.{getattr(model_class, '__name__', '<unknown>')}: {exc}",
            )
        finally:
            for name, original in shadow.items():
                try:
                    setattr(model_class, name, original)
                except Exception:
                    # Best-effort restoration; if this fails, the model is already in a bad state.
                    pass

    # Rebuild non-ORM Pydantic models (inline_value + function IO models).
    #
    # NOTE: `bootstrap_orm_package` historically only rebuilt ORMModel subclasses,
    # but canonical packages can now embed inline_value types inside ontology packages.
    # These must be rebuilt too, otherwise Pydantic will raise
    # "class not fully defined" when validating nested payloads.
    local_value_models: list[type[Any]] = []
    seen: set[type[Any]] = set()
    for model_class in local_pydantic_models:
        if model_class in seen:
            continue
        seen.add(model_class)
        try:
            if issubclass(model_class, ORMModel):
                continue
        except Exception:
            continue
        local_value_models.append(model_class)

    local_value_models = sorted(
        local_value_models,
        key=lambda c: (getattr(c, "__module__", ""), getattr(c, "__name__", "")),
    )

    for model_class in local_value_models:
        shadow: dict[str, object] = {}
        try:
            rebuild_ns = _rebuild_ns_for_model(model_class)

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
            had_errors = True
            logger.critical(
                "Package bootstrap: failed model_rebuild for "
                f"{getattr(model_class, '__module__', '<unknown>')}.{getattr(model_class, '__name__', '<unknown>')}: {exc}",
            )
        finally:
            for name, original in shadow.items():
                try:
                    setattr(model_class, name, original)
                except Exception:
                    pass

    return not had_errors


__all__ = ["bootstrap_orm_package", "bootstrap_orm_package_from_artifacts"]
