"""Transport-neutral caller-side API endpoint invocation substrate."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from importlib import import_module
from importlib.resources import files
import inspect
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol, cast

from pydantic import BaseModel

from aware_types import JsonObject, JsonValue

from .invocation import (
    ApiInvocationEndpointBinding,
    ApiInvocationIndex,
    LoadedApiInvocationManifest,
    PreparedApiEndpointInvocation,
)


_SUPPORTED_CLIENT_BACKENDS = frozenset(
    {
        "aware_api.invoker.AwareApiEndpointInvoker",
    }
)
_SUPPORTED_CLIENT_OPERATIONS = frozenset({"invoke_api_endpoint"})
_AWARE_CLASS_REF_MODULE_CACHE: dict[str, tuple[str, str] | None] = {}
_PYDANTIC_PACKAGE_BOOTSTRAPPED: set[str] = set()
_PYDANTIC_PACKAGE_MODEL_NAMESPACE_CACHE: dict[str, dict[str, object] | None] = {}


@dataclass(frozen=True, slots=True)
class ApiEndpointInvocation:
    """One caller-side hit against a compiled API endpoint contract."""

    endpoint_ref: str
    discriminant: str
    request_payload: JsonObject


@dataclass(frozen=True, slots=True)
class ApiEndpointResponse:
    """Transport-neutral API endpoint response envelope."""

    status: str = "succeeded"
    response_payload: object | None = None
    error: str | None = None
    receipt: object | None = None
    stream_lifecycle: str = "auto_close"


@dataclass(frozen=True, slots=True)
class ApiEndpointStream:
    """Transport-neutral stream of API endpoint response envelopes."""

    events: AsyncIterator[ApiEndpointResponse]
    close: Callable[[], Awaitable[None]]
    response: Awaitable[ApiEndpointResponse] | None = None


class ApiEndpointTransport(Protocol):
    """Caller-owned transport adapter for non-streaming endpoint invocation."""

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse: ...


class ApiEndpointStreamTransport(ApiEndpointTransport, Protocol):
    """Caller-owned transport adapter for streaming endpoint invocation."""

    async def open_stream(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointStream: ...


class AwareApiEndpointInvoker:
    """Caller-side API endpoint invoker shared by generated API clients.

    The invoker owns contract lookup, payload normalization, and typed response
    decoding. It deliberately does not own Node routing, Service selection, or
    hosted-runtime discovery; callers provide those semantics through the
    transport adapter.
    """

    def __init__(self, transport: ApiEndpointTransport) -> None:
        self._transport = transport

    @property
    def transport(self) -> ApiEndpointTransport:
        return self._transport

    def prepare_api_endpoint_invocation(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
    ) -> PreparedApiEndpointInvocation:
        index = _resolve_api_invocation_index(manifest)
        endpoint = _resolve_api_invocation_endpoint(
            index=index,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        _validate_api_endpoint_client_contract(endpoint)
        normalized_payload = _normalize_api_endpoint_request_payload(request_payload)
        stream_event_class_refs = MappingProxyType(
            {
                event.kind: event.class_ref
                for event in (endpoint.endpoint.stream.events if endpoint.endpoint.stream else [])
            }
        )
        stream_event_python_model_refs = MappingProxyType(
            {
                event.kind: event.python_model_ref
                for event in (endpoint.endpoint.stream.events if endpoint.endpoint.stream else [])
                if event.python_model_ref is not None
            }
        )
        return PreparedApiEndpointInvocation(
            endpoint=endpoint,
            request_payload=MappingProxyType(dict(normalized_payload)),
            request_class_ref=endpoint.endpoint.request.class_ref,
            request_python_model_ref=endpoint.endpoint.request.python_model_ref,
            response_class_ref=(
                endpoint.endpoint.response.class_ref if endpoint.endpoint.response is not None else None
            ),
            response_python_model_ref=(
                endpoint.endpoint.response.python_model_ref
                if endpoint.endpoint.response is not None
                else None
            ),
            stream_mode=(
                endpoint.endpoint.stream.stream_mode
                if endpoint.endpoint.stream is not None
                else None
            ),
            stream_event_class_refs=stream_event_class_refs,
            stream_event_python_model_refs=stream_event_python_model_refs,
            invocation_kind=endpoint.endpoint.invocation_kind,
            client_backend=endpoint.endpoint.client_backend,
            client_operation=endpoint.endpoint.client_operation,
            addressing_strategy=endpoint.endpoint.addressing_strategy,
        )

    async def invoke_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> Any:
        prepared = self.prepare_api_endpoint_invocation(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        response = await self.invoke_api_endpoint_raw(
            endpoint_ref=prepared.endpoint.endpoint_ref,
            discriminant=prepared.endpoint.endpoint.discriminant,
            request_payload=dict(prepared.request_payload),
            timeout_s=timeout_s,
        )
        status = _normalize_token(response.status)
        if status == "pending":
            raise NotImplementedError(
                "API endpoint request is still pending and no terminal response is available for "
                f"endpoint {prepared.endpoint.endpoint_ref!r}."
            )
        if status == "failed":
            raise RuntimeError(response.error or "API endpoint request failed")
        return decode_api_endpoint_response_payload(
            prepared=prepared,
            response_payload=response.response_payload,
        )

    async def invoke_api_endpoint_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: BaseModel | Mapping[str, Any],
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        invocation = ApiEndpointInvocation(
            endpoint_ref=_required_text("endpoint_ref", endpoint_ref),
            discriminant=_required_text("discriminant", discriminant),
            request_payload=JsonObject(_normalize_api_endpoint_request_payload(request_payload)),
        )
        response = await self._transport.invoke(invocation, timeout_s=timeout_s)
        return _coerce_api_endpoint_response(response)

    async def stream_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> AsyncIterator[Any]:
        prepared = self.prepare_api_endpoint_invocation(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        if prepared.stream_mode is None:
            raise ValueError(
                "API endpoint does not declare a stream contract for caller-side stream helpers: "
                f"{prepared.endpoint.endpoint_ref!r}"
            )
        handle = await self.open_api_endpoint_stream_raw(
            endpoint_ref=prepared.endpoint.endpoint_ref,
            discriminant=prepared.endpoint.endpoint.discriminant,
            request_payload=dict(prepared.request_payload),
            timeout_s=timeout_s,
        )
        try:
            async for item in handle.events:
                response = _coerce_api_endpoint_response(item)
                status = _normalize_token(response.status)
                if status == "failed":
                    raise RuntimeError(response.error or "API stream request failed")
                yield decode_api_stream_event_payload(
                    prepared=prepared,
                    event_payload=response.response_payload,
                )
        finally:
            await handle.close()

    async def open_api_endpoint_stream_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: BaseModel | Mapping[str, Any],
        timeout_s: float | None = None,
    ) -> ApiEndpointStream:
        if not callable(getattr(self._transport, "open_stream", None)):
            raise RuntimeError("API endpoint transport does not support streaming.")
        transport = cast(ApiEndpointStreamTransport, self._transport)
        invocation = ApiEndpointInvocation(
            endpoint_ref=_required_text("endpoint_ref", endpoint_ref),
            discriminant=_required_text("discriminant", discriminant),
            request_payload=JsonObject(_normalize_api_endpoint_request_payload(request_payload)),
        )
        stream = await transport.open_stream(invocation, timeout_s=timeout_s)
        if not isinstance(stream, ApiEndpointStream):
            raise TypeError("API endpoint stream transport returned an unexpected stream handle.")
        return stream


def decode_api_endpoint_response_payload(
    *,
    prepared: PreparedApiEndpointInvocation,
    response_payload: object,
) -> Any:
    response_model_ref = prepared.response_python_model_ref or prepared.response_class_ref
    if response_model_ref is None or response_payload is None:
        return response_payload
    model_cls = resolve_api_endpoint_model_class(response_model_ref)
    if isinstance(response_payload, model_cls):
        return response_payload
    return model_cls.model_validate(response_payload)


def decode_api_stream_event_payload(
    *,
    prepared: PreparedApiEndpointInvocation,
    event_payload: object,
) -> Any:
    class_refs = tuple(
        dict.fromkeys(
            prepared.stream_event_python_model_refs.get(kind) or class_ref
            for kind, class_ref in prepared.stream_event_class_refs.items()
        )
    )
    if not class_refs or event_payload is None:
        return event_payload

    matches: list[Any] = []
    payload_kind = _payload_kind(event_payload)
    if payload_kind is not None:
        kind_matches: list[Any] = []
        for class_ref in class_refs:
            model_cls = resolve_api_endpoint_model_class(class_ref)
            if _model_kind_default(model_cls) != payload_kind:
                continue
            if isinstance(event_payload, model_cls):
                return event_payload
            try:
                kind_matches.append(model_cls.model_validate(event_payload))
            except Exception:
                continue
        if len(kind_matches) == 1:
            return kind_matches[0]

    for class_ref in class_refs:
        model_cls = resolve_api_endpoint_model_class(class_ref)
        if isinstance(event_payload, model_cls):
            return event_payload
        try:
            matches.append(model_cls.model_validate(event_payload))
        except Exception:
            continue

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError(
            "Ambiguous API stream event payload for "
            f"endpoint {prepared.endpoint.endpoint_ref!r}."
        )
    return event_payload


def _payload_kind(event_payload: object) -> str | None:
    if not isinstance(event_payload, dict):
        return None
    value = event_payload.get("kind")
    if not isinstance(value, str):
        return None
    kind = value.strip()
    return kind or None


def _model_kind_default(model_cls: type[BaseModel]) -> str | None:
    field = model_cls.model_fields.get("kind")
    if field is None or not isinstance(field.default, str):
        return None
    kind = field.default.strip()
    return kind or None


def resolve_api_endpoint_model_class(class_ref: str) -> type[BaseModel]:
    module_name, _, class_name = class_ref.rpartition(".")
    if not module_name or not class_name:
        raise RuntimeError(
            "API endpoint response class_ref must be fully qualified: "
            f"{class_ref!r}"
        )
    resolved: object | None = None
    try:
        _bootstrap_generated_pydantic_package_for_ref(class_ref)
        resolved = getattr(import_module(module_name), class_name)
    except Exception:
        fallback = _resolve_bootstrapped_aware_class_ref(class_ref)
        if fallback is not None:
            fallback_module_name, fallback_class_name = fallback
            resolved = getattr(import_module(fallback_module_name), fallback_class_name)
    if not inspect.isclass(resolved) or not issubclass(resolved, BaseModel):
        raise RuntimeError(
            "API endpoint response class_ref did not resolve to a Pydantic model: "
            f"{class_ref!r}"
        )
    model_cls = cast(type[BaseModel], resolved)
    _ensure_api_endpoint_model_rebuilt(model_cls=model_cls, class_ref=class_ref)
    return model_cls


def _bootstrap_generated_pydantic_package_for_ref(class_ref: str) -> None:
    package_root, _, _ = class_ref.partition(".")
    if not package_root or package_root in _PYDANTIC_PACKAGE_BOOTSTRAPPED:
        return

    try:
        package = import_module(package_root)
        bootstrap_path = files(package).joinpath("_aware", "python.bootstrap.json")
        if not bootstrap_path.is_file():
            return
        from aware_utils.pydantic.package_bootstrap import (
            bootstrap_pydantic_package_from_artifacts,
        )

        bootstrap_pydantic_package_from_artifacts(
            package_prefix=package_root,
            strict_imports=False,
        )
        _PYDANTIC_PACKAGE_BOOTSTRAPPED.add(package_root)
    except Exception:
        return


def _ensure_api_endpoint_model_rebuilt(
    *,
    model_cls: type[BaseModel],
    class_ref: str,
) -> None:
    namespace = _generated_pydantic_package_model_namespace(class_ref)
    if namespace is not None:
        try:
            _rebuild_api_endpoint_model_with_namespace(
                model_cls=model_cls,
                namespace=namespace,
            )
            return
        except Exception:
            pass
    try:
        model_cls.model_rebuild(force=True)
    except Exception:
        return


def _generated_pydantic_package_model_namespace(class_ref: str) -> dict[str, object] | None:
    package_root, _, _ = class_ref.partition(".")
    if not package_root:
        return None
    cached = _PYDANTIC_PACKAGE_MODEL_NAMESPACE_CACHE.get(package_root)
    if cached is not None or package_root in _PYDANTIC_PACKAGE_MODEL_NAMESPACE_CACHE:
        return cached

    namespace: dict[str, object] = {
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "frozenset": frozenset,
    }
    try:
        package = import_module(package_root)
        manifest_path = files(package).joinpath("_aware", "python.bootstrap.json")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        modules = payload.get("modules") or []
    except Exception:
        _PYDANTIC_PACKAGE_MODEL_NAMESPACE_CACHE[package_root] = None
        return None

    if not isinstance(modules, list):
        _PYDANTIC_PACKAGE_MODEL_NAMESPACE_CACHE[package_root] = None
        return None

    for entry in modules:
        if not isinstance(entry, str):
            continue
        module_name = entry.strip()
        if not module_name:
            continue
        try:
            module = import_module(module_name)
        except Exception:
            continue
        module_dict = getattr(module, "__dict__", {})
        if not isinstance(module_dict, dict):
            continue
        for resolved in module_dict.values():
            if not inspect.isclass(resolved) or not issubclass(resolved, BaseModel):
                continue
            resolved_module = str(getattr(resolved, "__module__", ""))
            if not resolved_module.startswith(f"{package_root}."):
                continue
            namespace[resolved.__name__] = resolved

    for value in tuple(namespace.values()):
        if inspect.isclass(value) and issubclass(value, BaseModel):
            try:
                _rebuild_api_endpoint_model_with_namespace(
                    model_cls=cast(type[BaseModel], value),
                    namespace=namespace,
                )
            except Exception:
                continue

    _PYDANTIC_PACKAGE_MODEL_NAMESPACE_CACHE[package_root] = namespace
    return namespace


def _rebuild_api_endpoint_model_with_namespace(
    *,
    model_cls: type[BaseModel],
    namespace: Mapping[str, object],
) -> None:
    rebuild_namespace: dict[str, object] = {}
    try:
        module = import_module(model_cls.__module__)
        module_dict = getattr(module, "__dict__", {})
        if isinstance(module_dict, dict):
            rebuild_namespace.update(module_dict)
    except Exception:
        pass
    rebuild_namespace.update(namespace)
    model_cls.model_rebuild(force=True, _types_namespace=rebuild_namespace)


def _resolve_bootstrapped_aware_class_ref(class_ref: str) -> tuple[str, str] | None:
    cached = _AWARE_CLASS_REF_MODULE_CACHE.get(class_ref)
    if cached is not None or class_ref in _AWARE_CLASS_REF_MODULE_CACHE:
        return cached

    package_root, _, _ = class_ref.partition(".")
    if not package_root:
        _AWARE_CLASS_REF_MODULE_CACHE[class_ref] = None
        return None

    try:
        package = import_module(package_root)
        manifest_path = files(package).joinpath("_aware", "python.models.json")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        _AWARE_CLASS_REF_MODULE_CACHE[class_ref] = None
        return None

    classes = payload.get("classes") or []
    if not isinstance(classes, list):
        _AWARE_CLASS_REF_MODULE_CACHE[class_ref] = None
        return None

    for entry in classes:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("aware_class_ref") or "").strip() != class_ref:
            continue
        module_name = str(entry.get("module") or "").strip()
        class_name = str(entry.get("name") or "").strip()
        if not module_name or not class_name:
            break
        resolved = (module_name, class_name)
        _AWARE_CLASS_REF_MODULE_CACHE[class_ref] = resolved
        return resolved

    _AWARE_CLASS_REF_MODULE_CACHE[class_ref] = None
    return None


def _resolve_api_invocation_index(
    manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
) -> ApiInvocationIndex:
    if isinstance(manifest, LoadedApiInvocationManifest):
        return manifest.index
    return manifest


def _resolve_api_invocation_endpoint(
    *,
    index: ApiInvocationIndex,
    endpoint_ref: str | None,
    discriminant: str | None,
    api_name: str | None,
    capability_name: str | None,
    endpoint_name: str | None,
) -> ApiInvocationEndpointBinding:
    lookup_count = sum(
        value is not None
        for value in (endpoint_ref, discriminant)
    ) + (
        1 if api_name is not None or capability_name is not None or endpoint_name is not None else 0
    )
    if lookup_count != 1:
        raise ValueError(
            "Exactly one endpoint locator is required: "
            "endpoint_ref, discriminant, or api_name+capability_name+endpoint_name."
        )

    if endpoint_ref is not None:
        return index.require_endpoint_by_ref(endpoint_ref)
    if discriminant is not None:
        return index.require_endpoint_by_discriminant(discriminant)
    if api_name is None or capability_name is None or endpoint_name is None:
        raise ValueError(
            "api_name, capability_name, and endpoint_name are required together "
            "when resolving an endpoint by names."
        )
    return index.require_endpoint(api_name, capability_name, endpoint_name)


def _validate_api_endpoint_client_contract(endpoint: ApiInvocationEndpointBinding) -> None:
    if endpoint.endpoint.client_backend not in _SUPPORTED_CLIENT_BACKENDS:
        raise ValueError(
            "Unsupported client backend "
            f"{endpoint.endpoint.client_backend!r} for endpoint {endpoint.endpoint_ref!r}."
        )
    if endpoint.endpoint.client_operation not in _SUPPORTED_CLIENT_OPERATIONS:
        raise ValueError(
            "Unsupported client operation "
            f"{endpoint.endpoint.client_operation!r} for endpoint {endpoint.endpoint_ref!r}."
        )


def _normalize_api_endpoint_request_payload(
    request_payload: BaseModel | Mapping[str, Any],
) -> dict[str, JsonValue]:
    if isinstance(request_payload, BaseModel):
        payload = request_payload.model_dump(mode="json", exclude_none=False)
    elif isinstance(request_payload, Mapping):
        payload = dict(request_payload)
    else:
        raise TypeError(
            "request_payload must be a pydantic BaseModel or mapping for invoke_api_endpoint."
        )
    return _normalize_json_object(payload)


def _normalize_json_object(payload: Mapping[str, Any]) -> dict[str, JsonValue]:
    normalized: dict[str, JsonValue] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TypeError("request_payload keys must be strings for invoke_api_endpoint.")
        normalized[key] = _normalize_json_value(value)
    return normalized


def _normalize_json_value(value: object) -> JsonValue:
    if isinstance(value, BaseModel):
        return cast(
            JsonValue,
            _normalize_json_value(value.model_dump(mode="json", exclude_none=False)),
        )
    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, dict):
        return cast(JsonValue, _normalize_json_object(cast(Mapping[str, Any], value)))
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Path):
        return str(value)
    value_attr = getattr(value, "value", None)
    if isinstance(value_attr, bool | int | float | str):
        return value_attr
    raise TypeError(f"Unsupported JSON value for API endpoint payload: {type(value).__name__}")


def _coerce_api_endpoint_response(response: object) -> ApiEndpointResponse:
    if isinstance(response, ApiEndpointResponse):
        return response
    if isinstance(response, BaseModel):
        return ApiEndpointResponse(
            status=_normalize_token(getattr(response, "status", "succeeded")),
            response_payload=getattr(response, "response_payload", None),
            error=getattr(response, "error", None),
            receipt=getattr(response, "receipt", None),
            stream_lifecycle=_normalize_token(
                getattr(response, "stream_lifecycle", "auto_close")
            ),
        )
    if isinstance(response, Mapping):
        return ApiEndpointResponse(
            status=_normalize_token(response.get("status", "succeeded")),
            response_payload=response.get("response_payload"),
            error=cast(str | None, response.get("error")),
            receipt=response.get("receipt"),
            stream_lifecycle=_normalize_token(response.get("stream_lifecycle", "auto_close")),
        )
    raise TypeError(f"Unsupported API endpoint response type: {type(response).__name__}")


def _normalize_token(value: object) -> str:
    raw = getattr(value, "value", value)
    if raw is None:
        return ""
    return str(raw).strip()


def _required_text(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


__all__ = [
    "ApiEndpointInvocation",
    "ApiEndpointResponse",
    "ApiEndpointStream",
    "ApiEndpointStreamTransport",
    "ApiEndpointTransport",
    "AwareApiEndpointInvoker",
    "decode_api_endpoint_response_payload",
    "decode_api_stream_event_payload",
    "resolve_api_endpoint_model_class",
]
