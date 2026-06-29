from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .builder import SdkCompilePlan
from .compile import compile_sdk_workspace
from .features.contracts import (
    SdkOperationCatalogFeatureContext,
    SdkOperationCatalogFeaturePayloadUpdate,
)
from .features.registry import operation_catalog_feature_results
from .models import SdkConfigPlan, SdkOperationPlan, SdkSurfaceMethodPlan


SDK_OPERATION_CATALOG_CONTRACT = "aware.sdk_operation_catalog.v0"
SDK_OPERATION_CATALOG_SOURCE = "aware_sdk_runtime.sdk_compile_plan"
SDK_OPERATION_CATALOG_ARTIFACT_NAME = "sdk.operation_catalog.json"

_OPEN_OBJECT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": True,
}
_READ_OPERATION_PREFIXES = (
    "check_",
    "describe_",
    "fetch_",
    "find_",
    "get_",
    "inspect_",
    "list_",
    "load_",
    "read_",
    "resolve_",
    "select_",
    "status_",
    "validate_",
)
_STREAM_OPERATION_PREFIXES = (
    "stream_",
    "subscribe_",
    "watch_",
)


class SdkOperationCatalogMaterializationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogArtifact:
    path: Path
    relpath: str
    hash_sha256: str


def materialize_sdk_operation_catalog_from_toml(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    sdk_name: str | None = None,
) -> dict[str, object]:
    result = compile_sdk_workspace(
        toml_path=toml_path,
        repo_root=repo_root,
    )
    if result.compile_plan is None:
        message = (
            "SDK operation catalog materialization requires sdk_ontology "
            f"compilation mode: toml_path={toml_path!s}"
        )
        raise SdkOperationCatalogMaterializationError(message)
    return materialize_sdk_operation_catalog_from_compile_plan(
        plan=result.compile_plan,
        sdk_name=sdk_name,
        version_number=result.snapshot.spec.sdk.version_number,
    )


def materialize_sdk_operation_catalogs_from_compile_plan(
    *,
    plan: SdkCompilePlan,
    version_number: int | None = None,
) -> tuple[dict[str, object], ...]:
    return tuple(
        _catalog_payload(
            plan=plan,
            sdk_config=sdk_config,
            version_number=version_number,
        )
        for sdk_config in sorted(plan.sdk_configs, key=lambda item: item.name)
    )


def materialize_sdk_operation_catalog_from_compile_plan(
    *,
    plan: SdkCompilePlan,
    sdk_name: str | None = None,
    version_number: int | None = None,
) -> dict[str, object]:
    catalogs = materialize_sdk_operation_catalogs_from_compile_plan(
        plan=plan,
        version_number=version_number,
    )
    if sdk_name is None:
        if len(catalogs) != 1:
            discovered = ", ".join(str(item["sdk_name"]) for item in catalogs)
            message = (
                "SDK operation catalog materialization requires sdk_name when "
                f"the compile plan declares multiple SDK configs: {discovered}"
            )
            raise SdkOperationCatalogMaterializationError(message)
        return catalogs[0]

    normalized_sdk_name = _required_text(sdk_name, label="sdk_name")
    for catalog in catalogs:
        if str(catalog["sdk_name"]) == normalized_sdk_name:
            return catalog
    discovered = ", ".join(str(item["sdk_name"]) for item in catalogs)
    message = (
        "SDK operation catalog materialization could not find SDK config "
        f"{normalized_sdk_name!r}. Discovered: {discovered}"
    )
    raise SdkOperationCatalogMaterializationError(message)


def emit_sdk_operation_catalog_artifact(
    *,
    catalog_payload: dict[str, object],
    runtime_package_dir: Path,
    repo_root: Path,
) -> SdkOperationCatalogArtifact:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    canonical = json.dumps(
        catalog_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()
    artifact_path = (
        runtime_package_dir / SDK_OPERATION_CATALOG_ARTIFACT_NAME
    ).resolve()
    _ = artifact_path.write_text(
        json.dumps(catalog_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return SdkOperationCatalogArtifact(
        path=artifact_path,
        relpath=artifact_path.relative_to(repo_root).as_posix(),
        hash_sha256=digest,
    )


def _catalog_payload(
    *,
    plan: SdkCompilePlan,
    sdk_config: SdkConfigPlan,
    version_number: int | None,
) -> dict[str, object]:
    sdk_name = _required_text(sdk_config.name, label="sdk_config.name")
    surface_methods_by_operation_ref = _surface_methods_by_operation_ref(
        sdk_name=sdk_name,
        sdk_config=sdk_config,
    )
    operations = [
        _operation_payload(
            sdk_name=sdk_name,
            operation=operation,
            surface_methods_by_operation_ref=surface_methods_by_operation_ref,
        )
        for operation in sorted(sdk_config.operations, key=lambda item: item.name)
    ]
    surfaces = [
        _surface_payload(
            sdk_name=sdk_name,
            surface_name=surface.name,
            description=surface.description,
            methods=surface.methods,
        )
        for surface in sorted(sdk_config.surfaces, key=lambda item: item.name)
    ]
    catalog_payload: dict[str, object] = {
        "catalog_contract": SDK_OPERATION_CATALOG_CONTRACT,
        "catalog_source": SDK_OPERATION_CATALOG_SOURCE,
        "schema_version": 1,
        "sdk_name": sdk_name,
        "package_name": _required_text(plan.package_name, label="package_name"),
        "version_number": version_number,
        "fqn_prefix": plan.fqn_prefix,
        "source_files": list(plan.source_files),
        "sdk_source_path": sdk_config.source_path,
        "description": sdk_config.description,
        "surfaces": surfaces,
        "operations": operations,
    }
    return _apply_catalog_features(
        plan=plan,
        sdk_config=sdk_config,
        catalog_payload=catalog_payload,
    )


def _apply_catalog_features(
    *,
    plan: SdkCompilePlan,
    sdk_config: SdkConfigPlan,
    catalog_payload: dict[str, object],
) -> dict[str, object]:
    context = SdkOperationCatalogFeatureContext(
        plan=plan,
        sdk_config=sdk_config,
        catalog_payload=catalog_payload,
    )
    for result in operation_catalog_feature_results(context):
        _merge_feature_fields(
            target=catalog_payload,
            fields=result.catalog_fields,
            target_ref=f"{sdk_config.name}.catalog",
            feature_key=result.feature_key,
        )
        _apply_payload_updates(
            updates=result.operation_fields,
            payloads_by_ref=_payloads_by_ref(
                catalog_payload.get("operations"),
                ref_key="operation_ref",
            ),
            feature_key=result.feature_key,
        )
        _apply_payload_updates(
            updates=result.surface_fields,
            payloads_by_ref=_payloads_by_ref(
                catalog_payload.get("surfaces"),
                ref_key="surface_ref",
            ),
            feature_key=result.feature_key,
        )
        _apply_payload_updates(
            updates=result.surface_method_fields,
            payloads_by_ref=_surface_method_payloads_by_ref(catalog_payload),
            feature_key=result.feature_key,
        )
    return catalog_payload


def _apply_payload_updates(
    *,
    updates: tuple[SdkOperationCatalogFeaturePayloadUpdate, ...],
    payloads_by_ref: dict[str, tuple[dict[str, object], ...]],
    feature_key: str,
) -> None:
    for update in updates:
        payloads = payloads_by_ref.get(update.target_ref)
        if payloads is None:
            message = (
                f"SDK catalog feature {feature_key!r} targeted unknown payload "
                f"{update.target_ref!r}."
            )
            raise SdkOperationCatalogMaterializationError(message)
        for payload in payloads:
            _merge_feature_fields(
                target=payload,
                fields=update.fields,
                target_ref=update.target_ref,
                feature_key=feature_key,
            )


def _payloads_by_ref(
    value: object,
    *,
    ref_key: str,
) -> dict[str, tuple[dict[str, object], ...]]:
    indexed: dict[str, list[dict[str, object]]] = {}
    for payload in _dict_sequence(value):
        ref = str(payload.get(ref_key) or "").strip()
        if ref:
            indexed.setdefault(ref, []).append(payload)
    return {key: tuple(values) for key, values in indexed.items()}


def _surface_method_payloads_by_ref(
    catalog_payload: Mapping[str, object],
) -> dict[str, tuple[dict[str, object], ...]]:
    indexed: dict[str, list[dict[str, object]]] = {}
    for operation in _dict_sequence(catalog_payload.get("operations")):
        for method in _dict_sequence(operation.get("surface_methods")):
            ref = str(method.get("method_ref") or "").strip()
            if ref:
                indexed.setdefault(ref, []).append(method)
    for surface in _dict_sequence(catalog_payload.get("surfaces")):
        for method in _dict_sequence(surface.get("methods")):
            ref = str(method.get("method_ref") or "").strip()
            if ref:
                indexed.setdefault(ref, []).append(method)
    return {key: tuple(values) for key, values in indexed.items()}


def _dict_sequence(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _merge_feature_fields(
    *,
    target: dict[str, object],
    fields: Mapping[str, object],
    target_ref: str,
    feature_key: str,
) -> None:
    for key, value in fields.items():
        if key == "catalog_features" and key in target:
            target[key] = (*_object_sequence(target[key]), *_object_sequence(value))
            continue
        if key == "feature_contracts" and key in target:
            target[key] = _merged_mapping(
                existing=target[key],
                incoming=value,
                target_ref=target_ref,
                feature_key=feature_key,
            )
            continue
        if key in target and target[key] != value:
            message = (
                f"SDK catalog feature {feature_key!r} cannot overwrite field "
                f"{key!r} on {target_ref!r}."
            )
            raise SdkOperationCatalogMaterializationError(message)
        target[key] = value


def _object_sequence(value: object) -> tuple[object, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return (value,)
    return tuple(value)


def _merged_mapping(
    *,
    existing: object,
    incoming: object,
    target_ref: str,
    feature_key: str,
) -> dict[str, object]:
    if not isinstance(existing, Mapping) or not isinstance(incoming, Mapping):
        message = (
            f"SDK catalog feature {feature_key!r} cannot merge non-mapping "
            f"feature_contracts on {target_ref!r}."
        )
        raise SdkOperationCatalogMaterializationError(message)
    merged = dict(existing)
    for key, value in incoming.items():
        text_key = str(key)
        if text_key in merged and merged[text_key] != value:
            message = (
                f"SDK catalog feature {feature_key!r} cannot overwrite "
                f"feature_contracts[{text_key!r}] on {target_ref!r}."
            )
            raise SdkOperationCatalogMaterializationError(message)
        merged[text_key] = value
    return merged


def _operation_payload(
    *,
    sdk_name: str,
    operation: SdkOperationPlan,
    surface_methods_by_operation_ref: dict[str, tuple[SdkSurfaceMethodPlan, ...]],
) -> dict[str, object]:
    operation_name = _required_text(operation.name, label="operation.name")
    operation_ref = f"{sdk_name}.{operation_name}"
    surface_methods = surface_methods_by_operation_ref.get(operation_ref, ())
    policy = _operation_policy(
        operation_name=operation_name,
        operation_ref=operation_ref,
        surface_methods=surface_methods,
    )
    endpoints = sorted(
        operation.api_endpoints,
        key=lambda item: (item.order, item.endpoint_ref),
    )
    dependencies = sorted(
        operation.sdk_operation_dependencies,
        key=lambda item: (item.order, item.target_operation_ref),
    )
    return {
        "operation_ref": operation_ref,
        "sdk_name": sdk_name,
        "operation_name": operation_name,
        "title": _title_from_operation_name(operation_name),
        "description": operation.description,
        "source_path": operation.source_path,
        "endpoint_refs": [endpoint.endpoint_ref for endpoint in endpoints],
        "endpoint_details": [
            {
                "name": endpoint.name,
                "endpoint_ref": endpoint.endpoint_ref,
                "api_ref": endpoint.api_ref,
                "capability_name": endpoint.capability_name,
                "source_path": endpoint.source_path,
                "order": endpoint.order,
                "role": endpoint.role,
                "required": endpoint.required,
                "description": endpoint.description,
            }
            for endpoint in endpoints
        ],
        "surface_refs": [
            f"{sdk_name}.{method.surface_name}" for method in surface_methods
        ],
        "surface_methods": [
            _surface_method_payload(sdk_name=sdk_name, method=method)
            for method in surface_methods
        ],
        "method_family": policy["method_family"],
        "sdk_operation_dependency_refs": [
            dependency.target_operation_ref for dependency in dependencies
        ],
        "sdk_operation_dependencies": [
            {
                "target_operation_ref": dependency.target_operation_ref,
                "target_sdk_name": dependency.target_sdk_name,
                "target_operation_name": dependency.target_operation_name,
                "target_package_name": dependency.target_package_name,
                "source_path": dependency.source_path,
                "order": dependency.order,
                "role": dependency.role,
                "required": dependency.required,
                "description": dependency.description,
            }
            for dependency in dependencies
        ],
        "input_schema": dict(_OPEN_OBJECT_SCHEMA),
        "context_schema": dict(_OPEN_OBJECT_SCHEMA),
        "effect": policy["effect"],
        "effect_source": policy["effect_source"],
        "mutation_scope": policy["mutation_scope"],
        "confirmation_policy": policy["confirmation_policy"],
        "execution_mode": policy["execution_mode"],
        "runtime_binding_kind": policy["runtime_binding_kind"],
        "stability": "canonical",
        "handler_ref": None,
        "requires_confirmation": policy["requires_confirmation"],
    }


def _surface_methods_by_operation_ref(
    *,
    sdk_name: str,
    sdk_config: SdkConfigPlan,
) -> dict[str, tuple[SdkSurfaceMethodPlan, ...]]:
    indexed: dict[str, list[SdkSurfaceMethodPlan]] = {}
    for surface in sdk_config.surfaces:
        for method in surface.methods:
            operation_ref = method.operation_ref
            if "." not in operation_ref:
                operation_ref = f"{sdk_name}.{operation_ref}"
            indexed.setdefault(operation_ref, []).append(method)
    return {
        key: tuple(sorted(value, key=lambda item: (item.surface_name, item.name)))
        for key, value in indexed.items()
    }


def _surface_payload(
    *,
    sdk_name: str,
    surface_name: str,
    description: str | None,
    methods: tuple[SdkSurfaceMethodPlan, ...],
) -> dict[str, object]:
    return {
        "surface_ref": f"{sdk_name}.{surface_name}",
        "sdk_name": sdk_name,
        "surface_name": surface_name,
        "description": description,
        "methods": [
            _surface_method_payload(sdk_name=sdk_name, method=method)
            for method in sorted(methods, key=lambda item: item.name)
        ],
    }


def _surface_method_payload(
    *,
    sdk_name: str,
    method: SdkSurfaceMethodPlan,
) -> dict[str, object]:
    surface_ref = f"{sdk_name}.{method.surface_name}"
    return {
        "method_ref": f"{surface_ref}.{method.name}",
        "surface_ref": surface_ref,
        "sdk_name": sdk_name,
        "surface_name": method.surface_name,
        "method_name": method.name,
        "operation_ref": method.operation_ref,
        "operation_name": method.operation_name,
        "method_family": method.method_family,
        "effect": method.effect,
        "mutation_scope": method.mutation_scope,
        "confirmation_policy": method.confirmation_policy,
        "execution_mode": method.execution_mode,
        "runtime_binding_kind": method.runtime_binding_kind,
        "source_path": method.source_path,
        "description": method.description,
    }


def _operation_policy(
    *,
    operation_name: str,
    operation_ref: str,
    surface_methods: tuple[SdkSurfaceMethodPlan, ...],
) -> dict[str, object]:
    if not surface_methods:
        effect = _infer_operation_effect(operation_name)
        return {
            "method_family": None,
            "effect": effect,
            "effect_source": "inferred_operation_name",
            "mutation_scope": "unknown" if effect != "read" else "none",
            "confirmation_policy": "none" if effect == "read" else "required",
            "execution_mode": "stream" if effect == "stream" else "request_response",
            "runtime_binding_kind": "unbound",
            "requires_confirmation": effect != "read",
        }
    return {
        "method_family": _consistent_optional_value(
            operation_ref=operation_ref,
            field_name="method_family",
            values=tuple(method.method_family for method in surface_methods),
        ),
        "effect": _consistent_optional_value(
            operation_ref=operation_ref,
            field_name="effect",
            values=tuple(method.effect for method in surface_methods),
        ),
        "effect_source": "sdk_surface_method",
        "mutation_scope": _consistent_optional_value(
            operation_ref=operation_ref,
            field_name="mutation_scope",
            values=tuple(method.mutation_scope for method in surface_methods),
        ),
        "confirmation_policy": _consistent_optional_value(
            operation_ref=operation_ref,
            field_name="confirmation_policy",
            values=tuple(method.confirmation_policy for method in surface_methods),
        ),
        "execution_mode": _consistent_optional_value(
            operation_ref=operation_ref,
            field_name="execution_mode",
            values=tuple(method.execution_mode for method in surface_methods),
        ),
        "runtime_binding_kind": _consistent_optional_value(
            operation_ref=operation_ref,
            field_name="runtime_binding_kind",
            values=tuple(method.runtime_binding_kind for method in surface_methods),
        ),
        "requires_confirmation": any(
            method.confirmation_policy == "required" for method in surface_methods
        ),
    }


def _consistent_optional_value(
    *,
    operation_ref: str,
    field_name: str,
    values: tuple[str, ...],
) -> str | None:
    unique_values = sorted({value for value in values if value})
    if not unique_values:
        return None
    if len(unique_values) == 1:
        return unique_values[0]
    message = (
        f"SDK operation {operation_ref!r} has conflicting surface method "
        f"{field_name} values: {unique_values}"
    )
    raise SdkOperationCatalogMaterializationError(message)


def _infer_operation_effect(operation_name: str) -> str:
    lowered = operation_name.strip().casefold()
    if any(lowered.startswith(prefix) for prefix in _STREAM_OPERATION_PREFIXES):
        return "stream"
    if any(lowered.startswith(prefix) for prefix in _READ_OPERATION_PREFIXES):
        return "read"
    if lowered in {"status", "verify"}:
        return "read"
    return "write"


def _title_from_operation_name(operation_name: str) -> str:
    return " ".join(part.capitalize() for part in operation_name.split("_") if part)


def _required_text(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SdkOperationCatalogMaterializationError(f"SDK catalog {label} is empty.")
    return text


__all__ = [
    "SDK_OPERATION_CATALOG_ARTIFACT_NAME",
    "SDK_OPERATION_CATALOG_CONTRACT",
    "SDK_OPERATION_CATALOG_SOURCE",
    "SdkOperationCatalogArtifact",
    "SdkOperationCatalogMaterializationError",
    "emit_sdk_operation_catalog_artifact",
    "materialize_sdk_operation_catalog_from_compile_plan",
    "materialize_sdk_operation_catalog_from_toml",
    "materialize_sdk_operation_catalogs_from_compile_plan",
]
