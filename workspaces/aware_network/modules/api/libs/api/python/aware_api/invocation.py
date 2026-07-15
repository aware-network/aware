"""Consumer-side loader/index for ApiInvocationManifest artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from pydantic import BaseModel, Field

DEFAULT_API_INVOCATION_MANIFEST_FILENAME = "api.invocation_manifest.json"
SUPPORTED_API_INVOCATION_SCHEMA_VERSIONS = frozenset({1})


class ApiInvocationFulfillmentBindingSpec(BaseModel):
    name: str
    graph_target: str
    graph_capability_function_name: str
    source_path: str


class ApiInvocationStreamEventSpec(BaseModel):
    kind: str
    class_ref: str
    python_model_ref: str | None = None
    source_path: str
    description: str | None = None


class ApiInvocationStreamSpec(BaseModel):
    stream_mode: str
    source_path: str
    events: list[ApiInvocationStreamEventSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInvocationResponseSpec(BaseModel):
    class_ref: str
    python_model_ref: str | None = None
    source_path: str
    description: str | None = None


class ApiInvocationRequestSpec(BaseModel):
    class_ref: str
    python_model_ref: str | None = None
    source_path: str
    description: str | None = None


class ApiInvocationEndpointSpec(BaseModel):
    name: str
    source_path: str
    endpoint_ref: str
    discriminant: str
    invocation_kind: str
    client_backend: str
    client_operation: str
    addressing_strategy: str
    request: ApiInvocationRequestSpec
    response: ApiInvocationResponseSpec | None = None
    stream: ApiInvocationStreamSpec | None = None
    fulfillment_bindings: list[ApiInvocationFulfillmentBindingSpec] = Field(default_factory=list)
    adapter_callable_ref: str | None = None
    description: str | None = None


class ApiInvocationCapabilitySpec(BaseModel):
    name: str
    source_path: str
    endpoints: list[ApiInvocationEndpointSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInvocationApiSpec(BaseModel):
    name: str
    source_path: str
    capabilities: list[ApiInvocationCapabilitySpec] = Field(default_factory=list)


class ApiInvocationManifest(BaseModel):
    schema_version: int
    package_name: str
    fqn_prefix: str
    apis: list[ApiInvocationApiSpec] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ApiInvocationCapabilityBinding:
    api: ApiInvocationApiSpec
    capability: ApiInvocationCapabilitySpec

    @property
    def capability_ref(self) -> str:
        return _capability_ref(self.api.name, self.capability.name)


@dataclass(frozen=True, slots=True)
class ApiInvocationEndpointBinding:
    api: ApiInvocationApiSpec
    capability: ApiInvocationCapabilitySpec
    endpoint: ApiInvocationEndpointSpec

    @property
    def capability_ref(self) -> str:
        return _capability_ref(self.api.name, self.capability.name)

    @property
    def endpoint_ref(self) -> str:
        return self.endpoint.endpoint_ref


@dataclass(frozen=True, slots=True)
class ApiInvocationIndex:
    manifest: ApiInvocationManifest
    apis_by_name: Mapping[str, ApiInvocationApiSpec]
    capabilities_by_ref: Mapping[str, ApiInvocationCapabilityBinding]
    endpoints_by_ref: Mapping[str, ApiInvocationEndpointBinding]
    endpoints_by_discriminant: Mapping[str, ApiInvocationEndpointBinding]

    def get_api(self, api_name: str) -> ApiInvocationApiSpec | None:
        return self.apis_by_name.get(api_name)

    def require_api(self, api_name: str) -> ApiInvocationApiSpec:
        api = self.get_api(api_name)
        if api is None:
            raise KeyError(f"Unknown API '{api_name}'.")
        return api

    def get_capability(
        self,
        api_name: str,
        capability_name: str,
    ) -> ApiInvocationCapabilityBinding | None:
        return self.capabilities_by_ref.get(_capability_ref(api_name, capability_name))

    def require_capability(
        self,
        api_name: str,
        capability_name: str,
    ) -> ApiInvocationCapabilityBinding:
        capability = self.get_capability(api_name, capability_name)
        if capability is None:
            raise KeyError(f"Unknown capability '{api_name}.{capability_name}'.")
        return capability

    def get_endpoint(
        self,
        api_name: str,
        capability_name: str,
        endpoint_name: str,
    ) -> ApiInvocationEndpointBinding | None:
        return self.endpoints_by_ref.get(_endpoint_ref(api_name, capability_name, endpoint_name))

    def require_endpoint(
        self,
        api_name: str,
        capability_name: str,
        endpoint_name: str,
    ) -> ApiInvocationEndpointBinding:
        endpoint = self.get_endpoint(api_name, capability_name, endpoint_name)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint '{api_name}.{capability_name}.{endpoint_name}'.")
        return endpoint

    def get_endpoint_by_ref(self, endpoint_ref: str) -> ApiInvocationEndpointBinding | None:
        return self.endpoints_by_ref.get(endpoint_ref.strip())

    def require_endpoint_by_ref(self, endpoint_ref: str) -> ApiInvocationEndpointBinding:
        endpoint = self.get_endpoint_by_ref(endpoint_ref)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint ref '{endpoint_ref}'.")
        return endpoint

    def get_endpoint_by_discriminant(self, discriminant: str) -> ApiInvocationEndpointBinding | None:
        return self.endpoints_by_discriminant.get(discriminant.strip())

    def require_endpoint_by_discriminant(self, discriminant: str) -> ApiInvocationEndpointBinding:
        endpoint = self.get_endpoint_by_discriminant(discriminant)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint discriminant '{discriminant}'.")
        return endpoint


@dataclass(frozen=True, slots=True)
class LoadedApiInvocationManifest:
    manifest: ApiInvocationManifest
    index: ApiInvocationIndex
    hash_sha256: str
    source_path: Path | None = None


@dataclass(frozen=True, slots=True)
class PreparedApiEndpointInvocation:
    endpoint: ApiInvocationEndpointBinding
    request_payload: Mapping[str, Any]
    request_class_ref: str
    request_python_model_ref: str | None
    response_class_ref: str | None
    response_python_model_ref: str | None
    stream_mode: str | None
    stream_event_class_refs: Mapping[str, str]
    stream_event_python_model_refs: Mapping[str, str]
    invocation_kind: str
    client_backend: str
    client_operation: str
    addressing_strategy: str


def load_api_invocation_manifest_file(path: str | Path) -> LoadedApiInvocationManifest:
    source_path = Path(path).expanduser().resolve()
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    return load_api_invocation_manifest_payload(payload, source_path=source_path)


def load_api_invocation_manifest_json(
    data: str | bytes,
    *,
    source_path: str | Path | None = None,
) -> LoadedApiInvocationManifest:
    payload = json.loads(data)
    return load_api_invocation_manifest_payload(payload, source_path=source_path)


def load_api_invocation_manifest_payload(
    payload: Any,
    *,
    source_path: str | Path | None = None,
) -> LoadedApiInvocationManifest:
    if not isinstance(payload, dict):
        raise ValueError("ApiInvocationManifest payload must be a JSON object.")

    manifest = ApiInvocationManifest.model_validate(payload)
    _validate_manifest(manifest)
    index = build_api_invocation_index(manifest)
    canonical_payload = manifest.model_dump(mode="json", exclude_none=True)
    digest = sha256(
        json.dumps(
            canonical_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return LoadedApiInvocationManifest(
        manifest=manifest,
        index=index,
        hash_sha256=digest,
        source_path=_normalize_source_path(source_path),
    )


def build_api_invocation_index(manifest: ApiInvocationManifest) -> ApiInvocationIndex:
    _validate_manifest(manifest)

    apis_by_name: dict[str, ApiInvocationApiSpec] = {}
    capabilities_by_ref: dict[str, ApiInvocationCapabilityBinding] = {}
    endpoints_by_ref: dict[str, ApiInvocationEndpointBinding] = {}
    endpoints_by_discriminant: dict[str, ApiInvocationEndpointBinding] = {}

    for api in manifest.apis:
        api_name = _validated_key("api.name", api.name)
        if api_name in apis_by_name:
            raise ValueError(f"Duplicate API name '{api_name}'.")
        apis_by_name[api_name] = api

        capability_names: set[str] = set()
        for capability in api.capabilities:
            capability_name = _validated_key(f"capability.name[{api_name}]", capability.name)
            if capability_name in capability_names:
                raise ValueError(f"Duplicate capability name '{api_name}.{capability_name}'.")
            capability_names.add(capability_name)

            capability_binding = ApiInvocationCapabilityBinding(api=api, capability=capability)
            capability_ref = capability_binding.capability_ref
            if capability_ref in capabilities_by_ref:
                raise ValueError(f"Duplicate capability ref '{capability_ref}'.")
            capabilities_by_ref[capability_ref] = capability_binding

            endpoint_names: set[str] = set()
            for endpoint in capability.endpoints:
                endpoint_name = _validated_key(f"endpoint.name[{capability_ref}]", endpoint.name)
                if endpoint_name in endpoint_names:
                    raise ValueError(f"Duplicate endpoint name '{capability_ref}.{endpoint_name}'.")
                endpoint_names.add(endpoint_name)

                endpoint_binding = ApiInvocationEndpointBinding(
                    api=api,
                    capability=capability,
                    endpoint=endpoint,
                )
                endpoint_ref = _validated_key(
                    f"endpoint.endpoint_ref[{capability_ref}.{endpoint_name}]",
                    endpoint.endpoint_ref,
                )
                if endpoint_ref in endpoints_by_ref:
                    raise ValueError(f"Duplicate endpoint ref '{endpoint_ref}'.")
                endpoints_by_ref[endpoint_ref] = endpoint_binding

                discriminant = _validated_key(
                    f"endpoint.discriminant[{endpoint_ref}]",
                    endpoint.discriminant,
                )
                if discriminant in endpoints_by_discriminant:
                    raise ValueError(f"Duplicate endpoint discriminant '{discriminant}'.")
                endpoints_by_discriminant[discriminant] = endpoint_binding

                _validated_key(f"endpoint.invocation_kind[{endpoint_ref}]", endpoint.invocation_kind)
                _validated_key(f"endpoint.client_backend[{endpoint_ref}]", endpoint.client_backend)
                _validated_key(f"endpoint.client_operation[{endpoint_ref}]", endpoint.client_operation)
                _validated_key(
                    f"endpoint.addressing_strategy[{endpoint_ref}]",
                    endpoint.addressing_strategy,
                )

    return ApiInvocationIndex(
        manifest=manifest,
        apis_by_name=MappingProxyType(dict(apis_by_name)),
        capabilities_by_ref=MappingProxyType(dict(capabilities_by_ref)),
        endpoints_by_ref=MappingProxyType(dict(endpoints_by_ref)),
        endpoints_by_discriminant=MappingProxyType(dict(endpoints_by_discriminant)),
    )


def _validate_manifest(manifest: ApiInvocationManifest) -> None:
    if manifest.schema_version not in SUPPORTED_API_INVOCATION_SCHEMA_VERSIONS:
        raise ValueError(
            "Unsupported ApiInvocationManifest schema_version "
            f"{manifest.schema_version!r}; supported={sorted(SUPPORTED_API_INVOCATION_SCHEMA_VERSIONS)}."
        )
    _validated_key("package_name", manifest.package_name)
    _validated_key("fqn_prefix", manifest.fqn_prefix)


def _validated_key(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _capability_ref(api_name: str, capability_name: str) -> str:
    return ".".join((api_name, capability_name))


def _endpoint_ref(api_name: str, capability_name: str, endpoint_name: str) -> str:
    return ".".join((api_name, capability_name, endpoint_name))


def _normalize_source_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    return Path(path).expanduser().resolve()


__all__ = [
    "ApiInvocationApiSpec",
    "ApiInvocationCapabilityBinding",
    "ApiInvocationCapabilitySpec",
    "ApiInvocationEndpointBinding",
    "ApiInvocationEndpointSpec",
    "ApiInvocationFulfillmentBindingSpec",
    "ApiInvocationIndex",
    "ApiInvocationManifest",
    "ApiInvocationRequestSpec",
    "ApiInvocationResponseSpec",
    "ApiInvocationStreamEventSpec",
    "ApiInvocationStreamSpec",
    "DEFAULT_API_INVOCATION_MANIFEST_FILENAME",
    "LoadedApiInvocationManifest",
    "PreparedApiEndpointInvocation",
    "build_api_invocation_index",
    "load_api_invocation_manifest_file",
    "load_api_invocation_manifest_json",
    "load_api_invocation_manifest_payload",
]
