from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import keyword
import re

from aware_experience.materialization.service import (
    ActuatorConfigMaterializationSpec,
    ConnectorConfigMaterializationSpec,
    ConnectorInvocationActionConfigMaterializationSpec,
    ConnectorProviderMaterializationSpec,
    SensorConfigMaterializationSpec,
)
from aware_utils.string_transform import to_pascal_case, to_snake_case


CONNECTOR_PROTOCOL_PLAN_CONTRACT_VERSION = "aware.experience.connector-protocol-plan.v1"
CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION = (
    "aware.experience.connector-protocol-section-text-manifest.v1"
)
CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME = (
    "CONNECTOR_PROTOCOL_RENDER_SECTION_MANIFEST_JSON"
)


@dataclass(frozen=True, slots=True)
class ConnectorProtocolEndpointContractPlan:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConnectorProtocolProviderPlan:
    provider_key: str
    provider_kind: str
    provider_ref: str | None
    label: str | None
    description: str | None
    source_path: str


@dataclass(frozen=True, slots=True)
class ConnectorProtocolInvocationPlan:
    connector_key: str
    surface_kind: str
    surface_key: str
    action_key: str
    action_kind: str
    target_ref: str
    materialized_action_key: str
    label: str | None
    receipt_policy: str | None
    confirmation_policy: str | None
    optimistic_policy: str | None
    source_path: str
    endpoint_contract: ConnectorProtocolEndpointContractPlan | None = None

    @property
    def method_name(self) -> str:
        return _safe_python_identifier(self.action_key)

    @property
    def invoke_function_name(self) -> str:
        return "invoke_" + "__".join(
            _safe_python_identifier(token)
            for token in (
                self.connector_key,
                self.surface_kind,
                self.surface_key,
                self.action_key,
            )
        )

    @property
    def binding_constant_name(self) -> str:
        return _constant_name(
            (
                self.connector_key,
                self.surface_kind,
                self.surface_key,
                self.action_key,
                "binding",
            )
        )

    @property
    def stream_invoke_function_name(self) -> str:
        return "stream_" + self.invoke_function_name


@dataclass(frozen=True, slots=True)
class ConnectorProtocolSurfacePlan:
    connector_key: str
    surface_kind: str
    surface_key: str
    config_kind: str
    surface_ref: str | None
    state_node_refs: tuple[str, ...]
    label: str | None
    description: str | None
    source_path: str
    invocation_actions: tuple[ConnectorProtocolInvocationPlan, ...]

    @property
    def protocol_class_name(self) -> str:
        return _class_name(
            (
                self.connector_key,
                self.surface_key,
                self.surface_kind,
                "protocol",
            )
        )

    @property
    def root_property_name(self) -> str:
        return _safe_python_identifier(f"{self.surface_kind}_{self.surface_key}")

    @property
    def world_role(self) -> str:
        if self.surface_kind == "sensor":
            return "client"
        return "handler"


@dataclass(frozen=True, slots=True)
class ConnectorProtocolConnectorPlan:
    connector_key: str
    connector_kind: str
    projection_experience_name: str
    projection_key: str
    label: str | None
    description: str | None
    source_path: str
    providers: tuple[ConnectorProtocolProviderPlan, ...]
    sensor_surfaces: tuple[ConnectorProtocolSurfacePlan, ...]
    actuator_surfaces: tuple[ConnectorProtocolSurfacePlan, ...]

    @property
    def protocol_class_name(self) -> str:
        return _class_name((self.connector_key, "connector", "protocol"))

    @property
    def all_surfaces(self) -> tuple[ConnectorProtocolSurfacePlan, ...]:
        return (*self.sensor_surfaces, *self.actuator_surfaces)

    @property
    def all_invocation_actions(self) -> tuple[ConnectorProtocolInvocationPlan, ...]:
        return tuple(
            invocation
            for surface in self.all_surfaces
            for invocation in surface.invocation_actions
        )


@dataclass(frozen=True, slots=True)
class ConnectorProtocolPlan:
    package_name: str
    fqn_prefix: str
    connectors: tuple[ConnectorProtocolConnectorPlan, ...]
    contract_version: str = CONNECTOR_PROTOCOL_PLAN_CONTRACT_VERSION

    @property
    def invocation_count(self) -> int:
        return sum(
            len(connector.all_invocation_actions) for connector in self.connectors
        )


@dataclass(frozen=True, slots=True)
class PythonConnectorProtocolRenderSection:
    section_kind: str
    section_key: str
    lines: tuple[str, ...]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def rendered_text_digest(self) -> str:
        return _stable_section_text_digest(text=self.text)


def build_connector_protocol_plan(
    *,
    package_name: str,
    fqn_prefix: str,
    specs: Sequence[ConnectorConfigMaterializationSpec],
    endpoint_bindings: Mapping[str, object] | None = None,
) -> ConnectorProtocolPlan:
    resolved_endpoint_bindings = endpoint_bindings or {}
    connectors = tuple(
        _connector_plan_from_spec(
            spec,
            endpoint_bindings=resolved_endpoint_bindings,
        )
        for spec in sorted(
            specs,
            key=lambda item: (item.connector_key.casefold(), item.source_path),
        )
    )
    return ConnectorProtocolPlan(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        connectors=connectors,
    )


def endpoint_contract_from_service_protocol_binding(
    binding: object,
    *,
    reject_graph_fulfillment: bool = True,
) -> ConnectorProtocolEndpointContractPlan:
    fulfillment_bindings = tuple(getattr(binding, "fulfillment_bindings", ()) or ())
    if reject_graph_fulfillment and fulfillment_bindings:
        endpoint_ref = str(getattr(binding, "endpoint_ref", "<unknown>"))
        raise ValueError(
            "World-profile endpoint metadata must not carry graph fulfillment "
            f"bindings: endpoint_ref={endpoint_ref!r}"
        )
    return ConnectorProtocolEndpointContractPlan(
        endpoint_ref=str(getattr(binding, "endpoint_ref")),
        api_name=str(getattr(binding, "api_name")),
        capability_name=str(getattr(binding, "capability_name")),
        endpoint_name=str(getattr(binding, "endpoint_name")),
        request_type_ref=str(getattr(binding, "request_type_ref")),
        response_type_ref=(
            None
            if getattr(binding, "response_type_ref") is None
            else str(getattr(binding, "response_type_ref"))
        ),
        stream_event_type_refs=tuple(
            str(item) for item in getattr(binding, "stream_event_type_refs")
        ),
    )


def encode_connector_protocol_plan(
    *,
    plan: ConnectorProtocolPlan,
) -> dict[str, object]:
    return {
        "contract_version": plan.contract_version,
        "package_name": plan.package_name,
        "fqn_prefix": plan.fqn_prefix,
        "invocation_count": plan.invocation_count,
        "connectors": [
            {
                "connector_key": connector.connector_key,
                "connector_kind": connector.connector_kind,
                "projection_experience_name": (connector.projection_experience_name),
                "projection_key": connector.projection_key,
                "label": connector.label,
                "description": connector.description,
                "source_path": connector.source_path,
                "providers": [
                    {
                        "provider_key": provider.provider_key,
                        "provider_kind": provider.provider_kind,
                        "provider_ref": provider.provider_ref,
                        "label": provider.label,
                        "description": provider.description,
                        "source_path": provider.source_path,
                    }
                    for provider in connector.providers
                ],
                "sensor_surfaces": [
                    _encode_surface_plan(surface=surface)
                    for surface in connector.sensor_surfaces
                ],
                "actuator_surfaces": [
                    _encode_surface_plan(surface=surface)
                    for surface in connector.actuator_surfaces
                ],
            }
            for connector in plan.connectors
        ],
    }


def render_python_connector_protocol_module(
    *,
    plan: ConnectorProtocolPlan,
) -> str:
    return "\n".join(
        line
        for section in render_python_connector_protocol_sections(plan=plan)
        for line in section.lines
    )


def build_python_connector_protocol_section_text_manifest(
    *,
    sections: tuple[PythonConnectorProtocolRenderSection, ...],
    target_relpath: str = "protocols.py",
) -> dict[str, object]:
    described_sections_text = "\n".join(
        line for section in sections for line in section.lines
    )
    return {
        "contract_version": (CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION),
        "manifest_kind": "connector_protocol_section_text_manifest",
        "renderer_key": "PythonConnectorProtocolRenderer",
        "target_relpath": target_relpath,
        "text_digest_algorithm": "sha256",
        "manifest_digests_cover_manifest_section": False,
        "section_count": len(sections),
        "described_sections_text_digest": _stable_section_text_digest(
            text=described_sections_text,
        ),
        "sections": [
            {
                "section_order": index,
                "section_key": section.section_key,
                "section_kind": section.section_kind,
                "line_count": len(section.lines),
                "rendered_text_digest": section.rendered_text_digest,
            }
            for index, section in enumerate(sections)
        ],
    }


def render_python_connector_protocol_sections(
    *,
    plan: ConnectorProtocolPlan,
) -> tuple[PythonConnectorProtocolRenderSection, ...]:
    sections: list[PythonConnectorProtocolRenderSection] = []

    def append_section(
        *,
        section_kind: str,
        section_key: str,
        lines: list[str],
    ) -> None:
        sections.append(
            PythonConnectorProtocolRenderSection(
                section_kind=section_kind,
                section_key=section_key,
                lines=tuple(lines),
            )
        )

    append_section(
        section_kind="connector_protocol_module_prelude",
        section_key="experience.connector_protocol.module_prelude",
        lines=_render_module_prelude_lines(plan=plan),
    )
    append_section(
        section_kind="connector_protocol_runtime_support",
        section_key="experience.connector_protocol.runtime_support",
        lines=_render_runtime_support_lines(),
    )
    for connector in plan.connectors:
        append_section(
            section_kind="connector_protocol_connector_surface",
            section_key=(
                "experience.connector_protocol.connector:" + connector.connector_key
            ),
            lines=_render_connector_protocol_lines(connector=connector),
        )
    append_section(
        section_kind="connector_protocol_binding_registry",
        section_key="experience.connector_protocol.binding_registry",
        lines=_render_binding_registry_lines(plan=plan),
    )
    export_section = PythonConnectorProtocolRenderSection(
        section_kind="connector_protocol_module_exports",
        section_key="experience.connector_protocol.__all__",
        lines=tuple(_render_export_lines(plan=plan)),
    )
    append_section(
        section_kind="connector_protocol_section_text_manifest",
        section_key="experience.connector_protocol.section_text_manifest",
        lines=_render_section_text_manifest_lines(
            sections=(*sections, export_section),
        ),
    )
    sections.append(export_section)
    return tuple(sections)


def _connector_plan_from_spec(
    spec: ConnectorConfigMaterializationSpec,
    *,
    endpoint_bindings: Mapping[str, object],
) -> ConnectorProtocolConnectorPlan:
    return ConnectorProtocolConnectorPlan(
        connector_key=spec.connector_key,
        connector_kind=spec.connector_kind,
        projection_experience_name=spec.projection_experience_name,
        projection_key=spec.projection_key,
        label=spec.label,
        description=spec.description,
        source_path=spec.source_path,
        providers=tuple(
            _provider_plan_from_spec(provider=provider)
            for provider in sorted(
                spec.providers,
                key=lambda item: (item.provider_key.casefold(), item.source_path),
            )
        ),
        sensor_surfaces=tuple(
            _sensor_surface_plan_from_spec(
                connector_key=spec.connector_key,
                sensor=sensor,
                endpoint_bindings=endpoint_bindings,
            )
            for sensor in sorted(
                spec.sensor_configs,
                key=lambda item: (item.sensor_key.casefold(), item.source_path),
            )
        ),
        actuator_surfaces=tuple(
            _actuator_surface_plan_from_spec(
                connector_key=spec.connector_key,
                actuator=actuator,
                endpoint_bindings=endpoint_bindings,
            )
            for actuator in sorted(
                spec.actuator_configs,
                key=lambda item: (item.actuator_key.casefold(), item.source_path),
            )
        ),
    )


def _provider_plan_from_spec(
    *,
    provider: ConnectorProviderMaterializationSpec,
) -> ConnectorProtocolProviderPlan:
    return ConnectorProtocolProviderPlan(
        provider_key=provider.provider_key,
        provider_kind=provider.provider_kind,
        provider_ref=provider.provider_ref,
        label=provider.label,
        description=provider.description,
        source_path=provider.source_path,
    )


def _sensor_surface_plan_from_spec(
    *,
    connector_key: str,
    sensor: SensorConfigMaterializationSpec,
    endpoint_bindings: Mapping[str, object],
) -> ConnectorProtocolSurfacePlan:
    return ConnectorProtocolSurfacePlan(
        connector_key=connector_key,
        surface_kind="sensor",
        surface_key=sensor.sensor_key,
        config_kind=sensor.sensor_kind,
        surface_ref=sensor.source_ref,
        state_node_refs=sensor.observed_state_node_refs,
        label=sensor.label,
        description=sensor.description,
        source_path=sensor.source_path,
        invocation_actions=tuple(
            _invocation_plan_from_spec(
                connector_key=connector_key,
                surface_kind="sensor",
                surface_key=sensor.sensor_key,
                invocation=invocation,
                endpoint_bindings=endpoint_bindings,
            )
            for invocation in sorted(
                sensor.invocation_action_configs,
                key=lambda item: (item.action_key.casefold(), item.source_path),
            )
        ),
    )


def _actuator_surface_plan_from_spec(
    *,
    connector_key: str,
    actuator: ActuatorConfigMaterializationSpec,
    endpoint_bindings: Mapping[str, object],
) -> ConnectorProtocolSurfacePlan:
    return ConnectorProtocolSurfacePlan(
        connector_key=connector_key,
        surface_kind="actuator",
        surface_key=actuator.actuator_key,
        config_kind=actuator.actuator_kind,
        surface_ref=actuator.target_ref,
        state_node_refs=actuator.affected_state_node_refs,
        label=actuator.label,
        description=actuator.description,
        source_path=actuator.source_path,
        invocation_actions=tuple(
            _invocation_plan_from_spec(
                connector_key=connector_key,
                surface_kind="actuator",
                surface_key=actuator.actuator_key,
                invocation=invocation,
                endpoint_bindings=endpoint_bindings,
            )
            for invocation in sorted(
                actuator.invocation_action_configs,
                key=lambda item: (item.action_key.casefold(), item.source_path),
            )
        ),
    )


def _invocation_plan_from_spec(
    *,
    connector_key: str,
    surface_kind: str,
    surface_key: str,
    invocation: ConnectorInvocationActionConfigMaterializationSpec,
    endpoint_bindings: Mapping[str, object],
) -> ConnectorProtocolInvocationPlan:
    endpoint_contract: ConnectorProtocolEndpointContractPlan | None = None
    if invocation.action_kind == "api":
        endpoint_binding = endpoint_bindings.get(invocation.target_ref)
        if endpoint_binding is not None:
            endpoint_contract = endpoint_contract_from_service_protocol_binding(
                endpoint_binding
            )
    return ConnectorProtocolInvocationPlan(
        connector_key=connector_key,
        surface_kind=surface_kind,
        surface_key=surface_key,
        action_key=invocation.action_key,
        action_kind=invocation.action_kind,
        target_ref=invocation.target_ref,
        materialized_action_key=invocation.materialized_action_key,
        label=invocation.label,
        receipt_policy=invocation.receipt_policy,
        confirmation_policy=invocation.confirmation_policy,
        optimistic_policy=invocation.optimistic_policy,
        source_path=invocation.source_path,
        endpoint_contract=endpoint_contract,
    )


def _encode_surface_plan(
    *,
    surface: ConnectorProtocolSurfacePlan,
) -> dict[str, object]:
    return {
        "connector_key": surface.connector_key,
        "surface_kind": surface.surface_kind,
        "surface_key": surface.surface_key,
        "config_kind": surface.config_kind,
        "surface_ref": surface.surface_ref,
        "state_node_refs": list(surface.state_node_refs),
        "label": surface.label,
        "description": surface.description,
        "source_path": surface.source_path,
        "invocation_actions": [
            {
                "connector_key": invocation.connector_key,
                "surface_kind": invocation.surface_kind,
                "surface_key": invocation.surface_key,
                "action_key": invocation.action_key,
                "action_kind": invocation.action_kind,
                "target_ref": invocation.target_ref,
                "materialized_action_key": (invocation.materialized_action_key),
                "label": invocation.label,
                "receipt_policy": invocation.receipt_policy,
                "confirmation_policy": invocation.confirmation_policy,
                "optimistic_policy": invocation.optimistic_policy,
                "source_path": invocation.source_path,
                "endpoint_contract": _encode_endpoint_contract_plan(
                    endpoint_contract=invocation.endpoint_contract,
                ),
            }
            for invocation in surface.invocation_actions
        ],
    }


def _encode_endpoint_contract_plan(
    *,
    endpoint_contract: ConnectorProtocolEndpointContractPlan | None,
) -> dict[str, object] | None:
    if endpoint_contract is None:
        return None
    return {
        "endpoint_ref": endpoint_contract.endpoint_ref,
        "api_name": endpoint_contract.api_name,
        "capability_name": endpoint_contract.capability_name,
        "endpoint_name": endpoint_contract.endpoint_name,
        "request_type_ref": endpoint_contract.request_type_ref,
        "response_type_ref": endpoint_contract.response_type_ref,
        "stream_event_type_refs": list(endpoint_contract.stream_event_type_refs),
    }


def _render_module_prelude_lines(
    *,
    plan: ConnectorProtocolPlan,
) -> list[str]:
    type_checking_imports = _type_checking_import_modules(plan=plan)
    typing_imports = ["Final", "Protocol", "TypeAlias", "cast"]
    if type_checking_imports:
        typing_imports.insert(0, "TYPE_CHECKING")
    return [
        "# GENERATED CODE - DO NOT MODIFY BY HAND",
        "# Compiled Experience connector world-service profile package.",
        "# fmt: off",
        "from __future__ import annotations",
        "",
        "from collections.abc import AsyncIterator, Awaitable, Callable",
        "from dataclasses import dataclass",
        "from typing import " + ", ".join(typing_imports),
        "",
        "from pydantic import BaseModel",
        "",
        *(
            [
                "if TYPE_CHECKING:",
                *(f"    import {module_ref}" for module_ref in type_checking_imports),
                "",
            ]
            if type_checking_imports
            else []
        ),
        f"CONNECTOR_PROTOCOL_PACKAGE_NAME: Final[str] = {plan.package_name!r}",
        f"CONNECTOR_PROTOCOL_FQN_PREFIX: Final[str] = {plan.fqn_prefix!r}",
        (
            "CONNECTOR_PROTOCOL_CONTRACT_VERSION: Final[str] = "
            + f"{plan.contract_version!r}"
        ),
        "",
    ]


def _type_checking_import_modules(*, plan: ConnectorProtocolPlan) -> tuple[str, ...]:
    module_refs: set[str] = set()
    for connector in plan.connectors:
        for invocation in connector.all_invocation_actions:
            endpoint_contract = invocation.endpoint_contract
            if endpoint_contract is None:
                continue
            for type_ref in (
                endpoint_contract.request_type_ref,
                endpoint_contract.response_type_ref,
                *endpoint_contract.stream_event_type_refs,
            ):
                module_ref = _module_ref_for_type_ref(type_ref)
                if module_ref:
                    module_refs.add(module_ref)
    return tuple(sorted(module_refs))


def _module_ref_for_type_ref(type_ref: str | None) -> str:
    if type_ref is None:
        return ""
    parts = [part for part in type_ref.split(".") if part]
    if len(parts) < 2:
        return ""
    module_ref = ".".join(parts[:-1])
    if not re.fullmatch(
        r"[A-Za-z_][0-9A-Za-z_]*(\.[A-Za-z_][0-9A-Za-z_]*)+", module_ref
    ):
        return ""
    return module_ref


def _render_runtime_support_lines() -> list[str]:
    lines = [
        "@dataclass(frozen=True, slots=True)",
        "class ConnectorProviderBinding:",
        "    connector_key: str",
        "    provider_key: str",
        "    provider_kind: str",
        "    provider_ref: str | None",
        "    label: str | None",
        "    description: str | None",
        "",
        (
            "WorldServiceEndpointInvoker: TypeAlias = Callable[[object, "
            "BaseModel], Awaitable[object | None]]"
        ),
        (
            "WorldServiceEndpointStreamInvoker: TypeAlias = Callable[[object, "
            "BaseModel], AsyncIterator[object]]"
        ),
        "",
        "@dataclass(frozen=True, slots=True)",
        "class WorldServiceEndpointBinding:",
        "    connector_key: str",
        "    surface_kind: str",
        "    surface_key: str",
        "    action_key: str",
        "    role: str",
        "    endpoint_ref: str",
        "    api_name: str",
        "    capability_name: str",
        "    endpoint_name: str",
        "    request_type_ref: str",
        "    response_type_ref: str | None",
        "    stream_event_type_refs: tuple[str, ...]",
        "    materialized_action_key: str",
        "    state_node_refs: tuple[str, ...]",
        "    receipt_policy: str | None",
        "    confirmation_policy: str | None",
        "    optimistic_policy: str | None",
        "    invoke: WorldServiceEndpointInvoker",
        "    stream_invoke: WorldServiceEndpointStreamInvoker | None",
        "",
    ]
    return lines


def _render_connector_protocol_lines(
    *,
    connector: ConnectorProtocolConnectorPlan,
) -> list[str]:
    lines: list[str] = []
    for surface in connector.all_surfaces:
        lines.extend(_render_surface_protocol_class(surface=surface))
        lines.append("")
    lines.append(f"class {connector.protocol_class_name}(Protocol):")
    if not connector.all_surfaces:
        lines.append("    pass")
    for surface in connector.all_surfaces:
        lines.append("")
        lines.append("    @property")
        lines.append(
            f"    def {surface.root_property_name}(self) "
            + f"-> {surface.protocol_class_name}: ..."
        )
    lines.append("")
    for surface in connector.all_surfaces:
        for invocation in surface.invocation_actions:
            lines.extend(
                _render_invocation_function_lines(
                    connector=connector,
                    surface=surface,
                    invocation=invocation,
                )
            )
            lines.append("")
    return lines


def _render_surface_protocol_class(
    *,
    surface: ConnectorProtocolSurfacePlan,
) -> list[str]:
    lines = [f"class {surface.protocol_class_name}(Protocol):"]
    if not surface.invocation_actions:
        lines.append("    pass")
        return lines
    for invocation in surface.invocation_actions:
        endpoint_contract = _require_world_endpoint_contract(invocation=invocation)
        request_annotation = _type_annotation(endpoint_contract.request_type_ref)
        response_annotation = _type_annotation(
            endpoint_contract.response_type_ref,
            none_annotation="None",
        )
        lines.append("")
        lines.append(
            f"    async def {invocation.method_name}("
            + f"self, request: {request_annotation}) "
            + f"-> {response_annotation}: ..."
        )
        if endpoint_contract.stream_event_type_refs:
            stream_annotation = _stream_event_annotation(
                endpoint_contract=endpoint_contract,
            )
            lines.append("")
            lines.append(
                f"    def stream_{invocation.method_name}("
                + f"self, request: {request_annotation}) "
                + f"-> AsyncIterator[{stream_annotation}]: ..."
            )
    return lines


def _render_invocation_function_lines(
    *,
    connector: ConnectorProtocolConnectorPlan,
    surface: ConnectorProtocolSurfacePlan,
    invocation: ConnectorProtocolInvocationPlan,
) -> list[str]:
    endpoint_contract = _require_world_endpoint_contract(invocation=invocation)
    response_annotation = _type_annotation(
        endpoint_contract.response_type_ref,
        none_annotation="None",
    )
    lines = [
        f"async def {invocation.invoke_function_name}(",
        "    handler: object,",
        "    request: BaseModel,",
        f") -> {response_annotation}:",
        f"    typed_handler = cast({connector.protocol_class_name}, handler)",
        (
            f"    return await typed_handler.{surface.root_property_name}."
            + f"{invocation.method_name}(request)"
        ),
    ]
    if endpoint_contract.stream_event_type_refs:
        stream_annotation = _stream_event_annotation(
            endpoint_contract=endpoint_contract,
        )
        lines.extend(
            [
                "",
                f"def {invocation.stream_invoke_function_name}(",
                "    handler: object,",
                "    request: BaseModel,",
                f") -> AsyncIterator[{stream_annotation}]:",
                f"    typed_handler = cast({connector.protocol_class_name}, handler)",
                (
                    f"    return typed_handler.{surface.root_property_name}."
                    + f"stream_{invocation.method_name}(request)"
                ),
            ]
        )
    return lines


def _render_binding_registry_lines(
    *,
    plan: ConnectorProtocolPlan,
) -> list[str]:
    lines: list[str] = []
    provider_entries: list[tuple[str, str]] = []
    for connector in plan.connectors:
        for provider in connector.providers:
            constant_name = _constant_name(
                (
                    connector.connector_key,
                    "provider",
                    provider.provider_key,
                    "binding",
                )
            )
            provider_entries.append(
                (f"{connector.connector_key}.{provider.provider_key}", constant_name)
            )
            lines.append(f"{constant_name}: Final[ConnectorProviderBinding] = (")
            lines.append("    ConnectorProviderBinding(")
            lines.append(f"        connector_key={connector.connector_key!r},")
            lines.append(f"        provider_key={provider.provider_key!r},")
            lines.append(f"        provider_kind={provider.provider_kind!r},")
            lines.append(f"        provider_ref={provider.provider_ref!r},")
            lines.append(f"        label={provider.label!r},")
            lines.append(f"        description={provider.description!r},")
            lines.append("    )")
            lines.append(")")
            lines.append("")

    endpoint_entries: list[tuple[str, str]] = []
    for connector in plan.connectors:
        for surface in connector.all_surfaces:
            for invocation in surface.invocation_actions:
                endpoint_entries.append(
                    (
                        invocation.materialized_action_key,
                        invocation.binding_constant_name,
                    )
                )
                lines.extend(
                    _render_invocation_binding_lines(
                        surface=surface,
                        invocation=invocation,
                    )
                )
                lines.append("")

    lines.append(
        "CONNECTOR_PROVIDER_BINDINGS: Final[dict[str, "
        + "ConnectorProviderBinding]] = {"
    )
    for binding_key, constant_name in provider_entries:
        lines.append(f"    {binding_key!r}: {constant_name},")
    lines.append("}")
    lines.append("")
    lines.append(
        "WORLD_SERVICE_ENDPOINT_BINDINGS: Final[dict[str, "
        + "WorldServiceEndpointBinding]] = {"
    )
    for binding_key, constant_name in endpoint_entries:
        lines.append(f"    {binding_key!r}: {constant_name},")
    lines.append("}")
    lines.append("")
    return lines


def _render_invocation_binding_lines(
    *,
    surface: ConnectorProtocolSurfacePlan,
    invocation: ConnectorProtocolInvocationPlan,
) -> list[str]:
    endpoint_contract = _require_world_endpoint_contract(invocation=invocation)
    return [
        (
            f"{invocation.binding_constant_name}: "
            "Final[WorldServiceEndpointBinding] = ("
        ),
        "    WorldServiceEndpointBinding(",
        f"        connector_key={invocation.connector_key!r},",
        f"        surface_kind={invocation.surface_kind!r},",
        f"        surface_key={invocation.surface_key!r},",
        f"        action_key={invocation.action_key!r},",
        f"        role={surface.world_role!r},",
        f"        endpoint_ref={endpoint_contract.endpoint_ref!r},",
        f"        api_name={endpoint_contract.api_name!r},",
        f"        capability_name={endpoint_contract.capability_name!r},",
        f"        endpoint_name={endpoint_contract.endpoint_name!r},",
        f"        request_type_ref={endpoint_contract.request_type_ref!r},",
        f"        response_type_ref={endpoint_contract.response_type_ref!r},",
        (
            "        stream_event_type_refs="
            + f"{endpoint_contract.stream_event_type_refs!r},"
        ),
        (
            "        materialized_action_key="
            + f"{invocation.materialized_action_key!r},"
        ),
        f"        state_node_refs={surface.state_node_refs!r},",
        f"        receipt_policy={invocation.receipt_policy!r},",
        f"        confirmation_policy={invocation.confirmation_policy!r},",
        f"        optimistic_policy={invocation.optimistic_policy!r},",
        f"        invoke={invocation.invoke_function_name},",
        (
            "        stream_invoke="
            + (
                invocation.stream_invoke_function_name
                if endpoint_contract.stream_event_type_refs
                else "None"
            )
            + ","
        ),
        "    )",
        ")",
    ]


def _render_export_lines(
    *,
    plan: ConnectorProtocolPlan,
) -> list[str]:
    names = {
        CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME,
        "CONNECTOR_PROVIDER_BINDINGS",
        "CONNECTOR_PROTOCOL_CONTRACT_VERSION",
        "CONNECTOR_PROTOCOL_FQN_PREFIX",
        "CONNECTOR_PROTOCOL_PACKAGE_NAME",
        "ConnectorProviderBinding",
        "WORLD_SERVICE_ENDPOINT_BINDINGS",
        "WorldServiceEndpointBinding",
        "WorldServiceEndpointInvoker",
        "WorldServiceEndpointStreamInvoker",
    }
    for connector in plan.connectors:
        names.add(connector.protocol_class_name)
        for surface in connector.all_surfaces:
            names.add(surface.protocol_class_name)
            for invocation in surface.invocation_actions:
                names.add(invocation.binding_constant_name)
                names.add(invocation.invoke_function_name)
                if invocation.endpoint_contract is not None and (
                    invocation.endpoint_contract.stream_event_type_refs
                ):
                    names.add(invocation.stream_invoke_function_name)
    lines = ["__all__ = ["]
    for name in sorted(names, key=str.casefold):
        lines.append(f"    {name!r},")
    lines.append("]")
    lines.append("")
    return lines


def _render_section_text_manifest_lines(
    *,
    sections: tuple[PythonConnectorProtocolRenderSection, ...],
) -> list[str]:
    manifest_json = json.dumps(
        build_python_connector_protocol_section_text_manifest(sections=sections),
        indent=2,
        sort_keys=True,
    )
    lines = [f"{CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME}: Final[str] = ("]
    for line in manifest_json.splitlines():
        lines.append(f"    {line!r}")
    lines.append(")")
    lines.append("")
    return lines


def _require_world_endpoint_contract(
    *,
    invocation: ConnectorProtocolInvocationPlan,
) -> ConnectorProtocolEndpointContractPlan:
    if invocation.action_kind != "api":
        raise ValueError(
            "World-profile connector invocations must target API endpoints: "
            f"action_key={invocation.materialized_action_key!r} "
            f"action_kind={invocation.action_kind!r}"
        )
    if invocation.endpoint_contract is None:
        raise ValueError(
            "World-profile connector invocation is missing generated "
            "ServiceProtocolEndpointBinding metadata: "
            f"action_key={invocation.materialized_action_key!r} "
            f"target_ref={invocation.target_ref!r}"
        )
    if invocation.endpoint_contract.endpoint_ref != invocation.target_ref:
        raise ValueError(
            "World-profile connector invocation target must match endpoint "
            "binding ref: "
            f"action_key={invocation.materialized_action_key!r} "
            f"target_ref={invocation.target_ref!r} "
            f"endpoint_ref={invocation.endpoint_contract.endpoint_ref!r}"
        )
    return invocation.endpoint_contract


def _type_annotation(
    type_ref: str | None,
    *,
    none_annotation: str = "None",
) -> str:
    if type_ref is None:
        return none_annotation
    return repr(type_ref)


def _stream_event_annotation(
    *,
    endpoint_contract: ConnectorProtocolEndpointContractPlan,
) -> str:
    event_refs = endpoint_contract.stream_event_type_refs
    if not event_refs:
        return "object"
    if len(event_refs) == 1:
        return repr(event_refs[0])
    return repr(" | ".join(event_refs))


def _stable_section_text_digest(
    *,
    text: str,
) -> str:
    return f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"


def _safe_python_identifier(value: str) -> str:
    candidate = to_snake_case(_slug_text(value)).strip("_")
    candidate = re.sub(r"[^0-9A-Za-z_]+", "_", candidate).strip("_")
    if not candidate:
        candidate = "value"
    if candidate[0].isdigit():
        candidate = f"_{candidate}"
    if keyword.iskeyword(candidate):
        candidate = f"{candidate}_"
    return candidate


def _class_name(tokens: Sequence[str]) -> str:
    candidate = "".join(to_pascal_case(_slug_text(token)) for token in tokens)
    candidate = re.sub(r"[^0-9A-Za-z]+", "", candidate)
    if not candidate:
        candidate = "ConnectorProtocol"
    if candidate[0].isdigit():
        candidate = f"_{candidate}"
    return candidate


def _constant_name(tokens: Sequence[str]) -> str:
    return "__".join(_safe_python_identifier(token).upper() for token in tokens)


def _slug_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", value)


__all__ = [
    "CONNECTOR_PROTOCOL_PLAN_CONTRACT_VERSION",
    "CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION",
    "CONNECTOR_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME",
    "ConnectorProtocolConnectorPlan",
    "ConnectorProtocolEndpointContractPlan",
    "ConnectorProtocolInvocationPlan",
    "ConnectorProtocolPlan",
    "ConnectorProtocolProviderPlan",
    "ConnectorProtocolSurfacePlan",
    "PythonConnectorProtocolRenderSection",
    "build_connector_protocol_plan",
    "build_python_connector_protocol_section_text_manifest",
    "encode_connector_protocol_plan",
    "endpoint_contract_from_service_protocol_binding",
    "render_python_connector_protocol_module",
    "render_python_connector_protocol_sections",
]
