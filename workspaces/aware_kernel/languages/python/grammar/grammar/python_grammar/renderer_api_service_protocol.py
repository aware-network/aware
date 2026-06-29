from __future__ import annotations

import json
import keyword
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from typing_extensions import override

from aware_code.section.writer import CodeSectionWriter
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
    build_renderer_empty_code,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_utils.string_transform import to_pascal_case, to_snake_case


API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION = (
    "aware.api.service-protocol-section-text-manifest.v1"
)
API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME = (
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON"
)


@dataclass(frozen=True)
class _PythonTypeBinding:
    class_ref: str
    class_name: str
    module_path: str


@dataclass(frozen=True)
class _ExternalPythonTypeBinding:
    class_name: str
    module_path: str
    type_ref: str


@dataclass(frozen=True)
class _FulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str | None = None
    request_model: _ExecutionModelBinding | None = None
    response_model: _ExecutionModelBinding | None = None


@dataclass(frozen=True)
class _ExecutionFieldBinding:
    name: str
    type_annotation: str
    default_expr: str | None
    description: str | None


@dataclass(frozen=True)
class _ExecutionModelBinding:
    class_name: str
    type_ref: str
    fields: tuple[_ExecutionFieldBinding, ...]
    imported_types: tuple[_PythonTypeBinding, ...]


@dataclass(frozen=True)
class _EndpointProtocolBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    description: str | None
    request: _PythonTypeBinding
    response: _PythonTypeBinding | None
    stream_events: tuple[_PythonTypeBinding, ...]
    fulfillment_bindings: tuple[_FulfillmentBinding, ...]

    @property
    def endpoint_constant_name(self) -> str:
        return _endpoint_constant_name(self.endpoint_ref)

    @property
    def binding_constant_name(self) -> str:
        return f"{self.endpoint_constant_name.removesuffix('_ENDPOINT_REF')}_PROTOCOL_BINDING"

    @property
    def stream_alias_name(self) -> str:
        return (
            f"{to_pascal_case(self.api_name)}"
            f"{to_pascal_case(self.capability_name)}"
            f"{to_pascal_case(self.endpoint_name)}StreamEvent"
        )

    @property
    def method_name(self) -> str:
        return _safe_python_identifier(self.endpoint_name)

    @property
    def stream_method_name(self) -> str:
        return f"stream_{self.method_name}"

    @property
    def execution_protocol_name(self) -> str:
        return _execution_protocol_name(
            api_name=self.api_name,
            capability_name=self.capability_name,
            endpoint_name=self.endpoint_name,
        )

    @property
    def execution_protocol_ref(self) -> str:
        return f"protocols.{self.execution_protocol_name}"

    @property
    def execution_factory_name(self) -> str:
        return (
            "build_"
            f"{_safe_python_identifier(self.api_name)}__"
            f"{_safe_python_identifier(self.capability_name)}__"
            f"{_safe_python_identifier(self.endpoint_name)}_execution"
        )

    @property
    def execution_impl_name(self) -> str:
        return f"_{self.execution_protocol_name}Impl"

    @property
    def invoke_function_name(self) -> str:
        return (
            "invoke_"
            f"{_safe_python_identifier(self.api_name)}__"
            f"{_safe_python_identifier(self.capability_name)}__"
            f"{_safe_python_identifier(self.endpoint_name)}"
        )

    @property
    def stream_invoke_function_name(self) -> str:
        return (
            "stream_invoke_"
            f"{_safe_python_identifier(self.api_name)}__"
            f"{_safe_python_identifier(self.capability_name)}__"
            f"{_safe_python_identifier(self.endpoint_name)}"
        )


@dataclass(frozen=True)
class PythonApiServiceProtocolRenderSection:
    section_kind: str
    section_key: str
    lines: tuple[str, ...]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @property
    def rendered_text_digest(self) -> str:
        return _stable_section_text_digest(text=self.text)


class PythonApiServiceProtocolRendererLanguage(ObjectConfigGraphRendererLanguage):
    """Emit compiled `protocols.py` for Python API service protocol packages."""

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy=layout_strategy)
        self._graph: ObjectConfigGraph | None = None
        self._external_type_bindings_by_identity: dict[str, _PythonTypeBinding] = {}
        self._class_configs_by_identity: dict[str, ClassConfig] = {}

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    @property
    @override
    def indent(self) -> int:
        return 4

    @property
    @override
    def comment_prefix(self) -> str:
        return "#"

    @override
    def define_assemblers(self) -> None:
        return

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        _ = policy

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        self._graph = graph
        self._external_type_bindings_by_identity = _build_external_type_binding_index(
            graph=graph,
            external_type_bindings_by_entity_id=_build_external_python_type_bindings_by_entity_id(
                payload=self.profile_inputs.get("api.external_python_type_index")
            ),
        )
        self._class_configs_by_identity = _build_class_config_index(graph=graph)

    @override
    def extra_output_paths(self) -> list[Path]:
        return [Path("protocols.py")]

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.python,
            renderer_key=type(self).__name__,
        )

    @override
    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name
        if meta_objects:
            return

        _ = writer.token("\n".join(line for section in self.render_sections() for line in section.lines))

    def render_sections(self) -> tuple[PythonApiServiceProtocolRenderSection, ...]:
        service_plan = self._require_payload("api.service_protocol_plan")
        public_plan = self._require_payload("api.public_package_plan")
        invocation_manifest = self._require_payload("api.invocation_manifest")
        interface_spec = self._require_payload("api.interface_spec")
        public_package_import_root = _derive_public_package_import_root(public_plan=public_plan)
        endpoint_bindings = _build_endpoint_bindings(
            service_plan=service_plan,
            public_plan=public_plan,
            invocation_manifest=invocation_manifest,
            interface_spec=interface_spec,
            public_package_import_root=public_package_import_root,
            external_type_bindings_by_identity=self._external_type_bindings_by_identity,
        )
        endpoint_bindings = _enrich_endpoint_bindings_with_execution(
            endpoint_bindings=endpoint_bindings,
            class_configs_by_identity=self._class_configs_by_identity,
            external_type_bindings_by_identity=self._external_type_bindings_by_identity,
            public_package_import_root=public_package_import_root,
        )
        return render_python_api_service_protocol_sections(
            service_package_import_root=self.layout_strategy.import_root,
            public_package_import_root=public_package_import_root,
            service_plan=service_plan,
            endpoint_bindings=endpoint_bindings,
        )

    def render_section_text_manifest(self) -> dict[str, object]:
        sections = tuple(
            section
            for section in self.render_sections()
            if section.section_key != "api.service_protocol.section_text_manifest"
        )
        return build_python_api_service_protocol_section_text_manifest(
            sections=sections,
        )

    def _require_payload(self, key: str) -> dict[str, object]:
        payload = self.profile_inputs.get(key)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected profile input {key!r} to be a JSON object.")
        return payload


def render_python_api_service_protocol_module(
    *,
    service_package_import_root: str | None,
    public_package_import_root: str,
    service_plan: dict[str, object],
    endpoint_bindings: tuple[_EndpointProtocolBinding, ...],
) -> str:
    sections = render_python_api_service_protocol_sections(
        service_package_import_root=service_package_import_root,
        public_package_import_root=public_package_import_root,
        service_plan=service_plan,
        endpoint_bindings=endpoint_bindings,
    )
    return "\n".join(line for section in sections for line in section.lines)


def build_python_api_service_protocol_section_text_manifest(
    *,
    sections: tuple[PythonApiServiceProtocolRenderSection, ...],
    target_relpath: str = "protocols.py",
) -> dict[str, object]:
    described_sections_text = "\n".join(
        line for section in sections for line in section.lines
    )
    return {
        "contract_version": (
            API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION
        ),
        "manifest_kind": "api_service_protocol_section_text_manifest",
        "renderer_key": "PythonApiServiceProtocolRendererLanguage",
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


def render_python_api_service_protocol_sections(
    *,
    service_package_import_root: str | None,
    public_package_import_root: str,
    service_plan: dict[str, object],
    endpoint_bindings: tuple[_EndpointProtocolBinding, ...],
) -> tuple[PythonApiServiceProtocolRenderSection, ...]:
    root_protocol_name = _root_service_protocol_name(import_root=service_package_import_root)
    api_package_name = _require_string(service_plan, "package_name")
    api_fqn_prefix = _require_string(service_plan, "fqn_prefix")

    type_bindings = _collect_imported_types(endpoint_bindings=endpoint_bindings)
    aware_type_imports = _collect_aware_type_imports(endpoint_bindings=endpoint_bindings)
    execution_models_for_imports = tuple(
        model
        for binding in endpoint_bindings
        for fulfillment in binding.fulfillment_bindings
        for model in (fulfillment.request_model, fulfillment.response_model)
        if model is not None
    )
    imports_by_module: dict[str, list[_PythonTypeBinding]] = {}
    for binding in type_bindings:
        imports_by_module.setdefault(binding.module_path, []).append(binding)

    by_api: dict[str, dict[str, list[_EndpointProtocolBinding]]] = {}
    for binding in endpoint_bindings:
        by_api.setdefault(binding.api_name, {}).setdefault(binding.capability_name, []).append(binding)

    sections: list[PythonApiServiceProtocolRenderSection] = []

    def append_section(
        *,
        section_kind: str,
        section_key: str,
        lines: list[str],
    ) -> None:
        sections.append(
            PythonApiServiceProtocolRenderSection(
                section_kind=section_kind,
                section_key=section_key,
                lines=tuple(lines),
            )
        )

    lines: list[str] = []
    lines.append("# GENERATED CODE - DO NOT MODIFY BY HAND")
    lines.append("# Compiled API service protocol package.")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from collections.abc import AsyncIterator, Awaitable, Callable")
    lines.append("from dataclasses import dataclass")
    typing_imports = ["Final", "Protocol", "TypeAlias", "cast"]
    if any(
        "Any" in field.type_annotation
        for model in execution_models_for_imports
        for field in model.fields
    ):
        typing_imports.insert(0, "Any")
    lines.append(f"from typing import {', '.join(typing_imports)}")
    if any(
        "UUID" in field.type_annotation
        for model in execution_models_for_imports
        for field in model.fields
    ):
        lines.append("from uuid import UUID")
    lines.append("")
    pydantic_imports = ["BaseModel"]
    if any(
        field.default_expr is not None and "Field(" in field.default_expr
        for model in execution_models_for_imports
        for field in model.fields
    ):
        pydantic_imports.append("Field")
    lines.append(f"from pydantic import {', '.join(pydantic_imports)}")
    if aware_type_imports:
        lines.append(f"from aware_types import {', '.join(aware_type_imports)}")
    lines.append("")

    for module_path in sorted(imports_by_module, key=str.casefold):
        class_names = sorted({binding.class_name for binding in imports_by_module[module_path]}, key=str.casefold)
        lines.append(f"from {module_path} import {', '.join(class_names)}")

    lines.append("")
    lines.append(f"API_PACKAGE_NAME: Final[str] = {api_package_name!r}")
    lines.append(f"API_FQN_PREFIX: Final[str] = {api_fqn_prefix!r}")
    lines.append(f"PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = {public_package_import_root!r}")
    lines.append("")
    append_section(
        section_kind="service_protocol_module_prelude",
        section_key="api.service_protocol.module_prelude",
        lines=lines,
    )

    lines = []
    lines.append("@dataclass(frozen=True, slots=True)")
    lines.append("class ServiceProtocolFulfillmentBinding:")
    lines.append("    name: str")
    lines.append("    graph_target: str")
    lines.append("    graph_capability_function_name: str")
    lines.append("    graph_function_python_ref: str")
    lines.append("    method_name: str")
    lines.append("    request_type_ref: str")
    lines.append("    response_type_ref: str")
    lines.append("")
    lines.append("class ServiceProtocolExecutionBackend(Protocol):")
    lines.append("    async def invoke_fulfillment(")
    lines.append("        self,")
    lines.append("        *,")
    lines.append("        fulfillment_name: str,")
    lines.append("        request: BaseModel,")
    lines.append("    ) -> object | None: ...")
    lines.append("")
    lines.append("class ServiceProtocolExecution(Protocol):")
    lines.append("    pass")
    lines.append("")
    lines.append(
        "ServiceProtocolExecutionFactory: TypeAlias = Callable["
        + "[ServiceProtocolExecutionBackend], "
        + "ServiceProtocolExecution"
        + "]"
    )
    lines.append("")
    lines.append(
        "ServiceProtocolInvoker: TypeAlias = Callable["
        + "[object, BaseModel, ServiceProtocolExecution | None], "
        + "Awaitable[object | None]"
        + "]"
    )
    lines.append("")
    lines.append(
        "ServiceProtocolStreamInvoker: TypeAlias = Callable["
        + "[object, BaseModel, ServiceProtocolExecution | None], "
        + "AsyncIterator[object]"
        + "]"
    )
    lines.append("")
    lines.append("def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:")
    lines.append("    if isinstance(value, BaseModel):")
    lines.append("        payload = value.model_dump(mode='json')")
    lines.append("    else:")
    lines.append("        payload = value")
    lines.append("    required_fields = [")
    lines.append("        name")
    lines.append("        for name, field in model_cls.model_fields.items()")
    lines.append("        if field.is_required()")
    lines.append("    ]")
    lines.append("    if len(required_fields) == 1:")
    lines.append("        field_name = required_fields[0]")
    lines.append("        if isinstance(payload, dict) and field_name in payload:")
    lines.append("            return payload")
    lines.append("        return {field_name: payload}")
    lines.append("    return payload")
    lines.append("")
    lines.append("@dataclass(frozen=True, slots=True)")
    lines.append("class ServiceProtocolEndpointBinding:")
    lines.append("    endpoint_ref: str")
    lines.append("    api_name: str")
    lines.append("    capability_name: str")
    lines.append("    endpoint_name: str")
    lines.append("    request_type_ref: str")
    lines.append("    response_type_ref: str | None")
    lines.append("    stream_event_type_refs: tuple[str, ...]")
    lines.append("    execution_protocol_ref: str | None")
    lines.append("    build_execution: ServiceProtocolExecutionFactory | None")
    lines.append("    stream_invoke: ServiceProtocolStreamInvoker | None")
    lines.append("    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]")
    lines.append("    invoke: ServiceProtocolInvoker")
    lines.append("")
    append_section(
        section_kind="service_protocol_runtime_support",
        section_key="api.service_protocol.runtime_support",
        lines=lines,
    )

    stream_alias_names: list[str] = []
    execution_model_names: list[str] = []
    execution_protocol_names: list[str] = []

    for binding in endpoint_bindings:
        lines = []
        for fulfillment in binding.fulfillment_bindings:
            if fulfillment.request_model is not None:
                execution_model_names.append(fulfillment.request_model.class_name)
                lines.extend(_render_execution_model(binding=fulfillment.request_model))
                lines.append("")
            if fulfillment.response_model is not None:
                execution_model_names.append(fulfillment.response_model.class_name)
                lines.extend(_render_execution_model(binding=fulfillment.response_model))
                lines.append("")
        if binding.fulfillment_bindings:
            execution_protocol_names.append(binding.execution_protocol_name)
            lines.extend(_render_execution_protocol_class(endpoint_binding=binding))
            lines.append("")
            lines.extend(_render_execution_implementation_class(endpoint_binding=binding))
            lines.append("")
        append_section(
            section_kind="service_protocol_endpoint_execution",
            section_key=_service_protocol_endpoint_section_key(
                section_name="endpoint_execution",
                endpoint_binding=binding,
            ),
            lines=lines,
        )

    for binding in endpoint_bindings:
        lines = []
        if binding.stream_events:
            stream_alias_names.append(binding.stream_alias_name)
            alias_targets = " | ".join(event.class_name for event in binding.stream_events)
            lines.append(f"{binding.stream_alias_name}: TypeAlias = {alias_targets}")
        response_annotation = binding.response.class_name if binding.response is not None else "None"
        lines.append(
            f"async def {binding.invoke_function_name}("
            + "handler: object, request: BaseModel, "
            + "execution: ServiceProtocolExecution | None = None) "
            + f"-> {response_annotation}:"
        )
        lines.append(
            f"    typed_handler = cast({root_protocol_name}, handler)"
        )
        lines.append(
            f"    typed_request = {binding.request.class_name}.model_validate(request)"
        )
        if binding.fulfillment_bindings:
            lines.append("    if execution is None:")
            lines.append(
                "        raise RuntimeError("
                + "\"Compiled API service protocol requires execution context "
                + f"for endpoint_ref={binding.endpoint_ref!r}\""
                + ")"
            )
            lines.append(
                f"    typed_execution = cast({binding.execution_protocol_name}, execution)"
            )
            lines.append(
                "    return await "
                + f"typed_handler.{_safe_python_identifier(binding.api_name)}."
                + f"{_safe_python_identifier(binding.capability_name)}."
                + f"{binding.method_name}(typed_request, typed_execution)"
            )
        else:
            lines.append(
                "    return await "
                + f"typed_handler.{_safe_python_identifier(binding.api_name)}."
                + f"{_safe_python_identifier(binding.capability_name)}."
                + f"{binding.method_name}(typed_request)"
            )
        if binding.stream_events:
            lines.append("")
            lines.append(
                f"def {binding.stream_invoke_function_name}("
                + "handler: object, request: BaseModel, "
                + "execution: ServiceProtocolExecution | None = None) "
                + f"-> AsyncIterator[{binding.stream_alias_name}]:"
            )
            lines.append(
                f"    typed_handler = cast({root_protocol_name}, handler)"
            )
            lines.append(
                f"    typed_request = {binding.request.class_name}.model_validate(request)"
            )
            if binding.fulfillment_bindings:
                lines.append("    if execution is None:")
                lines.append(
                    "        raise RuntimeError("
                    + "\"Compiled API service protocol requires execution context "
                    + f"for endpoint_ref={binding.endpoint_ref!r} stream\""
                    + ")"
                )
                lines.append(
                    f"    typed_execution = cast({binding.execution_protocol_name}, execution)"
                )
                lines.append(
                    "    return "
                    + f"typed_handler.{_safe_python_identifier(binding.api_name)}."
                    + f"{_safe_python_identifier(binding.capability_name)}."
                    + f"{binding.stream_method_name}(typed_request, typed_execution)"
                )
            else:
                lines.append("    _ = execution")
                lines.append(
                    "    return "
                    + f"typed_handler.{_safe_python_identifier(binding.api_name)}."
                    + f"{_safe_python_identifier(binding.capability_name)}."
                    + f"{binding.stream_method_name}(typed_request)"
                )
        lines.append("")
        append_section(
            section_kind="service_protocol_endpoint_invoker",
            section_key=_service_protocol_endpoint_section_key(
                section_name="endpoint_invoker",
                endpoint_binding=binding,
            ),
            lines=lines,
        )

        lines = []
        lines.append(f"{binding.endpoint_constant_name}: Final[str] = {binding.endpoint_ref!r}")
        lines.append(
            f"{binding.binding_constant_name}: Final[ServiceProtocolEndpointBinding] = "
            + "ServiceProtocolEndpointBinding("
        )
        lines.append(f"    endpoint_ref={binding.endpoint_constant_name},")
        lines.append(f"    api_name={binding.api_name!r},")
        lines.append(f"    capability_name={binding.capability_name!r},")
        lines.append(f"    endpoint_name={binding.endpoint_name!r},")
        lines.append(f"    request_type_ref={binding.request.class_ref!r},")
        if binding.response is None:
            lines.append("    response_type_ref=None,")
        else:
            lines.append(f"    response_type_ref={binding.response.class_ref!r},")
        lines.append("    stream_event_type_refs=(")
        for event in binding.stream_events:
            lines.append(f"        {event.class_ref!r},")
        lines.append("    ),")
        if binding.fulfillment_bindings:
            lines.append(f"    execution_protocol_ref={binding.execution_protocol_ref!r},")
            lines.append(f"    build_execution={binding.execution_factory_name},")
        else:
            lines.append("    execution_protocol_ref=None,")
            lines.append("    build_execution=None,")
        if binding.stream_events:
            lines.append(f"    stream_invoke={binding.stream_invoke_function_name},")
        else:
            lines.append("    stream_invoke=None,")
        lines.append("    fulfillment_bindings=(")
        for fulfillment in binding.fulfillment_bindings:
            lines.append("        ServiceProtocolFulfillmentBinding(")
            lines.append(f"            name={fulfillment.name!r},")
            lines.append(f"            graph_target={fulfillment.graph_target!r},")
            lines.append(
                "            graph_capability_function_name="
                + f"{fulfillment.graph_capability_function_name!r},"
            )
            lines.append(
                "            graph_function_python_ref="
                + f"{fulfillment.graph_function_python_ref!r},"
            )
            lines.append(f"            method_name={fulfillment.method_name!r},")
            lines.append(
                "            request_type_ref="
                + f"{(fulfillment.request_model.type_ref if fulfillment.request_model is not None else '')!r},"
            )
            lines.append(
                "            response_type_ref="
                + f"{(fulfillment.response_model.type_ref if fulfillment.response_model is not None else '')!r},"
            )
            lines.append("        ),")
        lines.append("    ),")
        lines.append(f"    invoke={binding.invoke_function_name},")
        lines.append(")")
        lines.append("")
        append_section(
            section_kind="service_protocol_endpoint_binding",
            section_key=_service_protocol_endpoint_section_key(
                section_name="endpoint_binding",
                endpoint_binding=binding,
            ),
            lines=lines,
        )

    lines = []
    lines.append("ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {")
    for binding in endpoint_bindings:
        lines.append(f"    {binding.endpoint_constant_name}: {binding.binding_constant_name},")
    lines.append("}")
    lines.append("")
    append_section(
        section_kind="service_protocol_endpoint_binding_index",
        section_key="api.service_protocol.endpoint_bindings_index",
        lines=lines,
    )

    capability_protocol_class_names: list[str] = []
    api_protocol_class_names: list[str] = []

    for api_name in sorted(by_api, key=str.casefold):
        capability_bindings = by_api[api_name]
        for capability_name in sorted(capability_bindings, key=str.casefold):
            ordered_bindings = sorted(
                capability_bindings[capability_name],
                key=lambda item: (item.endpoint_name.casefold(), item.endpoint_ref),
            )
            capability_protocol_name = (
                f"{to_pascal_case(api_name)}{to_pascal_case(capability_name)}CapabilityServiceProtocol"
            )
            capability_protocol_class_names.append(capability_protocol_name)
            lines = _render_capability_protocol_class(
                class_name=capability_protocol_name,
                endpoint_bindings=ordered_bindings,
            )
            lines.append("")
            append_section(
                section_kind="service_protocol_capability_protocol",
                section_key=(
                    "api.service_protocol.capability_protocol:"
                    f"{api_name}.{capability_name}"
                ),
                lines=lines,
            )

        api_protocol_name = f"{to_pascal_case(api_name)}ApiServiceProtocol"
        api_protocol_class_names.append(api_protocol_name)
        lines = _render_api_protocol_class(
            api_name=api_name,
            class_name=api_protocol_name,
            capability_names=tuple(sorted(capability_bindings, key=str.casefold)),
        )
        lines.append("")
        append_section(
            section_kind="service_protocol_api_protocol",
            section_key=f"api.service_protocol.api_protocol:{api_name}",
            lines=lines,
        )

    lines = _render_root_service_protocol_class(
        class_name=root_protocol_name,
        api_names=tuple(sorted(by_api, key=str.casefold)),
    )
    lines.append("")
    append_section(
        section_kind="service_protocol_root_protocol",
        section_key="api.service_protocol.root_protocol",
        lines=lines,
    )

    lines = []
    lines.append("__all__ = [")
    lines.append("    'API_FQN_PREFIX',")
    lines.append("    'API_PACKAGE_NAME',")
    lines.append("    'ENDPOINT_BINDINGS',")
    lines.append("    'PUBLIC_PACKAGE_IMPORT_ROOT',")
    lines.append(f"    {API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME!r},")
    lines.append("    'ServiceProtocolExecutionBackend',")
    lines.append("    'ServiceProtocolExecutionFactory',")
    lines.append("    'ServiceProtocolEndpointBinding',")
    lines.append("    'ServiceProtocolFulfillmentBinding',")
    lines.append("    'ServiceProtocolInvoker',")
    lines.append("    'ServiceProtocolStreamInvoker',")
    lines.append(f"    {root_protocol_name!r},")
    for class_name in sorted(set(execution_model_names), key=str.casefold):
        lines.append(f"    {class_name!r},")
    for class_name in sorted(set(execution_protocol_names), key=str.casefold):
        lines.append(f"    {class_name!r},")
    for class_name in api_protocol_class_names:
        lines.append(f"    {class_name!r},")
    for class_name in capability_protocol_class_names:
        lines.append(f"    {class_name!r},")
    for alias_name in sorted(stream_alias_names):
        lines.append(f"    {alias_name!r},")
    for binding in endpoint_bindings:
        lines.append(f"    {binding.endpoint_constant_name!r},")
        lines.append(f"    {binding.binding_constant_name!r},")
        if binding.fulfillment_bindings:
            lines.append(f"    {binding.execution_factory_name!r},")
        lines.append(f"    {binding.invoke_function_name!r},")
        if binding.stream_events:
            lines.append(f"    {binding.stream_invoke_function_name!r},")
    lines.append("]")
    lines.append("")
    export_section = PythonApiServiceProtocolRenderSection(
        section_kind="service_protocol_module_exports",
        section_key="api.service_protocol.__all__",
        lines=tuple(lines),
    )
    append_section(
        section_kind="service_protocol_section_text_manifest",
        section_key="api.service_protocol.section_text_manifest",
        lines=_render_service_protocol_section_text_manifest_lines(
            sections=(*sections, export_section),
        ),
    )
    sections.append(export_section)
    return tuple(sections)


def _render_service_protocol_section_text_manifest_lines(
    *,
    sections: tuple[PythonApiServiceProtocolRenderSection, ...],
) -> list[str]:
    manifest_json = json.dumps(
        build_python_api_service_protocol_section_text_manifest(sections=sections),
        indent=2,
        sort_keys=True,
    )
    lines = [
        f"{API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME}: Final[str] = ("
    ]
    for line in manifest_json.splitlines():
        lines.append(f"    {line!r}")
    lines.append(")")
    lines.append("")
    return lines


def _stable_section_text_digest(*, text: str) -> str:
    return f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"


def _service_protocol_endpoint_section_key(
    *,
    section_name: str,
    endpoint_binding: _EndpointProtocolBinding,
) -> str:
    return (
        f"api.service_protocol.{section_name}:"
        f"{endpoint_binding.api_name}."
        f"{endpoint_binding.capability_name}."
        f"{endpoint_binding.endpoint_name}"
    )


def _render_capability_protocol_class(
    *,
    class_name: str,
    endpoint_bindings: list[_EndpointProtocolBinding],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"class {class_name}(Protocol):")
    if not endpoint_bindings:
        lines.append("    pass")
        return lines

    for binding in endpoint_bindings:
        response_annotation = binding.response.class_name if binding.response is not None else "None"
        lines.append("")
        if binding.fulfillment_bindings:
            lines.append(
                f"    async def {binding.method_name}(self, request: {binding.request.class_name}, "
                + f"execution: {binding.execution_protocol_name}) -> {response_annotation}: ..."
            )
        else:
            lines.append(
                f"    async def {binding.method_name}(self, request: {binding.request.class_name}) "
                + f"-> {response_annotation}: ..."
            )
        if binding.stream_events:
            stream_annotation = binding.stream_alias_name
            lines.append("")
            if binding.fulfillment_bindings:
                lines.append(
                    f"    def {binding.stream_method_name}(self, request: {binding.request.class_name}, "
                    + f"execution: {binding.execution_protocol_name}) -> AsyncIterator[{stream_annotation}]: ..."
                )
            else:
                lines.append(
                    f"    def {binding.stream_method_name}(self, request: {binding.request.class_name}) "
                    + f"-> AsyncIterator[{stream_annotation}]: ..."
                )
    return lines


def _render_api_protocol_class(
    *,
    api_name: str,
    class_name: str,
    capability_names: tuple[str, ...],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"class {class_name}(Protocol):")
    if not capability_names:
        lines.append("    pass")
        return lines
    for capability_name in capability_names:
        capability_protocol_name = (
            f"{to_pascal_case(api_name)}{to_pascal_case(capability_name)}CapabilityServiceProtocol"
        )
        lines.append(
            f"    {_safe_python_identifier(capability_name)}: {capability_protocol_name}"
        )
    return lines


def _render_root_service_protocol_class(
    *,
    class_name: str,
    api_names: tuple[str, ...],
) -> list[str]:
    lines: list[str] = []
    lines.append(f"class {class_name}(Protocol):")
    if not api_names:
        lines.append("    pass")
        return lines
    for api_name in api_names:
        api_protocol_name = f"{to_pascal_case(api_name)}ApiServiceProtocol"
        lines.append(f"    {_safe_python_identifier(api_name)}: {api_protocol_name}")
    return lines


def _render_execution_model(*, binding: _ExecutionModelBinding) -> list[str]:
    lines: list[str] = [f"class {binding.class_name}(BaseModel):"]
    if not binding.fields:
        lines.append("    pass")
        return lines
    for field in binding.fields:
        if field.default_expr is None:
            lines.append(f"    {field.name}: {field.type_annotation}")
            continue
        lines.append(f"    {field.name}: {field.type_annotation} = {field.default_expr}")
    return lines


def _render_execution_protocol_class(
    *,
    endpoint_binding: _EndpointProtocolBinding,
) -> list[str]:
    lines: list[str] = [f"class {endpoint_binding.execution_protocol_name}(ServiceProtocolExecution, Protocol):"]
    if not endpoint_binding.fulfillment_bindings:
        lines.append("    pass")
        return lines
    for fulfillment in endpoint_binding.fulfillment_bindings:
        if (
            fulfillment.method_name is None
            or fulfillment.request_model is None
            or fulfillment.response_model is None
        ):
            raise ValueError(
                "API service protocol execution rendering requires resolved fulfillment request/response "
                f"models for endpoint {endpoint_binding.endpoint_ref!r} fulfillment {fulfillment.name!r}"
            )
        lines.append("")
        lines.append(
            f"    async def {fulfillment.method_name}(self, request: {fulfillment.request_model.class_name}) "
            + f"-> {fulfillment.response_model.class_name}: ..."
        )
    return lines


def _render_execution_implementation_class(
    *,
    endpoint_binding: _EndpointProtocolBinding,
) -> list[str]:
    lines: list[str] = [
        f"class {endpoint_binding.execution_impl_name}({endpoint_binding.execution_protocol_name}):"
    ]
    lines.append("    def __init__(self, backend: ServiceProtocolExecutionBackend) -> None:")
    lines.append("        self._backend = backend")
    if not endpoint_binding.fulfillment_bindings:
        lines.append("")
        lines.append("    pass")
    for fulfillment in endpoint_binding.fulfillment_bindings:
        if (
            fulfillment.method_name is None
            or fulfillment.request_model is None
            or fulfillment.response_model is None
        ):
            raise ValueError(
                "Execution implementation rendering requires resolved fulfillment request/response "
                f"models for endpoint {endpoint_binding.endpoint_ref!r} fulfillment {fulfillment.name!r}"
            )
        lines.append("")
        lines.append(
            f"    async def {fulfillment.method_name}(self, request: {fulfillment.request_model.class_name}) "
            + f"-> {fulfillment.response_model.class_name}:"
        )
        lines.append(
            "        response = await self._backend.invoke_fulfillment("
        )
        lines.append(
            f"            fulfillment_name={fulfillment.name!r},"
        )
        lines.append("            request=request,")
        lines.append("        )")
        lines.append(
            f"        if isinstance(response, {fulfillment.response_model.class_name}):"
        )
        lines.append("            return response")
        lines.append(
            f"        return {fulfillment.response_model.class_name}.model_validate("
            f"_coerce_model_payload(response, model_cls={fulfillment.response_model.class_name})"
            ")"
        )
    lines.append("")
    lines.append(
        f"def {endpoint_binding.execution_factory_name}(backend: ServiceProtocolExecutionBackend) "
        + f"-> {endpoint_binding.execution_protocol_name}:"
    )
    lines.append(f"    return {endpoint_binding.execution_impl_name}(backend=backend)")
    return lines


def _enrich_endpoint_bindings_with_execution(
    *,
    endpoint_bindings: tuple[_EndpointProtocolBinding, ...],
    class_configs_by_identity: dict[str, ClassConfig],
    external_type_bindings_by_identity: dict[str, _PythonTypeBinding],
    public_package_import_root: str,
) -> tuple[_EndpointProtocolBinding, ...]:
    public_type_bindings_by_identity = _build_public_type_binding_index(
        endpoint_bindings=endpoint_bindings,
        public_package_import_root=public_package_import_root,
    )
    resolved_type_bindings_by_identity = dict(external_type_bindings_by_identity)
    resolved_type_bindings_by_identity.update(public_type_bindings_by_identity)

    enriched: list[_EndpointProtocolBinding] = []
    for endpoint_binding in endpoint_bindings:
        fulfillment_bindings = tuple(
            _resolve_execution_fulfillment_binding(
                endpoint_binding=endpoint_binding,
                fulfillment_binding=fulfillment_binding,
                class_configs_by_identity=class_configs_by_identity,
                resolved_type_bindings_by_identity=resolved_type_bindings_by_identity,
            )
            for fulfillment_binding in endpoint_binding.fulfillment_bindings
        )
        enriched.append(replace(endpoint_binding, fulfillment_bindings=fulfillment_bindings))
    return tuple(enriched)


def _resolve_execution_fulfillment_binding(
    *,
    endpoint_binding: _EndpointProtocolBinding,
    fulfillment_binding: _FulfillmentBinding,
    class_configs_by_identity: dict[str, ClassConfig],
    resolved_type_bindings_by_identity: dict[str, _PythonTypeBinding],
) -> _FulfillmentBinding:
    function_config = _resolve_function_config(
        graph_function_python_ref=fulfillment_binding.graph_function_python_ref,
        class_configs_by_identity=class_configs_by_identity,
    )
    request_model = _build_execution_model_binding(
        endpoint_binding=endpoint_binding,
        fulfillment_binding=fulfillment_binding,
        function_config=function_config,
        attribute_type=FunctionAttributeType.input,
        resolved_type_bindings_by_identity=resolved_type_bindings_by_identity,
        suffix="Request",
    )
    response_model = _build_execution_model_binding(
        endpoint_binding=endpoint_binding,
        fulfillment_binding=fulfillment_binding,
        function_config=function_config,
        attribute_type=FunctionAttributeType.output,
        resolved_type_bindings_by_identity=resolved_type_bindings_by_identity,
        suffix="Response",
    )
    return replace(
        fulfillment_binding,
        method_name=_safe_python_identifier(fulfillment_binding.name),
        request_model=request_model,
        response_model=response_model,
    )


def _resolve_function_config(
    *,
    graph_function_python_ref: str,
    class_configs_by_identity: dict[str, ClassConfig],
) -> FunctionConfig:
    target = graph_function_python_ref.strip()
    if not target or "." not in target:
        raise ValueError(
            "API service protocol execution-context rendering requires a qualified graph function target "
            + f"(got {graph_function_python_ref!r})"
        )
    class_ref, function_name = target.rsplit(".", 1)
    class_config = _resolve_class_config(
        class_ref=class_ref,
        class_configs_by_identity=class_configs_by_identity,
    )
    matches = [
        link.function_config
        for link in class_config.class_config_function_configs
        if (
            link.function_config is not None
            and _normalize_token(link.function_config.name) == _normalize_token(function_name)
        )
    ]
    unique_matches = {
        function_config.id: function_config
        for function_config in matches
    }
    if not unique_matches:
        raise ValueError(
            "API service protocol execution-context rendering could not resolve graph function target "
            + f"{graph_function_python_ref!r} onto one FunctionConfig"
        )
    if len(unique_matches) > 1:
        raise ValueError(
            "API service protocol execution-context rendering found ambiguous graph function target "
            + f"{graph_function_python_ref!r}"
        )
    return next(iter(unique_matches.values()))


def _resolve_class_config(
    *,
    class_ref: str,
    class_configs_by_identity: dict[str, ClassConfig],
) -> ClassConfig:
    candidates = {
        class_config.id: class_config
        for identity, class_config in class_configs_by_identity.items()
        if identity == _normalize_token(class_ref)
        or identity == _leaf_token(class_ref)
        or identity.endswith(f".{_normalize_token(class_ref)}")
    }
    if not candidates:
        raise ValueError(
            f"API service protocol execution-context rendering could not resolve class ref {class_ref!r}"
        )
    if len(candidates) > 1:
        raise ValueError(
            f"API service protocol execution-context rendering found ambiguous class ref {class_ref!r}"
        )
    return next(iter(candidates.values()))


def _build_execution_model_binding(
    *,
    endpoint_binding: _EndpointProtocolBinding,
    fulfillment_binding: _FulfillmentBinding,
    function_config: FunctionConfig,
    attribute_type: FunctionAttributeType,
    resolved_type_bindings_by_identity: dict[str, _PythonTypeBinding],
    suffix: str,
) -> _ExecutionModelBinding:
    prefix = _execution_prefix_name(
        api_name=endpoint_binding.api_name,
        capability_name=endpoint_binding.capability_name,
        endpoint_name=endpoint_binding.endpoint_name,
        fulfillment_name=fulfillment_binding.name,
    )
    class_name = f"{prefix}{suffix}"
    type_ref = f"protocols.{class_name}"
    imported_types: dict[str, _PythonTypeBinding] = {}
    fields: list[_ExecutionFieldBinding] = []

    edges = [
        edge
        for edge in function_config.function_config_attribute_configs
        if edge.type == attribute_type and edge.attribute_config is not None
    ]
    edges.sort(key=lambda item: (item.position, item.name.casefold(), str(item.id)))

    for edge in edges:
        attribute_config = edge.attribute_config
        if attribute_config is None:
            continue
        field_binding, used_imports = _build_execution_field_binding(
            attribute_config=attribute_config,
            resolved_type_bindings_by_identity=resolved_type_bindings_by_identity,
        )
        fields.append(field_binding)
        for import_binding in used_imports:
            imported_types.setdefault(import_binding.class_ref, import_binding)

    return _ExecutionModelBinding(
        class_name=class_name,
        type_ref=type_ref,
        fields=tuple(fields),
        imported_types=tuple(imported_types.values()),
    )


def _build_execution_field_binding(
    *,
    attribute_config: AttributeConfig,
    resolved_type_bindings_by_identity: dict[str, _PythonTypeBinding],
) -> tuple[_ExecutionFieldBinding, tuple[_PythonTypeBinding, ...]]:
    type_info = resolve_type_info(attribute_config)
    imported_types: list[_PythonTypeBinding] = []

    base_type = "Any"
    if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config is not None:
        primitive_type = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
        base_type = _render_primitive_type(primitive_type.base_type)
    elif type_info.kind == AttributeTypeDescriptorKind.enum and type_info.enum_config is not None:
        binding = _require_type_binding(
            class_ref=str(type_info.enum_config.enum_fqn or type_info.enum_config.name),
            resolved_type_bindings_by_identity=resolved_type_bindings_by_identity,
        )
        base_type = binding.class_name
        imported_types.append(binding)
    elif type_info.kind == AttributeTypeDescriptorKind.class_ and type_info.class_config is not None:
        binding = _require_type_binding(
            class_ref=str(type_info.class_config.class_fqn or type_info.class_config.name),
            resolved_type_bindings_by_identity=resolved_type_bindings_by_identity,
        )
        base_type = binding.class_name
        imported_types.append(binding)

    type_annotation = base_type
    if type_info.is_collection:
        type_annotation = f"list[{type_annotation}]"
    if _is_nullable(attribute_config=attribute_config, type_info=type_info) and not type_info.is_collection:
        type_annotation = f"{type_annotation} | None"

    return (
        _ExecutionFieldBinding(
            name=_safe_python_identifier(attribute_config.name),
            type_annotation=type_annotation,
            default_expr=_render_field_default(attribute_config=attribute_config, type_info=type_info),
            description=attribute_config.description,
        ),
        tuple(imported_types),
    )


def _execution_protocol_name(
    *,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
) -> str:
    return (
        _execution_prefix_name(
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
        )
        + "Execution"
    )


def _execution_prefix_name(
    *,
    api_name: str,
    capability_name: str,
    endpoint_name: str,
    fulfillment_name: str | None = None,
) -> str:
    parts = [
        to_pascal_case(api_name),
        to_pascal_case(capability_name),
        to_pascal_case(endpoint_name),
    ]
    if fulfillment_name is not None:
        parts.append(to_pascal_case(fulfillment_name))
    token = "".join(part for part in parts if part)
    return token or "Execution"


def _leaf_token(value: str) -> str:
    token = (value or "").strip()
    if not token:
        return ""
    return _normalize_token(token.rsplit(".", 1)[-1])


def _build_endpoint_bindings(
    *,
    service_plan: dict[str, object],
    public_plan: dict[str, object],
    invocation_manifest: dict[str, object],
    interface_spec: dict[str, object],
    public_package_import_root: str,
    external_type_bindings_by_identity: dict[str, _PythonTypeBinding],
) -> tuple[_EndpointProtocolBinding, ...]:
    interface_refs = _collect_interface_endpoint_refs(interface_spec=interface_spec)
    public_endpoints = _build_public_endpoint_index(public_plan=public_plan)
    invocation_endpoints = _build_invocation_endpoint_index(invocation_manifest=invocation_manifest)

    bindings: list[_EndpointProtocolBinding] = []
    for api in _iter_object_list(service_plan.get("apis"), label="api.service_protocol_plan.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                endpoint_ref = _require_string(endpoint, "endpoint_ref")
                discriminant = _require_string(endpoint, "discriminant")
                endpoint_name = _require_string(endpoint, "name")
                if endpoint_ref not in interface_refs:
                    raise ValueError(
                        "API service protocol renderer missing interface endpoint "
                        + f"{endpoint_ref!r} in api.interface_spec"
                    )
                public_endpoint = public_endpoints.get(endpoint_ref)
                if public_endpoint is None:
                    raise ValueError(
                        "API service protocol renderer missing public endpoint "
                        + f"{endpoint_ref!r} in api.public_package_plan"
                    )
                public_discriminant = _require_string(public_endpoint, "discriminant")
                if _normalize_token(public_discriminant) != _normalize_token(discriminant):
                    raise ValueError(
                        "API service protocol renderer discriminant drift for "
                        + f"{endpoint_ref!r}: service_plan={discriminant!r}, public_plan={public_discriminant!r}"
                    )

                invocation = invocation_endpoints.get(endpoint_ref)
                if invocation is None:
                    raise ValueError(
                        "API service protocol renderer missing invocation endpoint "
                        + f"{endpoint_ref!r} in api.invocation_manifest"
                    )

                request_payload = _require_object(endpoint.get("request"), label=f"{endpoint_ref}.request")
                request_ref = _require_string(request_payload, "class_ref")
                public_request_payload = _require_object(
                    public_endpoint.get("request"),
                    label=f"{endpoint_ref}.public_request",
                )
                public_request_ref = _require_string(public_request_payload, "class_ref")
                if _normalize_token(public_request_ref) != _normalize_token(request_ref):
                    raise ValueError(
                        "API service protocol renderer request class drift for "
                        + f"{endpoint_ref!r}: service_plan={request_ref!r}, public_plan={public_request_ref!r}"
                    )
                invocation_request_ref = _require_string(
                    _require_object(invocation.get("request"), label=f"{endpoint_ref}.invocation.request"),
                    "class_ref",
                )
                if _normalize_token(invocation_request_ref) != _normalize_token(request_ref):
                    raise ValueError(
                        "API service protocol renderer request class drift for "
                        + f"{endpoint_ref!r}: service_plan={request_ref!r}, invocation={invocation_request_ref!r}"
                    )

                response_binding = _resolve_optional_response_binding(
                    endpoint_ref=endpoint_ref,
                    service_endpoint=endpoint,
                    public_endpoint=public_endpoint,
                    public_package_import_root=public_package_import_root,
                    external_type_bindings_by_identity=external_type_bindings_by_identity,
                )
                stream_bindings = _resolve_stream_bindings(
                    endpoint_ref=endpoint_ref,
                    service_endpoint=endpoint,
                    public_endpoint=public_endpoint,
                    public_package_import_root=public_package_import_root,
                    external_type_bindings_by_identity=external_type_bindings_by_identity,
                )
                fulfillment_bindings = tuple(
                    _FulfillmentBinding(
                        name=_require_string(fulfillment, "name"),
                        graph_target=_require_string(fulfillment, "graph_target"),
                        graph_capability_function_name=_require_string(
                            fulfillment, "graph_capability_function_name"
                        ),
                        graph_function_python_ref=_require_string(
                            fulfillment, "graph_function_python_ref"
                        ),
                    )
                    for fulfillment in _iter_object_list(
                        endpoint.get("fulfillment_bindings"),
                        label=f"{endpoint_ref}.fulfillment_bindings",
                    )
                )

                bindings.append(
                    _EndpointProtocolBinding(
                        endpoint_ref=endpoint_ref,
                        api_name=api_name,
                        capability_name=capability_name,
                        endpoint_name=endpoint_name,
                        description=_optional_string(endpoint, "description"),
                        request=_python_type_binding(
                            class_ref=request_ref,
                            public_package_import_root=public_package_import_root,
                            external_type_bindings_by_identity=external_type_bindings_by_identity,
                        ),
                        response=response_binding,
                        stream_events=stream_bindings,
                        fulfillment_bindings=fulfillment_bindings,
                    )
                )

    return tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.api_name.casefold(),
                item.capability_name.casefold(),
                item.endpoint_name.casefold(),
                item.endpoint_ref,
            ),
        )
    )


def _resolve_optional_response_binding(
    *,
    endpoint_ref: str,
    service_endpoint: dict[str, object],
    public_endpoint: dict[str, object],
    public_package_import_root: str,
    external_type_bindings_by_identity: dict[str, _PythonTypeBinding],
) -> _PythonTypeBinding | None:
    service_response = service_endpoint.get("response")
    public_response = public_endpoint.get("response")
    if service_response is None and public_response is None:
        return None
    if service_response is None or public_response is None:
        raise ValueError(f"API service protocol renderer response drift for {endpoint_ref!r}.")
    service_payload = _require_object(service_response, label=f"{endpoint_ref}.response")
    public_payload = _require_object(public_response, label=f"{endpoint_ref}.public_response")
    service_ref = _require_string(service_payload, "class_ref")
    public_ref = _require_string(public_payload, "class_ref")
    if _normalize_token(service_ref) != _normalize_token(public_ref):
        raise ValueError(
            "API service protocol renderer response class drift for "
            + f"{endpoint_ref!r}: service_plan={service_ref!r}, public_plan={public_ref!r}"
        )
    return _python_type_binding(
        class_ref=service_ref,
        public_package_import_root=public_package_import_root,
        external_type_bindings_by_identity=external_type_bindings_by_identity,
    )


def _resolve_stream_bindings(
    *,
    endpoint_ref: str,
    service_endpoint: dict[str, object],
    public_endpoint: dict[str, object],
    public_package_import_root: str,
    external_type_bindings_by_identity: dict[str, _PythonTypeBinding],
) -> tuple[_PythonTypeBinding, ...]:
    service_stream = service_endpoint.get("stream")
    public_stream = public_endpoint.get("stream")
    if service_stream is None and public_stream is None:
        return ()
    if service_stream is None or public_stream is None:
        raise ValueError(f"API service protocol renderer stream drift for {endpoint_ref!r}.")

    service_stream_object = _require_object(service_stream, label=f"{endpoint_ref}.stream")
    public_stream_object = _require_object(public_stream, label=f"{endpoint_ref}.public_stream")
    service_mode = _require_string(service_stream_object, "stream_mode")
    public_mode = _require_string(public_stream_object, "stream_mode")
    if _normalize_token(service_mode) != _normalize_token(public_mode):
        raise ValueError(
            "API service protocol renderer stream mode drift for "
            + f"{endpoint_ref!r}: service_plan={service_mode!r}, public_plan={public_mode!r}"
        )

    public_events_by_kind = {
        _require_string(event, "kind"): _require_string(event, "class_ref")
        for event in _iter_object_list(
            public_stream_object.get("events"),
            label=f"{endpoint_ref}.public_stream.events",
        )
    }
    bindings: list[_PythonTypeBinding] = []
    for service_event in _iter_object_list(
        service_stream_object.get("events"),
        label=f"{endpoint_ref}.stream.events",
    ):
        kind = _require_string(service_event, "kind")
        service_ref = _require_string(service_event, "class_ref")
        public_ref = public_events_by_kind.get(kind)
        if public_ref is None:
            raise ValueError(
                "API service protocol renderer stream event drift for "
                + f"{endpoint_ref!r}: missing public event kind {kind!r}"
            )
        if _normalize_token(service_ref) != _normalize_token(public_ref):
            raise ValueError(
                "API service protocol renderer stream event class drift for "
                + f"{endpoint_ref!r}:{kind!r}: service_plan={service_ref!r}, public_plan={public_ref!r}"
            )
        bindings.append(
            _python_type_binding(
                class_ref=service_ref,
                public_package_import_root=public_package_import_root,
                external_type_bindings_by_identity=external_type_bindings_by_identity,
            )
        )
    return tuple(bindings)


def _build_public_endpoint_index(*, public_plan: dict[str, object]) -> dict[str, dict[str, object]]:
    endpoints: dict[str, dict[str, object]] = {}
    for api in _iter_object_list(public_plan.get("apis"), label="api.public_package_plan.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                endpoints[_require_string(endpoint, "discriminant")] = endpoint
    return endpoints


def _build_invocation_endpoint_index(
    *,
    invocation_manifest: dict[str, object],
) -> dict[str, dict[str, object]]:
    endpoints: dict[str, dict[str, object]] = {}
    for api in _iter_object_list(invocation_manifest.get("apis"), label="api.invocation_manifest.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                endpoints[_require_string(endpoint, "endpoint_ref")] = endpoint
    return endpoints


def _collect_interface_endpoint_refs(*, interface_spec: dict[str, object]) -> set[str]:
    refs: set[str] = set()
    for api in _iter_object_list(interface_spec.get("apis"), label="api.interface_spec.apis"):
        api_name = _require_string(api, "name")
        for capability in _iter_object_list(api.get("capabilities"), label=f"{api_name}.capabilities"):
            capability_name = _require_string(capability, "name")
            for endpoint in _iter_object_list(
                capability.get("endpoints"),
                label=f"{api_name}.{capability_name}.endpoints",
            ):
                refs.add(_require_string(endpoint, "discriminant"))
    return refs


def _collect_imported_types(
    *,
    endpoint_bindings: tuple[_EndpointProtocolBinding, ...],
) -> tuple[_PythonTypeBinding, ...]:
    ordered: dict[str, _PythonTypeBinding] = {}
    for binding in endpoint_bindings:
        ordered.setdefault(binding.request.class_ref, binding.request)
        if binding.response is not None:
            ordered.setdefault(binding.response.class_ref, binding.response)
        for event in binding.stream_events:
            ordered.setdefault(event.class_ref, event)
        for fulfillment in binding.fulfillment_bindings:
            if fulfillment.request_model is not None:
                for import_binding in fulfillment.request_model.imported_types:
                    ordered.setdefault(import_binding.class_ref, import_binding)
            if fulfillment.response_model is not None:
                for import_binding in fulfillment.response_model.imported_types:
                    ordered.setdefault(import_binding.class_ref, import_binding)
    return tuple(ordered.values())


def _collect_aware_type_imports(
    *,
    endpoint_bindings: tuple[_EndpointProtocolBinding, ...],
) -> tuple[str, ...]:
    symbols: set[str] = set()
    for binding in endpoint_bindings:
        for fulfillment in binding.fulfillment_bindings:
            for model in (fulfillment.request_model, fulfillment.response_model):
                if model is None:
                    continue
                for field in model.fields:
                    tokens = {
                        token.strip()
                        for token in field.type_annotation.replace("[", " ")
                        .replace("]", " ")
                        .replace("|", " ")
                        .replace(",", " ")
                        .split()
                    }
                    for symbol in ("Json", "JsonArray", "JsonObject", "JsonValue", "Vector", "VectorDim"):
                        if symbol in tokens:
                            symbols.add(symbol)
    return tuple(sorted(symbols))


def _build_public_type_binding_index(
    *,
    endpoint_bindings: tuple[_EndpointProtocolBinding, ...],
    public_package_import_root: str,
) -> dict[str, _PythonTypeBinding]:
    bindings: dict[str, _PythonTypeBinding] = {}
    for endpoint_binding in endpoint_bindings:
        for class_ref in {
            endpoint_binding.request.class_ref,
            *(event.class_ref for event in endpoint_binding.stream_events),
            *(
                [endpoint_binding.response.class_ref]
                if endpoint_binding.response is not None
                else []
            ),
        }:
            binding = _python_type_binding(
                class_ref=class_ref,
                public_package_import_root=public_package_import_root,
            )
            for identity in _type_binding_identities(class_ref):
                bindings.setdefault(identity, binding)
    return bindings


def _build_external_type_binding_index(
    *,
    graph: ObjectConfigGraph,
    external_type_bindings_by_entity_id: dict[str, _ExternalPythonTypeBinding],
) -> dict[str, _PythonTypeBinding]:
    bindings: dict[str, _PythonTypeBinding] = {}
    for node in graph.object_config_graph_nodes:
        if node.class_config is not None and node.class_config.class_fqn:
            external_binding = external_type_bindings_by_entity_id.get(str(node.class_config.id))
            if external_binding is None:
                continue
            type_ref = external_binding.type_ref or node.class_config.class_fqn
            binding = _PythonTypeBinding(
                class_ref=type_ref,
                class_name=external_binding.class_name,
                module_path=external_binding.module_path,
            )
            for identity in {
                *_type_binding_identities(node.class_config.class_fqn),
                *_type_binding_identities(type_ref),
            }:
                bindings.setdefault(identity, binding)
            bindings.setdefault(_normalize_token(node.class_config.name), binding)
            bindings.setdefault(_leaf_token(node.class_config.class_fqn), binding)
            bindings.setdefault(_leaf_token(node.class_config.name), binding)
            continue
        if node.enum_config is not None and node.enum_config.enum_fqn:
            external_binding = external_type_bindings_by_entity_id.get(str(node.enum_config.id))
            if external_binding is None:
                continue
            type_ref = external_binding.type_ref or node.enum_config.enum_fqn
            binding = _PythonTypeBinding(
                class_ref=type_ref,
                class_name=external_binding.class_name,
                module_path=external_binding.module_path,
            )
            for identity in {
                *_type_binding_identities(node.enum_config.enum_fqn),
                *_type_binding_identities(type_ref),
            }:
                bindings.setdefault(identity, binding)
            bindings.setdefault(_normalize_token(node.enum_config.name), binding)
            bindings.setdefault(_leaf_token(node.enum_config.enum_fqn), binding)
            bindings.setdefault(_leaf_token(node.enum_config.name), binding)
    return bindings


def _build_class_config_index(
    *,
    graph: ObjectConfigGraph,
) -> dict[str, ClassConfig]:
    bindings: dict[str, ClassConfig] = {}
    for node in graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is None or not class_config.class_fqn:
            continue
        for identity in _type_binding_identities(class_config.class_fqn):
            bindings.setdefault(identity, class_config)
        bindings.setdefault(_normalize_token(class_config.name), class_config)
        bindings.setdefault(_leaf_token(class_config.class_fqn), class_config)
        bindings.setdefault(_leaf_token(class_config.name), class_config)
    return bindings


def _python_type_binding(
    *,
    class_ref: str,
    public_package_import_root: str,
    external_type_bindings_by_identity: dict[str, _PythonTypeBinding] | None = None,
) -> _PythonTypeBinding:
    if external_type_bindings_by_identity:
        for identity in _type_binding_identities(class_ref):
            binding = external_type_bindings_by_identity.get(identity)
            if binding is not None:
                return binding
    class_name = _class_name_from_ref(class_ref)
    module_path = f"{public_package_import_root}.models.{to_snake_case(class_name)}"
    return _PythonTypeBinding(
        class_ref=class_ref,
        class_name=class_name,
        module_path=module_path,
    )


def _class_name_from_ref(class_ref: str) -> str:
    token = class_ref.strip()
    if not token:
        raise ValueError("Expected non-empty class_ref.")
    if "." in token:
        return token.rsplit(".", 1)[-1]
    return token


def _type_binding_identities(class_ref: str) -> tuple[str, ...]:
    normalized = _normalize_token(class_ref)
    if not normalized:
        return ()
    values = {normalized, _leaf_token(class_ref), _normalize_token(_class_name_from_ref(class_ref))}
    parts = [part for part in normalized.split(".") if part]
    if "default" in parts[1:-1]:
        values.add(".".join(part for part in parts if part != "default"))
    return tuple(sorted(value for value in values if value))


def _require_type_binding(
    *,
    class_ref: str,
    resolved_type_bindings_by_identity: dict[str, _PythonTypeBinding],
) -> _PythonTypeBinding:
    for identity in _type_binding_identities(class_ref):
        binding = resolved_type_bindings_by_identity.get(identity)
        if binding is not None:
            return binding
    raise ValueError(
        "API service protocol execution-context rendering could not resolve a Python type binding for "
        + f"{class_ref!r}"
    )


def _build_external_python_type_bindings_by_entity_id(
    *,
    payload: object,
) -> dict[str, _ExternalPythonTypeBinding]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Expected profile input 'api.external_python_type_index' to be a JSON object.")

    bindings: dict[str, _ExternalPythonTypeBinding] = {}
    for label in ("classes", "enums"):
        entries = payload.get(label, {})
        if not isinstance(entries, dict):
            raise ValueError(
                "Expected profile input 'api.external_python_type_index' field "
                + f"{label!r} to be a JSON object."
            )
        for entity_id, raw_binding in entries.items():
            if not isinstance(raw_binding, dict):
                raise ValueError(
                    "Expected profile input 'api.external_python_type_index' entry "
                    + f"{label!r}:{entity_id!r} to be a JSON object."
                )
            module_path = _require_string(raw_binding, "module")
            class_name = _require_string(raw_binding, "name")
            type_ref = (
                _optional_string(raw_binding, "class_ref")
                or _optional_string(raw_binding, "enum_ref")
                or ""
            ).strip()
            bindings[str(entity_id)] = _ExternalPythonTypeBinding(
                class_name=class_name,
                module_path=module_path,
                type_ref=type_ref,
            )
    return bindings


def _is_nullable(*, attribute_config: AttributeConfig, type_info) -> bool:
    if getattr(type_info, "nullable", False):
        return True
    if attribute_config.default_value is not None:
        try:
            if json.loads(attribute_config.default_value) is None:
                return True
        except Exception:
            pass
    return not attribute_config.is_required


def _render_field_default(
    *,
    attribute_config: AttributeConfig,
    type_info,
) -> str | None:
    default_expr: str | None = None
    if attribute_config.default_value is not None:
        default_expr = _render_default_literal(
            raw_default=attribute_config.default_value,
            attribute_config=attribute_config,
            type_info=type_info,
        )
    elif _is_nullable(attribute_config=attribute_config, type_info=type_info) or type_info.is_collection:
        default_expr = "Field(default=None)" if not type_info.is_collection else "Field(default_factory=list)"

    if attribute_config.description:
        if default_expr is None:
            return f"Field(description={json.dumps(attribute_config.description)})"
        if default_expr.startswith("Field(") and default_expr.endswith(")"):
            inner = default_expr[len("Field("):-1].strip()
            if inner:
                return f"Field({inner}, description={json.dumps(attribute_config.description)})"
            return f"Field(description={json.dumps(attribute_config.description)})"
        return f"Field(default={default_expr}, description={json.dumps(attribute_config.description)})"
    return default_expr


def _render_default_literal(
    *,
    raw_default: str,
    attribute_config: AttributeConfig,
    type_info,
) -> str:
    try:
        value = json.loads(raw_default)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "API service protocol execution-context rendering failed to parse default value for "
            + f"{attribute_config.name!r}: {raw_default!r}"
        ) from exc

    if value is None:
        return "Field(default=None)"
    if type_info.kind == AttributeTypeDescriptorKind.primitive and type_info.primitive_config is not None:
        primitive_type = CodePrimitiveType.model_validate(type_info.primitive_config.primitive_type)
        if primitive_type.base_type == CodePrimitiveBaseType.string:
            return f"Field(default={json.dumps(str(value))})"
        if primitive_type.base_type == CodePrimitiveBaseType.boolean:
            return f"Field(default={'True' if bool(value) else 'False'})"
        return f"Field(default={value!r})"
    return f"Field(default={value!r})"


def _render_primitive_type(base_type: CodePrimitiveBaseType) -> str:
    if base_type == CodePrimitiveBaseType.string:
        return "str"
    if base_type == CodePrimitiveBaseType.boolean:
        return "bool"
    if base_type == CodePrimitiveBaseType.integer:
        return "int"
    if base_type == CodePrimitiveBaseType.float:
        return "float"
    if base_type == CodePrimitiveBaseType.uuid:
        return "UUID"
    if base_type == CodePrimitiveBaseType.json:
        return "JsonValue"
    if base_type == CodePrimitiveBaseType.vector:
        return "Vector"
    return "Any"


def _derive_public_package_import_root(*, public_plan: dict[str, object]) -> str:
    token = (_optional_string(public_plan, "fqn_prefix") or _require_string(public_plan, "package_name")).strip()
    token = token.replace("-", "_")
    return token or "aware_api_public_package"


def _root_service_protocol_name(*, import_root: str | None) -> str:
    token = (import_root or "aware_api_service_protocol").replace("-", "_")
    for suffix in ("_service_protocol", "_protocol"):
        if token.endswith(suffix):
            token = token[: -len(suffix)]
            break
    parts = [part for part in token.split("_") if part]
    base_name = "".join(part[:1].upper() + part[1:] for part in parts) or "AwareApi"
    return f"{base_name}ServiceProtocol"


def _endpoint_constant_name(endpoint_ref: str) -> str:
    token = endpoint_ref.replace(".", "__").replace("-", "_")
    token = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in token)
    token = token.upper().strip("_")
    return f"{token}_ENDPOINT_REF"


def _safe_python_identifier(value: str) -> str:
    candidate = to_snake_case(value or "").strip("_") or "value"
    candidate = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in candidate)
    if candidate and candidate[0].isdigit():
        candidate = f"_{candidate}"
    if keyword.iskeyword(candidate):
        candidate = f"{candidate}_"
    return candidate


def _normalize_token(value: str) -> str:
    return (value or "").strip().casefold()


def _iter_object_list(value: object, *, label: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Expected {label} to be a list of objects.")
    result: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"Expected {label} entries to be JSON objects.")
        result.append(item)
    return result


def _require_object(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected {label} to be a JSON object.")
    return value


def _require_string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected key {key!r} to be a non-empty string.")
    return value


def _optional_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Expected key {key!r} to be a string when present.")
    return value


__all__ = [
    "PythonApiServiceProtocolRendererLanguage",
    "render_python_api_service_protocol_module",
]
