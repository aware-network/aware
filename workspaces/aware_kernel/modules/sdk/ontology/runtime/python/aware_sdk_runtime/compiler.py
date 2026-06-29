from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import cast

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from .models import (
    SdkApiOwnership,
    SdkOperationDependencyOwnership,
    SdkOperationEndpointOwnership,
    SdkOperationOwnership,
    SdkSurfaceMethodOwnership,
    SdkSurfaceOwnership,
    SdkOwnership,
)

_METHOD_FAMILIES = frozenset(
    {
        "create",
        "retrieve",
        "list",
        "update",
        "delete",
        "ensure",
        "resolve",
        "invoke",
    }
)
_EFFECTS = frozenset({"read", "write", "stream"})
_CONFIRMATION_POLICIES = frozenset({"none", "required"})
_EXECUTION_MODES = frozenset({"request_response", "stream", "background"})
_RUNTIME_BINDING_KINDS = frozenset(
    {"unbound", "local_handler", "api_client", "composed"}
)


def load_sdk_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    sdk_dependency_package_names_by_sdk_ref: Mapping[str, str] | None = None,
) -> tuple[SdkOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    sdks_by_name: dict[str, SdkOwnership] = {}
    dependency_package_names_by_sdk_ref = {
        key.casefold(): value
        for key, value in (sdk_dependency_package_names_by_sdk_ref or {}).items()
    }

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="sdk source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        if tree.root_node.has_error:
            raise ValueError(f"SDK source {source_path} has parse errors")

        for node in tree.root_node.named_children:
            if node.type != "sdk_def":
                continue
            sdk_name = _symbol_key(_field_text(node, "name"))
            if not sdk_name:
                raise ValueError(f"SDK declaration has empty name in {source_path}")
            if sdk_name in sdks_by_name:
                raise ValueError(
                    f"Duplicate SDK declaration {sdk_name!r} across SDK sources"
                )

            apis_by_ref: dict[str, SdkApiOwnership] = {}
            operations_by_name: dict[str, SdkOperationOwnership] = {}
            surfaces_by_name: dict[str, SdkSurfaceOwnership] = {}
            description = _first_literal_text(node)

            for child in _iter_sdk_children(node=node):
                if child.type == "sdk_api_decl":
                    api_ref = _qualified_text(child.child_by_field_name("api"))
                    if not api_ref:
                        raise ValueError(
                            f"SDK declaration {sdk_name!r} has api declaration with empty target in {source_path}"
                        )
                    api_key = api_ref.casefold()
                    if api_key in apis_by_ref:
                        raise ValueError(
                            f"SDK declaration {sdk_name!r} has duplicate api binding {api_ref!r} in {source_path}"
                        )
                    apis_by_ref[api_key] = SdkApiOwnership(
                        api_ref=api_ref, source_path=source_rel
                    )
                    continue

                if child.type != "sdk_operation_def":
                    if child.type == "sdk_surface_def":
                        surface = _load_sdk_surface_definition(
                            node=child,
                            sdk_name=sdk_name,
                            source_path=source_path,
                            source_rel=source_rel,
                        )
                        surface_key = surface.name.casefold()
                        if surface_key in surfaces_by_name:
                            message = f"SDK declaration {sdk_name!r} has duplicate surface {surface.name!r} in {source_path}"
                            raise ValueError(message)
                        surfaces_by_name[surface_key] = surface
                    continue
                operation = _load_sdk_operation_definition(
                    node=child,
                    sdk_name=sdk_name,
                    source_path=source_path,
                    source_rel=source_rel,
                    declared_api_refs=tuple(
                        api.api_ref for api in apis_by_ref.values()
                    ),
                )
                operation_key = operation.name.casefold()
                if operation_key in operations_by_name:
                    raise ValueError(
                        f"SDK declaration {sdk_name!r} has duplicate operation {operation.name!r} in {source_path}"
                    )
                operations_by_name[operation_key] = operation

            if not apis_by_ref:
                raise ValueError(
                    f"SDK declaration {sdk_name!r} must include at least one api in {source_path}"
                )
            if not operations_by_name:
                raise ValueError(
                    f"SDK declaration {sdk_name!r} must include at least one operation in {source_path}"
                )
            _validate_sdk_surfaces(
                sdk_name=sdk_name,
                operations_by_name=operations_by_name,
                surfaces=tuple(surfaces_by_name.values()),
                source_path=source_path,
            )
            _validate_sdk_operation_dependencies(
                sdk_name=sdk_name,
                operations=tuple(operations_by_name.values()),
                sdk_dependency_package_names_by_sdk_ref=(
                    dependency_package_names_by_sdk_ref
                ),
                source_path=source_path,
            )

            sdks_by_name[sdk_name] = SdkOwnership(
                name=sdk_name,
                source_path=source_rel,
                apis=tuple(
                    sorted(
                        apis_by_ref.values(),
                        key=lambda item: (item.api_ref, item.source_path),
                    )
                ),
                operations=tuple(
                    sorted(
                        operations_by_name.values(),
                        key=lambda item: (item.name, item.source_path),
                    )
                ),
                surfaces=tuple(
                    sorted(
                        surfaces_by_name.values(),
                        key=lambda item: (item.name, item.source_path),
                    )
                ),
                description=description,
            )

    return tuple(
        sorted(sdks_by_name.values(), key=lambda item: (item.name, item.source_path))
    )


def _load_sdk_operation_definition(
    *,
    node: Node,
    sdk_name: str,
    source_path: Path,
    source_rel: str,
    declared_api_refs: tuple[str, ...],
) -> SdkOperationOwnership:
    operation_name = _symbol_key(_field_text(node, "operation_name"))
    if not operation_name:
        raise ValueError(
            f"SDK declaration {sdk_name!r} has operation with empty name in {source_path}"
        )

    endpoints_by_ref: dict[str, SdkOperationEndpointOwnership] = {}
    operation_dependencies_by_ref: dict[str, SdkOperationDependencyOwnership] = {}
    for child in _iter_operation_children(node=node):
        if child.type == "sdk_operation_dependency_def":
            target_operation_ref = _qualified_text(
                child.child_by_field_name("operation")
            )
            target_sdk_name, target_operation_name = _parse_sdk_operation_ref(
                target_operation_ref=target_operation_ref,
                sdk_name=sdk_name,
                operation_name=operation_name,
                source_path=source_path,
            )
            dependency_key = target_operation_ref.casefold()
            if dependency_key in operation_dependencies_by_ref:
                raise ValueError(
                    f"SDK declaration {sdk_name!r} operation {operation_name!r} "
                    + "has duplicate SDK operation dependency "
                    + f"{target_operation_ref!r} in {source_path}"
                )
            operation_dependencies_by_ref[dependency_key] = (
                SdkOperationDependencyOwnership(
                    target_operation_ref=target_operation_ref,
                    target_sdk_name=target_sdk_name,
                    target_operation_name=target_operation_name,
                    source_path=source_rel,
                    description=_first_literal_text(child),
                )
            )
            continue

        if child.type != "sdk_operation_endpoint_def":
            continue
        endpoint_ref = _qualified_text(child.child_by_field_name("endpoint"))
        if len(endpoint_ref.split(".")) < 3:
            raise ValueError(
                f"SDK declaration {sdk_name!r} operation {operation_name!r} has invalid endpoint ref "
                + f"{endpoint_ref!r} in {source_path}; expected api.capability.endpoint"
            )
        if (
            _resolve_declared_api_ref(
                endpoint_ref=endpoint_ref, declared_api_refs=declared_api_refs
            )
            is None
        ):
            raise ValueError(
                f"SDK declaration {sdk_name!r} operation {operation_name!r} references undeclared api endpoint "
                + f"{endpoint_ref!r} in {source_path}"
            )
        endpoint_key = endpoint_ref.casefold()
        if endpoint_key in endpoints_by_ref:
            raise ValueError(
                f"SDK declaration {sdk_name!r} operation {operation_name!r} has duplicate endpoint "
                + f"{endpoint_ref!r} in {source_path}"
            )
        endpoints_by_ref[endpoint_key] = SdkOperationEndpointOwnership(
            endpoint_ref=endpoint_ref,
            source_path=source_rel,
            description=_first_literal_text(child),
        )

    if not endpoints_by_ref and not operation_dependencies_by_ref:
        raise ValueError(
            f"SDK declaration {sdk_name!r} operation {operation_name!r} must "
            + f"include at least one endpoint or operation dependency in {source_path}"
        )
    return SdkOperationOwnership(
        name=operation_name,
        source_path=source_rel,
        endpoints=tuple(
            sorted(
                endpoints_by_ref.values(),
                key=lambda item: (item.endpoint_ref, item.source_path),
            )
        ),
        operation_dependencies=tuple(
            sorted(
                operation_dependencies_by_ref.values(),
                key=lambda item: (item.target_operation_ref, item.source_path),
            )
        ),
        description=_first_literal_text(node),
    )


def _load_sdk_surface_definition(
    *,
    node: Node,
    sdk_name: str,
    source_path: Path,
    source_rel: str,
) -> SdkSurfaceOwnership:
    surface_name = _symbol_key(_field_text(node, "surface_name"))
    if not surface_name:
        raise ValueError(
            f"SDK declaration {sdk_name!r} has surface with empty name in {source_path}"
        )

    methods_by_name: dict[str, SdkSurfaceMethodOwnership] = {}
    for child in _iter_surface_children(node=node):
        if child.type != "sdk_surface_method_def":
            continue
        method = _load_sdk_surface_method_definition(
            node=child,
            sdk_name=sdk_name,
            surface_name=surface_name,
            source_path=source_path,
            source_rel=source_rel,
        )
        method_key = method.name.casefold()
        if method_key in methods_by_name:
            message = f"SDK declaration {sdk_name!r} surface {surface_name!r} has duplicate method {method.name!r} in {source_path}"
            raise ValueError(message)
        methods_by_name[method_key] = method
    if not methods_by_name:
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} must include at least one method in {source_path}"
        raise ValueError(message)
    return SdkSurfaceOwnership(
        name=surface_name,
        source_path=source_rel,
        methods=tuple(
            sorted(
                methods_by_name.values(), key=lambda item: (item.name, item.source_path)
            )
        ),
        description=_first_literal_text(node),
    )


def _load_sdk_surface_method_definition(
    *,
    node: Node,
    sdk_name: str,
    surface_name: str,
    source_path: Path,
    source_rel: str,
) -> SdkSurfaceMethodOwnership:
    method_name = _symbol_key(_field_text(node, "method_name"))
    if not method_name:
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} has method with empty name in {source_path}"
        raise ValueError(message)

    operation_ref: str | None = None
    method_family: str | None = None
    effect: str | None = None
    mutation_scope: str | None = None
    confirmation_policy: str | None = None
    execution_mode: str | None = None
    runtime_binding_kind: str | None = None

    for child in _iter_surface_method_children(node=node):
        if child.type == "sdk_surface_method_operation_decl":
            operation_ref = _set_once(
                current=operation_ref,
                value=_qualified_text(child.child_by_field_name("operation")),
                field_name="operation",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )
            continue
        if child.type == "sdk_surface_method_family_decl":
            method_family = _set_once(
                current=method_family,
                value=_symbol_key(_field_text(child, "method_family")),
                field_name="method_family",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )
            continue
        if child.type == "sdk_surface_method_effect_decl":
            effect = _set_once(
                current=effect,
                value=_symbol_key(_field_text(child, "effect")),
                field_name="effect",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )
            continue
        if child.type == "sdk_surface_method_mutation_scope_decl":
            mutation_scope = _set_once(
                current=mutation_scope,
                value=_symbol_key(_field_text(child, "mutation_scope")),
                field_name="mutation_scope",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )
            continue
        if child.type == "sdk_surface_method_confirmation_policy_decl":
            confirmation_policy = _set_once(
                current=confirmation_policy,
                value=_symbol_key(_field_text(child, "confirmation_policy")),
                field_name="confirmation_policy",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )
            continue
        if child.type == "sdk_surface_method_execution_mode_decl":
            execution_mode = _set_once(
                current=execution_mode,
                value=_symbol_key(_field_text(child, "execution_mode")),
                field_name="execution_mode",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )
            continue
        if child.type == "sdk_surface_method_runtime_binding_kind_decl":
            runtime_binding_kind = _set_once(
                current=runtime_binding_kind,
                value=_symbol_key(_field_text(child, "runtime_binding_kind")),
                field_name="runtime_binding_kind",
                sdk_name=sdk_name,
                surface_name=surface_name,
                method_name=method_name,
                source_path=source_path,
            )

    if operation_ref is None:
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} method {method_name!r} must declare operation in {source_path}"
        raise ValueError(message)
    if method_family is None:
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} method {method_name!r} must declare method_family in {source_path}"
        raise ValueError(message)
    method_family = _validate_member(
        value=method_family,
        field_name="method_family",
        allowed=_METHOD_FAMILIES,
        sdk_name=sdk_name,
        surface_name=surface_name,
        method_name=method_name,
        source_path=source_path,
    )
    effect = _validate_member(
        value=effect or "read",
        field_name="effect",
        allowed=_EFFECTS,
        sdk_name=sdk_name,
        surface_name=surface_name,
        method_name=method_name,
        source_path=source_path,
    )
    confirmation_policy = _validate_member(
        value=confirmation_policy or ("none" if effect == "read" else "required"),
        field_name="confirmation_policy",
        allowed=_CONFIRMATION_POLICIES,
        sdk_name=sdk_name,
        surface_name=surface_name,
        method_name=method_name,
        source_path=source_path,
    )
    execution_mode = _validate_member(
        value=execution_mode
        or ("stream" if effect == "stream" else "request_response"),
        field_name="execution_mode",
        allowed=_EXECUTION_MODES,
        sdk_name=sdk_name,
        surface_name=surface_name,
        method_name=method_name,
        source_path=source_path,
    )
    runtime_binding_kind = _validate_member(
        value=runtime_binding_kind or "unbound",
        field_name="runtime_binding_kind",
        allowed=_RUNTIME_BINDING_KINDS,
        sdk_name=sdk_name,
        surface_name=surface_name,
        method_name=method_name,
        source_path=source_path,
    )
    target_sdk_name, target_operation_name = _parse_sdk_operation_ref(
        target_operation_ref=_normalize_sdk_operation_ref(
            sdk_name=sdk_name,
            operation_ref=operation_ref,
        ),
        sdk_name=sdk_name,
        operation_name=method_name,
        source_path=source_path,
    )
    if target_sdk_name.casefold() != sdk_name.casefold():
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} method {method_name!r} must target a local SDK operation in {source_path}; got {operation_ref!r}"
        raise ValueError(message)

    return SdkSurfaceMethodOwnership(
        name=method_name,
        surface_name=surface_name,
        source_path=source_rel,
        operation_ref=f"{target_sdk_name}.{target_operation_name}",
        operation_name=target_operation_name,
        method_family=method_family,
        effect=effect,
        mutation_scope=mutation_scope or "none",
        confirmation_policy=confirmation_policy,
        execution_mode=execution_mode,
        runtime_binding_kind=runtime_binding_kind,
        description=_first_literal_text(node),
    )


def _parse_sdk_operation_ref(
    *,
    target_operation_ref: str,
    sdk_name: str,
    operation_name: str,
    source_path: Path,
) -> tuple[str, str]:
    parts = [
        part.strip() for part in (target_operation_ref or "").split(".") if part.strip()
    ]
    if len(parts) != 2:
        raise ValueError(
            f"SDK declaration {sdk_name!r} operation {operation_name!r} has "
            + "invalid SDK operation dependency "
            + f"{target_operation_ref!r} in {source_path}; expected sdk.operation"
        )
    return parts[0], parts[1]


def _normalize_sdk_operation_ref(*, sdk_name: str, operation_ref: str) -> str:
    parts = [part.strip() for part in (operation_ref or "").split(".") if part.strip()]
    if len(parts) == 1:
        return f"{sdk_name}.{parts[0]}"
    return operation_ref


def _validate_sdk_surfaces(
    *,
    sdk_name: str,
    operations_by_name: Mapping[str, SdkOperationOwnership],
    surfaces: tuple[SdkSurfaceOwnership, ...],
    source_path: Path,
) -> None:
    operation_keys = set(operations_by_name)
    for surface in surfaces:
        for method in surface.methods:
            if method.operation_name.casefold() not in operation_keys:
                message = f"SDK declaration {sdk_name!r} surface {surface.name!r} method {method.name!r} references unknown local operation {method.operation_ref!r} in {source_path}"
                raise ValueError(message)


def _validate_sdk_operation_dependencies(
    *,
    sdk_name: str,
    operations: tuple[SdkOperationOwnership, ...],
    sdk_dependency_package_names_by_sdk_ref: Mapping[str, str],
    source_path: Path,
) -> None:
    operation_names_by_key = {
        operation.name.casefold(): operation.name for operation in operations
    }
    sdk_name_key = sdk_name.casefold()
    for operation in operations:
        for dependency in operation.operation_dependencies:
            target_sdk_key = dependency.target_sdk_name.casefold()
            target_operation_key = dependency.target_operation_name.casefold()
            if target_sdk_key == sdk_name_key:
                if target_operation_key == operation.name.casefold():
                    raise ValueError(
                        f"SDK declaration {sdk_name!r} operation {operation.name!r} "
                        + "cannot depend on itself in "
                        + f"{source_path}"
                    )
                if target_operation_key not in operation_names_by_key:
                    raise ValueError(
                        f"SDK declaration {sdk_name!r} operation {operation.name!r} "
                        + "references unknown local SDK operation dependency "
                        + f"{dependency.target_operation_ref!r} in {source_path}"
                    )
                continue
            if target_sdk_key not in sdk_dependency_package_names_by_sdk_ref:
                raise ValueError(
                    f"SDK declaration {sdk_name!r} operation {operation.name!r} "
                    + "references SDK operation dependency "
                    + f"{dependency.target_operation_ref!r} not declared in "
                    + "`aware.sdk.toml` sdk_package dependencies in "
                    + f"{source_path}"
                )


def _resolve_declared_api_ref(
    *, endpoint_ref: str, declared_api_refs: tuple[str, ...]
) -> str | None:
    matches = [
        api_ref
        for api_ref in declared_api_refs
        if endpoint_ref == api_ref or endpoint_ref.startswith(api_ref + ".")
    ]
    if not matches:
        return None
    return max(matches, key=len)


def _iter_sdk_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in {"sdk_api_decl", "sdk_operation_def", "sdk_surface_def"}:
            children.append(child)
            continue
        if child.type == "sdk_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _iter_surface_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type == "sdk_surface_method_def":
            children.append(child)
            continue
        if child.type in {"sdk_surface_block", "sdk_surface_item"}:
            children.extend(_iter_surface_children(node=child))
    return tuple(children)


def _iter_surface_method_children(*, node: Node) -> tuple[Node, ...]:
    item_types = {
        "sdk_surface_method_operation_decl",
        "sdk_surface_method_family_decl",
        "sdk_surface_method_effect_decl",
        "sdk_surface_method_mutation_scope_decl",
        "sdk_surface_method_confirmation_policy_decl",
        "sdk_surface_method_execution_mode_decl",
        "sdk_surface_method_runtime_binding_kind_decl",
    }
    children: list[Node] = []
    for child in node.named_children:
        if child.type in item_types:
            children.append(child)
            continue
        if child.type in {"sdk_surface_method_block", "sdk_surface_method_item"}:
            children.extend(_iter_surface_method_children(node=child))
    return tuple(children)


def _iter_operation_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in {
            "sdk_operation_endpoint_def",
            "sdk_operation_dependency_def",
        }:
            children.append(child)
            continue
        if child.type in {"sdk_operation_block", "sdk_operation_item"}:
            children.extend(_iter_operation_children(node=child))
    return tuple(children)


def _first_literal_text(node: Node) -> str | None:
    for child in node.named_children:
        if child.type in {"string_literal", "triple_string_literal"}:
            value = _decode_literal_text(child)
            if value:
                return value
            continue
        if child.type in {
            "sdk_operation_block",
            "sdk_surface_block",
            "sdk_surface_method_block",
        }:
            nested = _first_literal_text(child)
            if nested:
                return nested
    return None


def _decode_literal_text(node: Node) -> str | None:
    raw = _qualified_text(node)
    if not raw:
        return None
    if raw.startswith('"""') and raw.endswith('"""'):
        value = raw[3:-3].strip()
        return value or None
    try:
        value = cast(object, json.loads(raw))
    except json.JSONDecodeError:
        if raw.startswith('"') and raw.endswith('"'):
            value = raw[1:-1].strip()
            return value or None
        return raw.strip() or None
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _set_once(
    *,
    current: str | None,
    value: str,
    field_name: str,
    sdk_name: str,
    surface_name: str,
    method_name: str,
    source_path: Path,
) -> str:
    normalized = (value or "").strip()
    if not normalized:
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} method {method_name!r} has empty {field_name} in {source_path}"
        raise ValueError(message)
    if current is not None:
        message = f"SDK declaration {sdk_name!r} surface {surface_name!r} method {method_name!r} has duplicate {field_name} in {source_path}"
        raise ValueError(message)
    return normalized


def _validate_member(
    *,
    value: str,
    field_name: str,
    allowed: frozenset[str],
    sdk_name: str,
    surface_name: str,
    method_name: str,
    source_path: Path,
) -> str:
    normalized = (value or "").strip().casefold()
    if normalized in allowed:
        return normalized
    allowed_text = ", ".join(sorted(allowed))
    message = f"SDK declaration {sdk_name!r} surface {surface_name!r} method {method_name!r} has invalid {field_name} {value!r} in {source_path}; expected one of: {allowed_text}"
    raise ValueError(message)


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} path must stay within package root: {candidate_resolved}"
    )


__all__ = [
    "load_sdk_ownership_from_sources",
]
