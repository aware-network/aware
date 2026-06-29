from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProjectionOwnedClassTruth:
    class_fqn: str
    attributes: frozenset[str]
    identity_key_attributes: frozenset[str]
    relationship_targets: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class BindingMapTruth:
    binding_ref: str
    source_graph: str
    target_graph: str
    source_class_ref: str
    target_class: str
    target_attribute: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APIGraphProjectionOwnership:
    target: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APIGraphCapabilityFunctionOwnership:
    name: str
    target: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APICapabilityEndpointStreamEventConfigOwnership:
    kind: str
    class_ref: str
    source_path: str
    class_config_id: UUID | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class APICapabilityEndpointStreamConfigOwnership:
    stream_mode: str
    source_path: str
    event_configs: tuple[APICapabilityEndpointStreamEventConfigOwnership, ...] = ()
    description: str | None = None


@dataclass(frozen=True, slots=True)
class APICapabilityEndpointResponseConfigOwnership:
    class_ref: str
    source_path: str
    class_config_id: UUID | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class APICapabilityEndpointRequestConfigOwnership:
    class_ref: str
    source_path: str
    class_config_id: UUID | None = None
    response_config: APICapabilityEndpointResponseConfigOwnership | None = None
    stream_config: APICapabilityEndpointStreamConfigOwnership | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class APICapabilityEndpointFunctionOwnership:
    name: str
    graph_target: str
    graph_capability_function_name: str
    source_path: str


@dataclass(frozen=True, slots=True)
class APIGraphCapabilityOwnership:
    capability_name: str
    source_path: str
    functions: tuple[APIGraphCapabilityFunctionOwnership, ...]


@dataclass(frozen=True, slots=True)
class APIGraphOwnership:
    target: str
    source_path: str
    projections: tuple[APIGraphProjectionOwnership, ...]
    capabilities: tuple[APIGraphCapabilityOwnership, ...]


@dataclass(frozen=True, slots=True)
class APICapabilityEndpointOwnership:
    name: str
    source_path: str
    request_config: APICapabilityEndpointRequestConfigOwnership
    functions: tuple[APICapabilityEndpointFunctionOwnership, ...] = ()
    description: str | None = None


@dataclass(frozen=True, slots=True)
class APICapabilityOwnership:
    name: str
    source_path: str
    endpoints: tuple[APICapabilityEndpointOwnership, ...]
    description: str | None = None


@dataclass(frozen=True, slots=True)
class APIOwnership:
    name: str
    source_path: str
    capabilities: tuple[APICapabilityOwnership, ...]
    graphs: tuple[APIGraphOwnership, ...]
