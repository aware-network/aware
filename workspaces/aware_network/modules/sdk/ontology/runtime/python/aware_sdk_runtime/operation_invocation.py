"""Runtime invocation for SDK operation catalogs.

This module is the execution side of ``aware.sdk_operation_catalog.v0``.
It deliberately resolves operations from SDK-published catalogs instead of
guessing implementation modules from operation refs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import import_module, metadata
import inspect
import os


SDK_OPERATION_CATALOG_CONTRACT = "aware.sdk_operation_catalog.v0"
SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP = "aware.sdk_operation_catalogs"


class SdkOperationInvocationError(RuntimeError):
    """Raised when a catalog-declared SDK operation cannot be invoked."""


@dataclass(frozen=True, slots=True)
class SdkOperationDescriptor:
    operation_ref: str
    endpoint_refs: tuple[str, ...]
    effect: str
    handler_ref: str | None
    requires_confirmation: bool
    catalog_provider_ref: str
    package_name: str
    sdk_name: str


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogIndex:
    operation_by_ref: Mapping[str, SdkOperationDescriptor]

    def resolve(self, operation_ref: str) -> SdkOperationDescriptor:
        normalized = _normalize_operation_ref(operation_ref)
        operation = self.operation_by_ref.get(normalized)
        if operation is None:
            raise SdkOperationInvocationError(
                f"Unknown SDK operation_ref={operation_ref!r}."
            )
        return operation


def load_sdk_operation_catalog_index(
    *,
    extra_provider_refs: Iterable[str] = (),
) -> SdkOperationCatalogIndex:
    """Load SDK operation catalogs from installed implementation packages."""

    operation_by_ref: dict[str, SdkOperationDescriptor] = {}
    for provider_ref, catalog in (
        *_load_entry_point_catalogs(),
        *_load_explicit_provider_catalogs(
            provider_refs=(*_env_provider_refs(), *tuple(extra_provider_refs)),
        ),
    ):
        _append_catalog_operations(
            operation_by_ref=operation_by_ref,
            provider_ref=provider_ref,
            catalog=catalog,
        )
    return SdkOperationCatalogIndex(operation_by_ref=operation_by_ref)


async def invoke_sdk_operation_from_catalog(
    *,
    operation_ref: str,
    request_payload: Mapping[str, object] | None = None,
    context: Mapping[str, object] | None = None,
    timeout_s: float | None = None,
    allow_mutation: bool = False,
    extra_provider_refs: Iterable[str] = (),
) -> object:
    """Invoke one SDK operation through its catalog-declared handler."""

    index = load_sdk_operation_catalog_index(
        extra_provider_refs=extra_provider_refs,
    )
    operation = index.resolve(operation_ref)
    if operation.effect != "read" and not allow_mutation:
        raise SdkOperationInvocationError(
            "SDK operation may mutate state; allow mutation before invoking: "
            + operation.operation_ref
        )
    if not operation.handler_ref:
        raise SdkOperationInvocationError(
            "SDK operation has no runtime handler_ref: "
            + operation.operation_ref
        )
    handler = _load_ref(operation.handler_ref)
    if not callable(handler):
        raise SdkOperationInvocationError(
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


def _append_catalog_operations(
    *,
    operation_by_ref: dict[str, SdkOperationDescriptor],
    provider_ref: str,
    catalog: object,
) -> None:
    if not isinstance(catalog, Mapping):
        raise SdkOperationInvocationError(
            "SDK operation catalog provider returned non-mapping payload: "
            + provider_ref
        )
    catalog_contract = str(catalog.get("catalog_contract") or "").strip()
    if catalog_contract != SDK_OPERATION_CATALOG_CONTRACT:
        raise SdkOperationInvocationError(
            "Unsupported SDK operation catalog contract: "
            + f"provider={provider_ref!r} contract={catalog_contract!r}"
        )
    sdk_name = _required_text(catalog.get("sdk_name"), label="sdk_name")
    package_name = _required_text(
        catalog.get("package_name"),
        label="package_name",
    )
    raw_operations = catalog.get("operations")
    if not isinstance(raw_operations, list):
        raise SdkOperationInvocationError(
            f"SDK operation catalog operations must be a list: {provider_ref}"
        )
    for raw_operation in raw_operations:
        if not isinstance(raw_operation, Mapping):
            raise SdkOperationInvocationError(
                f"SDK operation entry must be a mapping: {provider_ref}"
            )
        operation_ref = _normalize_operation_ref(
            _required_text(
                raw_operation.get("operation_ref"),
                label="operation_ref",
            )
        )
        operation_sdk_name, _ = operation_ref.split(".", 1)
        if operation_sdk_name != sdk_name:
            raise SdkOperationInvocationError(
                "SDK operation ref does not match catalog sdk_name: "
                + f"{operation_ref!r} under {sdk_name!r}"
            )
        if operation_ref in operation_by_ref:
            raise SdkOperationInvocationError(
                f"Duplicate SDK operation_ref={operation_ref!r}."
            )
        operation_by_ref[operation_ref] = SdkOperationDescriptor(
            operation_ref=operation_ref,
            endpoint_refs=tuple(
                str(endpoint_ref)
                for endpoint_ref in _sequence(
                    raw_operation.get("endpoint_refs")
                )
            ),
            effect=(
                str(raw_operation.get("effect") or "write").strip() or "write"
            ),
            handler_ref=_optional_text(raw_operation.get("handler_ref")),
            requires_confirmation=bool(
                raw_operation.get("requires_confirmation")
            ),
            catalog_provider_ref=provider_ref,
            package_name=package_name,
            sdk_name=sdk_name,
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
    except TypeError:  # pragma: no cover
        entry_points = metadata.entry_points().select(
            group=SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP
        )
    return tuple(entry_points)


def _load_explicit_provider_catalogs(
    *,
    provider_refs: Iterable[str],
) -> tuple[tuple[str, object], ...]:
    loaded: list[tuple[str, object]] = []
    for provider_ref in provider_refs:
        normalized = provider_ref.strip()
        if not normalized:
            continue
        provider = _load_ref(normalized)
        if not callable(provider):
            raise SdkOperationInvocationError(
                f"SDK catalog provider is not callable: {normalized}"
            )
        loaded.append((normalized, provider()))
    return tuple(loaded)


def _env_provider_refs() -> tuple[str, ...]:
    raw = os.environ.get("AWARE_SDK_OPERATION_CATALOGS", "")
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _load_ref(ref: str) -> object:
    module_name, separator, attr_name = ref.partition(":")
    if not separator or not module_name.strip() or not attr_name.strip():
        raise SdkOperationInvocationError(
            f"Import ref must use `module:attribute`: {ref!r}"
        )
    module = import_module(module_name)
    target: object = module
    for segment in attr_name.split("."):
        if not segment:
            raise SdkOperationInvocationError(f"Invalid import ref: {ref!r}")
        target = getattr(target, segment)
    return target


def _normalize_operation_ref(value: str) -> str:
    parts = [
        _required_text(part, label="operation_ref segment")
        for part in str(value or "").split(".")
        if part.strip()
    ]
    if len(parts) != 2:
        raise SdkOperationInvocationError(
            "SDK operation ref must use `sdk_name.operation_name`: "
            + repr(value)
        )
    return ".".join(parts)


def _required_text(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SdkOperationInvocationError(
            f"SDK operation catalog {label} is empty."
        )
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


__all__ = [
    "SDK_OPERATION_CATALOG_CONTRACT",
    "SDK_OPERATION_CATALOG_ENTRY_POINT_GROUP",
    "SdkOperationCatalogIndex",
    "SdkOperationDescriptor",
    "SdkOperationInvocationError",
    "invoke_sdk_operation_from_catalog",
    "load_sdk_operation_catalog_index",
]
