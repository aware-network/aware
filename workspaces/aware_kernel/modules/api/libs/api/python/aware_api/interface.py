"""Consumer-side loader/index for ApiInterfaceSpec artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from pydantic import BaseModel, Field

DEFAULT_API_INTERFACE_SPEC_FILENAME = "api.interface_spec.json"
SUPPORTED_API_INTERFACE_SCHEMA_VERSIONS = frozenset({1})


class ApiInterfaceStreamEventSpec(BaseModel):
    kind: str
    class_ref: str
    source_path: str
    description: str | None = None


class ApiInterfaceStreamSpec(BaseModel):
    stream_mode: str
    source_path: str
    events: list[ApiInterfaceStreamEventSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInterfaceResponseSpec(BaseModel):
    class_ref: str
    source_path: str
    description: str | None = None


class ApiInterfaceRequestSpec(BaseModel):
    class_ref: str
    source_path: str
    description: str | None = None


class ApiInterfaceEndpointSpec(BaseModel):
    name: str
    source_path: str
    discriminant: str
    request: ApiInterfaceRequestSpec
    response: ApiInterfaceResponseSpec | None = None
    stream: ApiInterfaceStreamSpec | None = None
    description: str | None = None


class ApiInterfaceCapabilitySpec(BaseModel):
    name: str
    source_path: str
    endpoints: list[ApiInterfaceEndpointSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInterfaceApiSpec(BaseModel):
    name: str
    source_path: str
    capabilities: list[ApiInterfaceCapabilitySpec] = Field(default_factory=list)


class ApiInterfaceSpec(BaseModel):
    schema_version: int
    package_name: str
    fqn_prefix: str
    apis: list[ApiInterfaceApiSpec] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ApiInterfaceCapabilityBinding:
    api: ApiInterfaceApiSpec
    capability: ApiInterfaceCapabilitySpec

    @property
    def capability_ref(self) -> str:
        return _capability_ref(self.api.name, self.capability.name)


@dataclass(frozen=True, slots=True)
class ApiInterfaceEndpointBinding:
    api: ApiInterfaceApiSpec
    capability: ApiInterfaceCapabilitySpec
    endpoint: ApiInterfaceEndpointSpec

    @property
    def capability_ref(self) -> str:
        return _capability_ref(self.api.name, self.capability.name)

    @property
    def endpoint_ref(self) -> str:
        return _endpoint_ref(self.api.name, self.capability.name, self.endpoint.name)


@dataclass(frozen=True, slots=True)
class ApiInterfaceIndex:
    spec: ApiInterfaceSpec
    apis_by_name: Mapping[str, ApiInterfaceApiSpec]
    capabilities_by_ref: Mapping[str, ApiInterfaceCapabilityBinding]
    endpoints_by_ref: Mapping[str, ApiInterfaceEndpointBinding]
    endpoints_by_discriminant: Mapping[str, ApiInterfaceEndpointBinding]

    def get_api(self, api_name: str) -> ApiInterfaceApiSpec | None:
        return self.apis_by_name.get(api_name)

    def require_api(self, api_name: str) -> ApiInterfaceApiSpec:
        api = self.get_api(api_name)
        if api is None:
            raise KeyError(f"Unknown API '{api_name}'.")
        return api

    def get_capability(
        self,
        api_name: str,
        capability_name: str,
    ) -> ApiInterfaceCapabilityBinding | None:
        return self.capabilities_by_ref.get(_capability_ref(api_name, capability_name))

    def require_capability(
        self,
        api_name: str,
        capability_name: str,
    ) -> ApiInterfaceCapabilityBinding:
        capability = self.get_capability(api_name, capability_name)
        if capability is None:
            raise KeyError(f"Unknown capability '{api_name}.{capability_name}'.")
        return capability

    def get_endpoint(
        self,
        api_name: str,
        capability_name: str,
        endpoint_name: str,
    ) -> ApiInterfaceEndpointBinding | None:
        return self.endpoints_by_ref.get(_endpoint_ref(api_name, capability_name, endpoint_name))

    def require_endpoint(
        self,
        api_name: str,
        capability_name: str,
        endpoint_name: str,
    ) -> ApiInterfaceEndpointBinding:
        endpoint = self.get_endpoint(api_name, capability_name, endpoint_name)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint '{api_name}.{capability_name}.{endpoint_name}'.")
        return endpoint

    def get_endpoint_by_discriminant(self, discriminant: str) -> ApiInterfaceEndpointBinding | None:
        return self.endpoints_by_discriminant.get(discriminant)

    def require_endpoint_by_discriminant(self, discriminant: str) -> ApiInterfaceEndpointBinding:
        endpoint = self.get_endpoint_by_discriminant(discriminant)
        if endpoint is None:
            raise KeyError(f"Unknown endpoint discriminant '{discriminant}'.")
        return endpoint


@dataclass(frozen=True, slots=True)
class LoadedApiInterface:
    spec: ApiInterfaceSpec
    index: ApiInterfaceIndex
    hash_sha256: str
    source_path: Path | None = None


def load_api_interface_spec_file(path: str | Path) -> LoadedApiInterface:
    source_path = Path(path).expanduser().resolve()
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    return load_api_interface_spec_payload(payload, source_path=source_path)


def load_api_interface_spec_json(
    data: str | bytes,
    *,
    source_path: str | Path | None = None,
) -> LoadedApiInterface:
    payload = json.loads(data)
    return load_api_interface_spec_payload(payload, source_path=source_path)


def load_api_interface_spec_payload(
    payload: Any,
    *,
    source_path: str | Path | None = None,
) -> LoadedApiInterface:
    if not isinstance(payload, dict):
        raise ValueError("ApiInterfaceSpec payload must be a JSON object.")

    spec = ApiInterfaceSpec.model_validate(payload)
    _validate_spec(spec)
    index = build_api_interface_index(spec)
    canonical_payload = spec.model_dump(mode="json", exclude_none=True)
    digest = sha256(
        json.dumps(
            canonical_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return LoadedApiInterface(
        spec=spec,
        index=index,
        hash_sha256=digest,
        source_path=_normalize_source_path(source_path),
    )


def build_api_interface_index(spec: ApiInterfaceSpec) -> ApiInterfaceIndex:
    _validate_spec(spec)

    apis_by_name: dict[str, ApiInterfaceApiSpec] = {}
    capabilities_by_ref: dict[str, ApiInterfaceCapabilityBinding] = {}
    endpoints_by_ref: dict[str, ApiInterfaceEndpointBinding] = {}
    endpoints_by_discriminant: dict[str, ApiInterfaceEndpointBinding] = {}

    for api in spec.apis:
        api_name = _validated_key("api.name", api.name)
        if api_name in apis_by_name:
            raise ValueError(f"Duplicate API name '{api_name}'.")
        apis_by_name[api_name] = api

        capability_names: set[str] = set()
        for capability in api.capabilities:
            capability_name = _validated_key(
                f"capability.name[{api_name}]",
                capability.name,
            )
            if capability_name in capability_names:
                raise ValueError(f"Duplicate capability name '{api_name}.{capability_name}'.")
            capability_names.add(capability_name)

            capability_binding = ApiInterfaceCapabilityBinding(api=api, capability=capability)
            capability_ref = capability_binding.capability_ref
            if capability_ref in capabilities_by_ref:
                raise ValueError(f"Duplicate capability ref '{capability_ref}'.")
            capabilities_by_ref[capability_ref] = capability_binding

            endpoint_names: set[str] = set()
            for endpoint in capability.endpoints:
                endpoint_name = _validated_key(
                    f"endpoint.name[{capability_ref}]",
                    endpoint.name,
                )
                if endpoint_name in endpoint_names:
                    raise ValueError(f"Duplicate endpoint name '{capability_ref}.{endpoint_name}'.")
                endpoint_names.add(endpoint_name)

                endpoint_binding = ApiInterfaceEndpointBinding(
                    api=api,
                    capability=capability,
                    endpoint=endpoint,
                )
                endpoint_ref = endpoint_binding.endpoint_ref
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

    return ApiInterfaceIndex(
        spec=spec,
        apis_by_name=MappingProxyType(dict(apis_by_name)),
        capabilities_by_ref=MappingProxyType(dict(capabilities_by_ref)),
        endpoints_by_ref=MappingProxyType(dict(endpoints_by_ref)),
        endpoints_by_discriminant=MappingProxyType(dict(endpoints_by_discriminant)),
    )


def _validate_spec(spec: ApiInterfaceSpec) -> None:
    if spec.schema_version not in SUPPORTED_API_INTERFACE_SCHEMA_VERSIONS:
        raise ValueError(
            "Unsupported ApiInterfaceSpec schema_version "
            f"{spec.schema_version!r}; supported={sorted(SUPPORTED_API_INTERFACE_SCHEMA_VERSIONS)}."
        )
    _validated_key("package_name", spec.package_name)
    _validated_key("fqn_prefix", spec.fqn_prefix)


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
    "ApiInterfaceApiSpec",
    "ApiInterfaceCapabilityBinding",
    "ApiInterfaceCapabilitySpec",
    "ApiInterfaceEndpointSpec",
    "ApiInterfaceEndpointBinding",
    "ApiInterfaceIndex",
    "ApiInterfaceRequestSpec",
    "ApiInterfaceResponseSpec",
    "ApiInterfaceSpec",
    "ApiInterfaceStreamEventSpec",
    "ApiInterfaceStreamSpec",
    "DEFAULT_API_INTERFACE_SPEC_FILENAME",
    "LoadedApiInterface",
    "build_api_interface_index",
    "load_api_interface_spec_file",
    "load_api_interface_spec_json",
    "load_api_interface_spec_payload",
]
