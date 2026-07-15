"""Renderer-local Python import grouping.

Import ownership is render policy, not generic utility behavior.  Semantic package
groups must be provided by the renderer/materialization inputs; this module never
discovers package identity from repo files or import-name prefixes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
import sys


STANDARD_GROUP = "Standard"
THIRD_PARTY_GROUP = "Third-party"


@dataclass(frozen=True)
class PythonImportGroupingPolicy:
    """Explicit import grouping policy for one render invocation."""

    semantic_import_roots: Mapping[str, str] = field(default_factory=dict)
    support_import_roots: Mapping[str, str] = field(default_factory=dict)


def group_python_imports(
    imports: Mapping[str, set[str]],
    *,
    policy: PythonImportGroupingPolicy | None = None,
) -> dict[str, dict[str, set[str]]]:
    """Group imports using standard-library knowledge and explicit semantic roots."""

    grouping_policy = policy or PythonImportGroupingPolicy()
    semantic_roots = {
        _module_root(root): _clean_label(label)
        for root, label in grouping_policy.semantic_import_roots.items()
        if _module_root(root) and _clean_label(label)
    }
    support_roots = {
        _module_root(root): _clean_label(label)
        for root, label in grouping_policy.support_import_roots.items()
        if _module_root(root) and _clean_label(label)
    }

    groups: dict[str, dict[str, set[str]]] = {}
    for module, items in imports.items():
        if not module:
            continue
        module_root = _module_root(module)
        if _is_standard_module(module):
            group_name = STANDARD_GROUP
        elif module_root in support_roots:
            group_name = support_roots[module_root]
        elif module_root in semantic_roots:
            group_name = semantic_roots[module_root]
        else:
            group_name = THIRD_PARTY_GROUP

        groups.setdefault(group_name, {}).setdefault(module, set()).update(items)

    ordered: dict[str, dict[str, set[str]]] = {}
    for group_name in (STANDARD_GROUP, THIRD_PARTY_GROUP):
        if group_name in groups:
            ordered[group_name] = groups[group_name]
    for group_name in sorted(name for name in groups if name not in ordered):
        ordered[group_name] = groups[group_name]
    return {group_name: modules for group_name, modules in ordered.items() if modules}


def semantic_import_roots_from_renderer_inputs(
    *,
    import_root: str | None = None,
    import_overrides: Mapping[str, str] | None = None,
    external_graph_fqn_prefixes: Iterable[str | None] = (),
) -> dict[str, str]:
    """Build semantic import-root labels from explicit renderer inputs."""

    roots: dict[str, str] = {}
    _add_semantic_root(roots, import_root)
    for module in (import_overrides or {}).values():
        _add_semantic_root(roots, module)
    for fqn_prefix in external_graph_fqn_prefixes:
        _add_semantic_root(roots, fqn_prefix)
    return roots


def _add_semantic_root(roots: dict[str, str], value: str | None) -> None:
    root = _module_root(value or "")
    if root:
        roots.setdefault(root, _label_from_import_root(root))


def _module_root(module: str) -> str:
    return module.strip().split(".", 1)[0]


def _is_standard_module(module: str) -> bool:
    root = _module_root(module)
    return module in sys.stdlib_module_names or root in sys.stdlib_module_names


def _label_from_import_root(root: str) -> str:
    return public_label_from_import_root(root)


def public_label_from_import_root(root: str) -> str:
    public_root = root.removeprefix("aware_")
    return public_root.replace("-", "_").replace("_", " ").title()


def _clean_label(label: str) -> str:
    return " ".join(label.replace("_", " ").split())


__all__ = [
    "PythonImportGroupingPolicy",
    "group_python_imports",
    "public_label_from_import_root",
    "semantic_import_roots_from_renderer_inputs",
]
