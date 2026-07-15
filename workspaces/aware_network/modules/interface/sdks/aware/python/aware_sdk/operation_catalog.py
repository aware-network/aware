"""SDK operation catalog discovery for the aware-sdk CLI renderer."""

from __future__ import annotations

import importlib
import inspect
import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

SDK_OPERATION_CATALOG_CONTRACT = "aware.sdk_operation_catalog.v0"
SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP = "aware.sdk_operation_catalogs"

_BUILTIN_PROVIDER_REFS = (
    "aware_interface_sdk.operation_catalog:get_sdk_operation_catalog",
)


class SdkOperationCatalogError(RuntimeError):
    """Raised when an SDK operation catalog cannot be loaded or invoked."""


@dataclass(frozen=True, slots=True)
class SdkOperationDescriptor:
    """One explicit SDK-declared operation available to CLI renderers."""

    operation_ref: str
    title: str | None
    description: str | None
    endpoint_refs: tuple[str, ...]
    input_schema: Mapping[str, object]
    context_schema: Mapping[str, object]
    effect: str
    stability: str
    handler_ref: str | None
    requires_confirmation: bool

    @property
    def sdk_name(self) -> str:
        return _split_operation_ref(self.operation_ref)[0]

    @property
    def operation_name(self) -> str:
        return _split_operation_ref(self.operation_ref)[1]

    def summary_payload(self) -> dict[str, object]:
        return {
            "operation_ref": self.operation_ref,
            "sdk_name": self.sdk_name,
            "operation_name": self.operation_name,
            "title": self.title,
            "description": self.description,
            "endpoint_refs": list(self.endpoint_refs),
            "effect": self.effect,
            "stability": self.stability,
            "handler_ref": self.handler_ref,
            "requires_confirmation": self.requires_confirmation,
        }

    def detail_payload(self) -> dict[str, object]:
        return {
            **self.summary_payload(),
            "input_schema": dict(self.input_schema),
            "context_schema": dict(self.context_schema),
        }


@dataclass(frozen=True, slots=True)
class SdkOperationCatalog:
    """Operations published by one SDK package."""

    sdk_name: str
    package_name: str
    version_number: int | None
    provider_ref: str
    operations: tuple[SdkOperationDescriptor, ...]

    def summary_payload(self) -> dict[str, object]:
        return {
            "sdk_name": self.sdk_name,
            "package_name": self.package_name,
            "version_number": self.version_number,
            "provider_ref": self.provider_ref,
            "operation_count": len(self.operations),
        }


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogIndex:
    """Resolved operation catalog index keyed by operation ref."""

    catalogs: tuple[SdkOperationCatalog, ...]
    operations: tuple[SdkOperationDescriptor, ...]
    operation_by_ref: Mapping[str, SdkOperationDescriptor]

    def list_payload(self) -> dict[str, object]:
        return {
            "catalog_contract": SDK_OPERATION_CATALOG_CONTRACT,
            "catalog_count": len(self.catalogs),
            "operation_count": len(self.operations),
            "catalogs": [catalog.summary_payload() for catalog in self.catalogs],
            "operations": [
                operation.summary_payload() for operation in self.operations
            ],
        }

    def resolve(self, operation_ref: str) -> SdkOperationDescriptor:
        normalized = _normalize_operation_ref(operation_ref)
        operation = self.operation_by_ref.get(normalized)
        if operation is None:
            raise SdkOperationCatalogError(
                f"Unknown SDK operation_ref={operation_ref!r}."
            )
        return operation


def load_sdk_operation_catalog_index(
    *,
    extra_provider_refs: Iterable[str] = (),
    include_builtin_providers: bool = True,
) -> SdkOperationCatalogIndex:
    """Load catalogs from installed SDK providers and local bootstrap providers."""

    catalogs: list[SdkOperationCatalog] = []
    for provider_ref, raw_catalog in _load_entry_point_catalogs():
        catalogs.append(_catalog_from_payload(raw_catalog, provider_ref=provider_ref))

    existing_sdk_names = {catalog.sdk_name for catalog in catalogs}
    provider_refs: list[str] = []
    provider_refs.extend(_env_provider_refs())
    provider_refs.extend(extra_provider_refs)
    if include_builtin_providers:
        provider_refs.extend(_BUILTIN_PROVIDER_REFS)

    for provider_ref in provider_refs:
        catalog = _catalog_from_payload(
            _call_provider_ref(provider_ref),
            provider_ref=provider_ref,
        )
        if (
            catalog.sdk_name in existing_sdk_names
            and provider_ref in _BUILTIN_PROVIDER_REFS
        ):
            continue
        catalogs.append(catalog)
        existing_sdk_names.add(catalog.sdk_name)

    return _index_catalogs(catalogs)


async def invoke_sdk_operation(
    *,
    operation: SdkOperationDescriptor,
    request_payload: Mapping[str, object] | None = None,
    context: Mapping[str, object] | None = None,
    timeout_s: float | None = None,
    allow_mutation: bool = False,
) -> object:
    """Invoke one SDK-declared operation through its explicit handler ref."""

    if operation.effect != "read" and not allow_mutation:
        raise SdkOperationCatalogError(
            "SDK operation may mutate state; pass --allow-mutation to invoke: "
            + operation.operation_ref
        )
    if not operation.handler_ref:
        raise SdkOperationCatalogError(
            f"SDK operation has no CLI handler_ref: {operation.operation_ref}"
        )
    handler = _load_ref(operation.handler_ref)
    if not callable(handler):
        raise SdkOperationCatalogError(
            f"SDK operation handler is not callable: {operation.handler_ref}"
        )
    result = handler(
        operation_ref=operation.operation_ref,
        request_payload=dict(request_payload or {}),
        context=dict(context or {}),
        timeout_s=timeout_s,
    )
    if inspect.isawaitable(result):
        return await result
    return result


def parse_json_object(raw: str | None, *, label: str) -> dict[str, object]:
    if raw is None:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise SdkOperationCatalogError(f"{label} must decode to a JSON object.")
    return dict(parsed)


def path_context_value(path: Path | None) -> str | None:
    return str(path.expanduser().resolve()) if path is not None else None


def _index_catalogs(
    catalogs: Iterable[SdkOperationCatalog],
) -> SdkOperationCatalogIndex:
    catalog_tuple = tuple(sorted(catalogs, key=lambda item: item.sdk_name))
    operation_by_ref: dict[str, SdkOperationDescriptor] = {}
    for catalog in catalog_tuple:
        for operation in catalog.operations:
            if operation.sdk_name != catalog.sdk_name:
                raise SdkOperationCatalogError(
                    "SDK operation ref does not match catalog sdk_name: "
                    + f"{operation.operation_ref!r} under {catalog.sdk_name!r}"
                )
            normalized = _normalize_operation_ref(operation.operation_ref)
            if normalized in operation_by_ref:
                raise SdkOperationCatalogError(
                    f"Duplicate SDK operation_ref={operation.operation_ref!r}."
                )
            operation_by_ref[normalized] = operation
    operations = tuple(operation_by_ref[key] for key in sorted(operation_by_ref))
    return SdkOperationCatalogIndex(
        catalogs=catalog_tuple,
        operations=operations,
        operation_by_ref=operation_by_ref,
    )


def _load_entry_point_catalogs() -> tuple[tuple[str, object], ...]:
    loaded: list[tuple[str, object]] = []
    for entry_point in _entry_points():
        provider_ref = f"{entry_point.module}:{entry_point.attr}"
        loaded.append((provider_ref, entry_point.load()()))
    return tuple(loaded)


def _entry_points() -> tuple[metadata.EntryPoint, ...]:
    try:
        entry_points = metadata.entry_points(
            group=SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP
        )
    except TypeError:  # pragma: no cover - compatibility with older metadata API
        all_entry_points = metadata.entry_points()
        entry_points = all_entry_points.select(
            group=SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP,
        )
    return tuple(entry_points)


def _env_provider_refs() -> tuple[str, ...]:
    raw = os.environ.get("AWARE_SDK_OPERATION_CATALOGS", "")
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _call_provider_ref(provider_ref: str) -> object:
    provider = _load_ref(provider_ref)
    if not callable(provider):
        raise SdkOperationCatalogError(
            f"Catalog provider is not callable: {provider_ref}"
        )
    return provider()


def _load_ref(ref: str) -> object:
    module_name, _, attr_path = ref.partition(":")
    if not module_name or not attr_path:
        raise SdkOperationCatalogError(
            f"Import ref must use module:attribute syntax: {ref!r}"
        )
    value: object = importlib.import_module(module_name)
    for attr in attr_path.split("."):
        value = getattr(value, attr)
    return value


def _catalog_from_payload(payload: object, *, provider_ref: str) -> SdkOperationCatalog:
    if not isinstance(payload, Mapping):
        raise SdkOperationCatalogError(
            f"SDK operation catalog provider returned non-object: {provider_ref}"
        )
    contract = str(payload.get("catalog_contract") or "").strip()
    if contract != SDK_OPERATION_CATALOG_CONTRACT:
        raise SdkOperationCatalogError(
            "SDK operation catalog has unsupported contract: "
            + f"{contract!r} from {provider_ref}"
        )
    sdk_name = _normalize_token(payload.get("sdk_name"), label="sdk_name")
    raw_operations = payload.get("operations")
    if not isinstance(raw_operations, (list, tuple)):
        raise SdkOperationCatalogError(
            f"SDK operation catalog operations must be a list: {provider_ref}"
        )
    operations = tuple(_operation_from_payload(item) for item in raw_operations)
    return SdkOperationCatalog(
        sdk_name=sdk_name,
        package_name=_normalize_token(
            payload.get("package_name"), label="package_name"
        ),
        version_number=_optional_int(payload.get("version_number")),
        provider_ref=provider_ref,
        operations=tuple(sorted(operations, key=lambda item: item.operation_ref)),
    )


def _operation_from_payload(payload: object) -> SdkOperationDescriptor:
    if not isinstance(payload, Mapping):
        raise SdkOperationCatalogError("SDK operation descriptor must be an object.")
    return SdkOperationDescriptor(
        operation_ref=_normalize_operation_ref(payload.get("operation_ref")),
        title=_optional_text(payload.get("title")),
        description=_optional_text(payload.get("description")),
        endpoint_refs=tuple(
            _normalize_token(item, label="endpoint_ref")
            for item in _sequence(payload.get("endpoint_refs"), label="endpoint_refs")
        ),
        input_schema=_mapping(payload.get("input_schema"), label="input_schema"),
        context_schema=_mapping(payload.get("context_schema"), label="context_schema"),
        effect=_normalize_effect(payload.get("effect")),
        stability=_optional_text(payload.get("stability")) or "preview",
        handler_ref=_optional_text(payload.get("handler_ref")),
        requires_confirmation=bool(payload.get("requires_confirmation", False)),
    )


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise SdkOperationCatalogError(f"SDK operation {label} must be an object.")
    return {str(key): item for key, item in value.items()}


def _sequence(value: object, *, label: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SdkOperationCatalogError(f"SDK operation {label} must be a list.")
    return tuple(value)


def _normalize_operation_ref(value: object) -> str:
    text = _normalize_token(value, label="operation_ref")
    parts = text.split(".")
    if len(parts) != 2:
        raise SdkOperationCatalogError(
            f"SDK operation_ref must use sdk_name.operation_name: {text!r}"
        )
    return ".".join(_normalize_token(part, label="operation_ref") for part in parts)


def _split_operation_ref(operation_ref: str) -> tuple[str, str]:
    sdk_name, operation_name = operation_ref.split(".", 1)
    return sdk_name, operation_name


def _normalize_effect(value: object) -> str:
    effect = _optional_text(value) or "read"
    if effect not in {"read", "write", "stream"}:
        raise SdkOperationCatalogError(f"Unsupported SDK operation effect: {effect!r}")
    return effect


def _normalize_token(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SdkOperationCatalogError(f"SDK operation catalog {label} must be set.")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise SdkOperationCatalogError(
        f"SDK operation catalog version_number must be an integer: {value!r}"
    )


__all__ = [
    "SDK_OPERATION_CATALOG_CONTRACT",
    "SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP",
    "SdkOperationCatalog",
    "SdkOperationCatalogError",
    "SdkOperationCatalogIndex",
    "SdkOperationDescriptor",
    "invoke_sdk_operation",
    "load_sdk_operation_catalog_index",
    "parse_json_object",
    "path_context_value",
]
